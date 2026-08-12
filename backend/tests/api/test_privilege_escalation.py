from datetime import datetime, timedelta, timezone
from uuid import uuid4

from jose import jwt

from app.core.config import settings


AUTH_PREFIX = "/api/v1/auth"


def create_test_user(client):
    """Create a normal user and return credentials."""

    suffix = uuid4().hex[:10]

    user = {
        "username": f"privilege_{suffix}",
        "email": f"privilege_{suffix}@example.com",
        "password": "Password123!",
        "full_name": "Privilege Escalation Test User",
    }

    response = client.post(
        f"{AUTH_PREFIX}/register",
        json=user,
    )

    assert response.status_code == 201

    return user


def login_user(client, user):
    """Login and return token response."""

    response = client.post(
        f"{AUTH_PREFIX}/login",
        data={
            "username": user["email"],
            "password": user["password"],
        },
    )

    assert response.status_code == 200

    return response.json()


def auth_headers(token):
    return {
        "Authorization": f"Bearer {token}",
    }


# ------------------------------------------------------------------
# Admin endpoint protection
# ------------------------------------------------------------------


def test_normal_user_cannot_access_admin_endpoint(client):
    """
    A normal authenticated user must not access admin-only APIs.
    """

    user = create_test_user(client)
    tokens = login_user(client, user)

    response = client.get(
        f"{AUTH_PREFIX}/admin",
        headers=auth_headers(tokens["access_token"]),
    )

    assert response.status_code == 403

    assert response.json()["detail"] == (
        "Admin privileges required."
    )


def test_unauthenticated_user_cannot_access_admin_endpoint(client):
    """
    Anonymous users must not access admin-only APIs.
    """

    response = client.get(
        f"{AUTH_PREFIX}/admin",
    )

    assert response.status_code == 401


# ------------------------------------------------------------------
# Registration privilege escalation
# ------------------------------------------------------------------


def test_registration_cannot_create_admin_user(client):
    """
    A public registration request must never be able to create
    an administrator by supplying role=admin.
    """

    suffix = uuid4().hex[:10]

    payload = {
        "username": f"massassign_{suffix}",
        "email": f"massassign_{suffix}@example.com",
        "password": "Password123!",
        "full_name": "Mass Assignment Test",
        "role": "admin",
    }

    response = client.post(
        f"{AUTH_PREFIX}/register",
        json=payload,
    )

    # The API may either reject the unexpected field or ignore it.
    # It must never create an admin account.
    assert response.status_code in (201, 422)

    if response.status_code == 201:
        data = response.json()

        assert data.get("role") != "admin"


def test_registration_cannot_set_verified_admin_state(client):
    """
    Public registration must not allow privilege-related fields
    to be controlled by the client.
    """

    suffix = uuid4().hex[:10]

    payload = {
        "username": f"massassign2_{suffix}",
        "email": f"massassign2_{suffix}@example.com",
        "password": "Password123!",
        "full_name": "Privilege Field Test",
        "is_active": True,
        "is_verified": True,
    }

    response = client.post(
        f"{AUTH_PREFIX}/register",
        json=payload,
    )

    assert response.status_code in (201, 422)

    if response.status_code == 201:
        data = response.json()

        # Public registration must not grant verification privileges.
        assert data.get("is_verified") is not True


# ------------------------------------------------------------------
# JWT privilege escalation
# ------------------------------------------------------------------


def test_forged_admin_jwt_with_wrong_secret_is_rejected(client):
    """
    An attacker must not be able to forge an admin JWT using a
    different signing secret.
    """

    user = create_test_user(client)

    payload = {
        "sub": user["email"],
        "user_id": 999999999,
        "role": "admin",
        "exp": datetime.now(timezone.utc)
        + timedelta(minutes=30),
    }

    forged_token = jwt.encode(
        payload,
        "attacker-controlled-secret",
        algorithm=settings.ALGORITHM,
    )

    response = client.get(
        f"{AUTH_PREFIX}/admin",
        headers=auth_headers(forged_token),
    )

    assert response.status_code == 401


def test_user_cannot_change_jwt_role_to_admin(client):
    """
    A valid JWT signed by the server must still represent the
    database user. Changing the role claim and re-signing with
    an attacker-controlled secret must fail.
    """

    user = create_test_user(client)
    tokens = login_user(client, user)

    original_payload = jwt.decode(
        tokens["access_token"],
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],
    )

    forged_payload = dict(original_payload)
    forged_payload["role"] = "admin"

    forged_token = jwt.encode(
        forged_payload,
        "attacker-controlled-secret",
        algorithm=settings.ALGORITHM,
    )

    response = client.get(
        f"{AUTH_PREFIX}/admin",
        headers=auth_headers(forged_token),
    )

    assert response.status_code == 401


def test_user_cannot_change_jwt_user_id_to_admin_user(
    client,
):
    """
    Changing user_id in a forged token must not grant another
    user's privileges.
    """

    user = create_test_user(client)
    tokens = login_user(client, user)

    original_payload = jwt.decode(
        tokens["access_token"],
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],
    )

    forged_payload = dict(original_payload)

    forged_payload["user_id"] = 1
    forged_payload["role"] = "admin"

    forged_token = jwt.encode(
        forged_payload,
        "attacker-controlled-secret",
        algorithm=settings.ALGORITHM,
    )

    response = client.get(
        f"{AUTH_PREFIX}/admin",
        headers=auth_headers(forged_token),
    )

    assert response.status_code == 401