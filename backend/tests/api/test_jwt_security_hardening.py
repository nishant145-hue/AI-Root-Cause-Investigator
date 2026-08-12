from datetime import datetime, timedelta, timezone
from uuid import uuid4

from jose import jwt

from app.core.config import settings
from app.models.user import User


AUTH_PREFIX = "/api/v1/auth"


def create_user(client):
    suffix = uuid4().hex[:10]

    user = {
        "username": f"jwtsec_{suffix}",
        "email": f"jwtsec_{suffix}@example.com",
        "password": "Password123!",
        "full_name": "JWT Security User",
    }

    response = client.post(
        f"{AUTH_PREFIX}/register",
        json=user,
    )

    assert response.status_code == 201

    return user


def login(client, user):
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
        "Authorization": f"Bearer {token}"
    }


# ------------------------------------------------------------------
# Missing token
# ------------------------------------------------------------------


def test_protected_endpoint_requires_access_token(
    client,
):
    response = client.get(
        f"{AUTH_PREFIX}/me",
    )

    assert response.status_code == 401


# ------------------------------------------------------------------
# Malformed token
# ------------------------------------------------------------------


def test_malformed_jwt_is_rejected(client):
    response = client.get(
        f"{AUTH_PREFIX}/me",
        headers=auth_headers(
            "not.a.valid.jwt"
        ),
    )

    assert response.status_code == 401

    assert response.json()["detail"] == (
        "Could not validate credentials"
    )


# ------------------------------------------------------------------
# JWT signed with wrong secret
# ------------------------------------------------------------------


def test_jwt_signed_with_wrong_secret_is_rejected(
    client,
):
    user = create_user(client)

    token = jwt.encode(
        {
            "sub": user["email"],
            "user_id": 999999,
            "role": "user",
            "exp": (
                datetime.now(timezone.utc)
                + timedelta(minutes=30)
            ),
        },
        "definitely-wrong-secret",
        algorithm=settings.ALGORITHM,
    )

    response = client.get(
        f"{AUTH_PREFIX}/me",
        headers=auth_headers(token),
    )

    assert response.status_code == 401

    assert response.json()["detail"] == (
        "Could not validate credentials"
    )


# ------------------------------------------------------------------
# Missing subject claim
# ------------------------------------------------------------------


def test_jwt_without_subject_is_rejected(
    client,
):
    token = jwt.encode(
        {
            "user_id": 1,
            "role": "user",
            "exp": (
                datetime.now(timezone.utc)
                + timedelta(minutes=30)
            ),
        },
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

    response = client.get(
        f"{AUTH_PREFIX}/me",
        headers=auth_headers(token),
    )

    assert response.status_code == 401

    assert response.json()["detail"] == (
        "Could not validate credentials"
    )


# ------------------------------------------------------------------
# Unknown user in validly signed JWT
# ------------------------------------------------------------------


def test_jwt_for_unknown_user_is_rejected(
    client,
):
    token = jwt.encode(
        {
            "sub": "does-not-exist@example.com",
            "user_id": 999999999,
            "role": "user",
            "exp": (
                datetime.now(timezone.utc)
                + timedelta(minutes=30)
            ),
        },
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

    response = client.get(
        f"{AUTH_PREFIX}/me",
        headers=auth_headers(token),
    )

    assert response.status_code == 401

    assert response.json()["detail"] == (
        "Could not validate credentials"
    )


# ------------------------------------------------------------------
# Expired token
# ------------------------------------------------------------------


def test_expired_access_token_is_rejected(
    client,
):
    user = create_user(client)

    token = jwt.encode(
        {
            "sub": user["email"],
            "user_id": 1,
            "role": "user",
            "exp": (
                datetime.now(timezone.utc)
                - timedelta(minutes=1)
            ),
        },
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

    response = client.get(
        f"{AUTH_PREFIX}/me",
        headers=auth_headers(token),
    )

    assert response.status_code == 401

    assert response.json()["detail"] == (
        "Could not validate credentials"
    )


# ------------------------------------------------------------------
# Wrong algorithm
# ------------------------------------------------------------------


def test_wrong_algorithm_is_rejected(
    client,
):
    user = create_user(client)

    # HS384 is intentionally different from
    # the configured algorithm.
    token = jwt.encode(
        {
            "sub": user["email"],
            "user_id": 1,
            "role": "user",
            "exp": (
                datetime.now(timezone.utc)
                + timedelta(minutes=30)
            ),
        },
        settings.SECRET_KEY,
        algorithm="HS384",
    )

    response = client.get(
        f"{AUTH_PREFIX}/me",
        headers=auth_headers(token),
    )

    assert response.status_code == 401


# ------------------------------------------------------------------
# JWT payload tampering
# ------------------------------------------------------------------


def test_tampered_jwt_is_rejected(
    client,
):
    user = create_user(client)
    tokens = login(client, user)

    access_token = tokens["access_token"]

    header = jwt.get_unverified_header(
        access_token
    )

    payload = jwt.get_unverified_claims(
        access_token
    )

    payload["sub"] = (
        "attacker@example.com"
    )

    tampered_token = jwt.encode(
        payload,
        "wrong-secret",
        algorithm=header["alg"],
    )

    response = client.get(
        f"{AUTH_PREFIX}/me",
        headers=auth_headers(
            tampered_token
        ),
    )

    assert response.status_code == 401


# ------------------------------------------------------------------
# Token type response
# ------------------------------------------------------------------


def test_login_returns_bearer_token_type(
    client,
):
    user = create_user(client)

    tokens = login(client, user)

    assert tokens["token_type"] == "bearer"

    assert isinstance(
        tokens["access_token"],
        str,
    )

    assert isinstance(
        tokens["refresh_token"],
        str,
    )