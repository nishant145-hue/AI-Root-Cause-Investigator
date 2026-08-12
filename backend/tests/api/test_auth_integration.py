from datetime import datetime, timedelta, timezone
from uuid import uuid4

from jose import jwt

from app.core.config import settings


AUTH_PREFIX = "/api/v1/auth"


def create_test_user(client):
    """
    Create a unique test user and return its credentials.
    """

    suffix = uuid4().hex[:10]

    user = {
        "username": f"authuser_{suffix}",
        "email": f"auth_{suffix}@example.com",
        "password": "Password123!",
        "full_name": "Authentication Test User",
    }

    response = client.post(
        f"{AUTH_PREFIX}/register",
        json=user,
    )

    assert response.status_code == 201

    return user


def login_user(client, user):
    """
    Login using the OAuth2 form expected by the API.
    """

    response = client.post(
        f"{AUTH_PREFIX}/login",
        data={
            "username": user["email"],
            "password": user["password"],
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"

    return data


def auth_headers(access_token):
    return {
        "Authorization": f"Bearer {access_token}"
    }


# ------------------------------------------------------------------
# Registration
# ------------------------------------------------------------------


def test_register_user(client):
    user = create_test_user(client)

    response = client.post(
        f"{AUTH_PREFIX}/login",
        data={
            "username": user["email"],
            "password": user["password"],
        },
    )

    assert response.status_code == 200


# ------------------------------------------------------------------
# Login
# ------------------------------------------------------------------


def test_login_returns_access_and_refresh_tokens(client):
    user = create_test_user(client)

    tokens = login_user(client, user)

    assert tokens["access_token"]
    assert tokens["refresh_token"]
    assert tokens["token_type"] == "bearer"


def test_login_rejects_invalid_password(client):
    user = create_test_user(client)

    response = client.post(
        f"{AUTH_PREFIX}/login",
        data={
            "username": user["email"],
            "password": "WrongPassword123!",
        },
    )

    assert response.status_code == 401


def test_login_rejects_unknown_user(client):
    response = client.post(
        f"{AUTH_PREFIX}/login",
        data={
            "username": "does-not-exist@example.com",
            "password": "Password123!",
        },
    )

    assert response.status_code == 401


# ------------------------------------------------------------------
# Protected endpoint enforcement
# ------------------------------------------------------------------


def test_me_requires_authentication(client):
    response = client.get(
        f"{AUTH_PREFIX}/me"
    )

    assert response.status_code == 401


def test_profile_requires_authentication(client):
    response = client.get(
        f"{AUTH_PREFIX}/profile"
    )

    assert response.status_code == 401


def test_me_accepts_valid_access_token(client):
    user = create_test_user(client)
    tokens = login_user(client, user)

    response = client.get(
        f"{AUTH_PREFIX}/me",
        headers=auth_headers(tokens["access_token"]),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["email"] == user["email"]
    assert data["username"] == user["username"]


def test_profile_accepts_valid_access_token(client):
    user = create_test_user(client)
    tokens = login_user(client, user)

    response = client.get(
        f"{AUTH_PREFIX}/profile",
        headers=auth_headers(tokens["access_token"]),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["email"] == user["email"]
    assert data["username"] == user["username"]


# ------------------------------------------------------------------
# Invalid JWT
# ------------------------------------------------------------------


def test_me_rejects_malformed_access_token(client):
    response = client.get(
        f"{AUTH_PREFIX}/me",
        headers=auth_headers("this-is-not-a-valid-jwt"),
    )

    assert response.status_code == 401


def test_me_rejects_expired_access_token(client):
    expired_payload = {
        "sub": "expired@example.com",
        "user_id": 999999,
        "role": "user",
        "exp": datetime.now(timezone.utc) - timedelta(minutes=5),
    }

    expired_token = jwt.encode(
        expired_payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

    response = client.get(
        f"{AUTH_PREFIX}/me",
        headers=auth_headers(expired_token),
    )

    assert response.status_code == 401


def test_me_rejects_token_signed_with_wrong_secret(client):
    payload = {
        "sub": "fake@example.com",
        "user_id": 999999,
        "role": "user",
        "exp": datetime.now(timezone.utc)
        + timedelta(minutes=30),
    }

    invalid_token = jwt.encode(
        payload,
        "definitely-wrong-secret",
        algorithm=settings.ALGORITHM,
    )

    response = client.get(
        f"{AUTH_PREFIX}/me",
        headers=auth_headers(invalid_token),
    )

    assert response.status_code == 401


# ------------------------------------------------------------------
# Refresh-token flow
# ------------------------------------------------------------------


def test_refresh_token_returns_new_access_token(client):
    user = create_test_user(client)
    tokens = login_user(client, user)

    response = client.post(
        f"{AUTH_PREFIX}/refresh",
        json={
            "refresh_token": tokens["refresh_token"],
        },
    )

    assert response.status_code == 200

    refreshed = response.json()

    assert refreshed["access_token"]
    assert refreshed["refresh_token"]
    assert refreshed["token_type"] == "bearer"

    # Refresh-token rotation:
    # the refreshed token must be different from the original token.
    assert refreshed["refresh_token"] != tokens["refresh_token"]


def test_refreshed_access_token_can_access_me(client):
    user = create_test_user(client)
    tokens = login_user(client, user)

    refresh_response = client.post(
        f"{AUTH_PREFIX}/refresh",
        json={
            "refresh_token": tokens["refresh_token"],
        },
    )

    assert refresh_response.status_code == 200

    new_access_token = refresh_response.json()["access_token"]

    response = client.get(
        f"{AUTH_PREFIX}/me",
        headers=auth_headers(new_access_token),
    )

    assert response.status_code == 200
    assert response.json()["email"] == user["email"]


def test_refresh_rejects_invalid_refresh_token(client):
    response = client.post(
        f"{AUTH_PREFIX}/refresh",
        json={
            "refresh_token": "invalid-refresh-token",
        },
    )

    assert response.status_code == 401


def test_refresh_requires_refresh_token(client):
    response = client.post(
        f"{AUTH_PREFIX}/refresh",
        json={},
    )

    assert response.status_code == 422


def test_refresh_rejects_empty_refresh_token(client):
    response = client.post(
        f"{AUTH_PREFIX}/refresh",
        json={
            "refresh_token": "",
        },
    )

    assert response.status_code in (401, 422)


# ------------------------------------------------------------------
# Logout / revoked refresh token
# ------------------------------------------------------------------


def test_logout_revokes_refresh_token(client):
    user = create_test_user(client)
    tokens = login_user(client, user)

    logout_response = client.post(
        f"{AUTH_PREFIX}/logout",
        json={
            "refresh_token": tokens["refresh_token"],
        },
    )

    assert logout_response.status_code == 200

    refresh_response = client.post(
        f"{AUTH_PREFIX}/refresh",
        json={
            "refresh_token": tokens["refresh_token"],
        },
    )

    assert refresh_response.status_code == 401


# ------------------------------------------------------------------
# Token isolation
# ------------------------------------------------------------------


def test_user_token_returns_only_that_user(client):
    user_a = create_test_user(client)
    user_b = create_test_user(client)

    tokens_a = login_user(client, user_a)
    tokens_b = login_user(client, user_b)

    response_a = client.get(
        f"{AUTH_PREFIX}/me",
        headers=auth_headers(tokens_a["access_token"]),
    )

    response_b = client.get(
        f"{AUTH_PREFIX}/me",
        headers=auth_headers(tokens_b["access_token"]),
    )

    assert response_a.status_code == 200
    assert response_b.status_code == 200

    assert response_a.json()["email"] == user_a["email"]
    assert response_b.json()["email"] == user_b["email"]

    assert response_a.json()["email"] != response_b.json()["email"]
    
def test_old_refresh_token_cannot_be_reused_after_rotation(client):
    user = create_test_user(client)
    tokens = login_user(client, user)

    response = client.post(
        f"{AUTH_PREFIX}/refresh",
        json={
            "refresh_token": tokens["refresh_token"],
        },
    )

    assert response.status_code == 200

    refreshed = response.json()

    assert refreshed["refresh_token"] != tokens["refresh_token"]

    # The original refresh token was rotated/revoked.
    reuse_response = client.post(
        f"{AUTH_PREFIX}/refresh",
        json={
            "refresh_token": tokens["refresh_token"],
        },
    )

    assert reuse_response.status_code == 401
    
# ------------------------------------------------------------------
# Additional token lifecycle security
# ------------------------------------------------------------------


def test_refresh_rejects_expired_refresh_token(client):
    expired_payload = {
        "sub": "expired-refresh@example.com",
        "user_id": 999999,
        "role": "user",
        "exp": datetime.now(timezone.utc) - timedelta(minutes=5),
    }

    expired_refresh_token = jwt.encode(
        expired_payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

    response = client.post(
        f"{AUTH_PREFIX}/refresh",
        json={
            "refresh_token": expired_refresh_token,
        },
    )

    assert response.status_code == 401


def test_refresh_rejects_refresh_token_signed_with_wrong_secret(
    client,
):
    payload = {
        "sub": "fake-refresh@example.com",
        "user_id": 999999,
        "role": "user",
        "exp": datetime.now(timezone.utc)
        + timedelta(minutes=30),
    }

    invalid_refresh_token = jwt.encode(
        payload,
        "definitely-wrong-secret",
        algorithm=settings.ALGORITHM,
    )

    response = client.post(
        f"{AUTH_PREFIX}/refresh",
        json={
            "refresh_token": invalid_refresh_token,
        },
    )

    assert response.status_code == 401


def test_me_rejects_access_token_for_nonexistent_user(
    client,
):
    payload = {
        "sub": "nonexistent@example.com",
        "user_id": 999999999,
        "role": "user",
        "exp": datetime.now(timezone.utc)
        + timedelta(minutes=30),
    }

    token = jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

    response = client.get(
        f"{AUTH_PREFIX}/me",
        headers=auth_headers(token),
    )

    assert response.status_code == 401


def test_refresh_rejects_token_for_nonexistent_user(
    client,
):
    payload = {
        "sub": "nonexistent-refresh@example.com",
        "user_id": 999999999,
        "role": "user",
        "exp": datetime.now(timezone.utc)
        + timedelta(minutes=30),
    }

    token = jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

    response = client.post(
        f"{AUTH_PREFIX}/refresh",
        json={
            "refresh_token": token,
        },
    )

    assert response.status_code == 401
    
# ------------------------------------------------------------------
# JWT Security Hardening
# ------------------------------------------------------------------


def test_me_rejects_access_token_without_subject(client):
    """
    The access token must contain the `sub` claim because
    get_current_user() uses it to identify the authenticated user.
    """

    payload = {
        "user_id": 999999,
        "role": "user",
        "exp": datetime.now(timezone.utc)
        + timedelta(minutes=30),
    }

    token = jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

    response = client.get(
        f"{AUTH_PREFIX}/me",
        headers=auth_headers(token),
    )

    assert response.status_code == 401


def test_me_rejects_tampered_access_token(client):
    """
    Changing the JWT payload without recalculating its signature
    must invalidate the token.
    """

    user = create_test_user(client)
    tokens = login_user(client, user)

    original_token = tokens["access_token"]

    parts = original_token.split(".")

    assert len(parts) == 3

    # Change the payload while keeping the original signature.
    import base64
    import json

    payload_bytes = base64.urlsafe_b64decode(
        parts[1] + "=" * (-len(parts[1]) % 4)
    )

    payload = json.loads(payload_bytes)

    payload["sub"] = "attacker@example.com"

    modified_payload = base64.urlsafe_b64encode(
        json.dumps(
            payload,
            separators=(",", ":"),
        ).encode()
    ).decode().rstrip("=")

    tampered_token = (
        f"{parts[0]}.{modified_payload}.{parts[2]}"
    )

    response = client.get(
        f"{AUTH_PREFIX}/me",
        headers=auth_headers(tampered_token),
    )

    assert response.status_code == 401


def test_me_rejects_access_token_signed_with_wrong_algorithm(
    client,
):
    """
    A token signed using an algorithm different from the
    configured algorithm must be rejected.
    """

    user = create_test_user(client)

    payload = {
        "sub": user["email"],
        "user_id": 999999,
        "role": "user",
        "exp": datetime.now(timezone.utc)
        + timedelta(minutes=30),
    }

    wrong_algorithm_token = jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm="HS384",
    )

    response = client.get(
        f"{AUTH_PREFIX}/me",
        headers=auth_headers(wrong_algorithm_token),
    )

    assert response.status_code == 401


def test_me_rejects_access_token_with_unknown_subject(
    client,
):
    """
    A correctly signed JWT must still be rejected when its
    subject does not correspond to an existing user.
    """

    payload = {
        "sub": "attacker-does-not-exist@example.com",
        "user_id": 999999,
        "role": "user",
        "exp": datetime.now(timezone.utc)
        + timedelta(minutes=30),
    }

    token = jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

    response = client.get(
        f"{AUTH_PREFIX}/me",
        headers=auth_headers(token),
    )

    assert response.status_code == 401