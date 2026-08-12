from uuid import uuid4

from sqlmodel import select

from app.auth.hashing import hash_password, verify_password
from app.models.user import User


AUTH_PREFIX = "/api/v1/auth"


def create_user_payload():
    suffix = uuid4().hex[:10]

    return {
        "username": f"passwordsec_{suffix}",
        "email": f"passwordsec_{suffix}@example.com",
        "password": "StrongPassword123!",
        "full_name": "Password Security User",
    }


# ------------------------------------------------------------------
# Password hashing
# ------------------------------------------------------------------


def test_password_hash_is_not_plaintext():
    password = "StrongPassword123!"

    hashed = hash_password(password)

    assert hashed != password
    assert hashed.startswith("$2")

    assert verify_password(
        password,
        hashed,
    ) is True

    assert verify_password(
        "WrongPassword123!",
        hashed,
    ) is False


def test_password_hashes_are_unique():
    password = "StrongPassword123!"

    hash_one = hash_password(password)
    hash_two = hash_password(password)

    assert hash_one != hash_two

    assert verify_password(
        password,
        hash_one,
    ) is True

    assert verify_password(
        password,
        hash_two,
    ) is True


# ------------------------------------------------------------------
# Registration password storage
# ------------------------------------------------------------------


def test_registration_stores_hashed_password(
    client,
    db_session,
):
    payload = create_user_payload()

    response = client.post(
        f"{AUTH_PREFIX}/register",
        json=payload,
    )

    assert response.status_code == 201

    data = response.json()

    # Password must never appear in the response.
    assert "password" not in data
    assert "hashed_password" not in data

    db_user = db_session.exec(
        select(User).where(
            User.email == payload["email"]
        )
    ).one()

    assert db_user.hashed_password != payload["password"]

    assert db_user.hashed_password.startswith("$2")

    assert verify_password(
        payload["password"],
        db_user.hashed_password,
    ) is True


# ------------------------------------------------------------------
# Password must never be returned by /me
# ------------------------------------------------------------------


def test_current_user_does_not_expose_password(
    client,
    auth_headers,
):
    response = client.get(
        f"{AUTH_PREFIX}/me",
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert "password" not in data
    assert "hashed_password" not in data


# ------------------------------------------------------------------
# Profile must not expose password
# ------------------------------------------------------------------


def test_profile_does_not_expose_password(
    client,
    auth_headers,
):
    response = client.get(
        f"{AUTH_PREFIX}/profile",
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert "password" not in data
    assert "hashed_password" not in data


# ------------------------------------------------------------------
# Login verifies hashed password
# ------------------------------------------------------------------


def test_login_accepts_original_password(
    client,
):
    payload = create_user_payload()

    register_response = client.post(
        f"{AUTH_PREFIX}/register",
        json=payload,
    )

    assert register_response.status_code == 201

    response = client.post(
        f"{AUTH_PREFIX}/login",
        data={
            "username": payload["email"],
            "password": payload["password"],
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert "refresh_token" in data


# ------------------------------------------------------------------
# Wrong password must fail
# ------------------------------------------------------------------


def test_login_rejects_wrong_password(
    client,
):
    payload = create_user_payload()

    register_response = client.post(
        f"{AUTH_PREFIX}/register",
        json=payload,
    )

    assert register_response.status_code == 201

    response = client.post(
        f"{AUTH_PREFIX}/login",
        data={
            "username": payload["email"],
            "password": "CompletelyWrongPassword123!",
        },
    )

    assert response.status_code == 401

    assert response.json()["detail"] == (
        "Invalid email or password"
    )


# ------------------------------------------------------------------
# Password must not be accepted as hashed_password
# ------------------------------------------------------------------


def test_registration_does_not_accept_client_hashed_password(
    client,
    db_session,
):
    payload = create_user_payload()

    payload["hashed_password"] = (
        "$2b$12$client_supplied_fake_hash"
    )

    response = client.post(
        f"{AUTH_PREFIX}/register",
        json=payload,
    )

    assert response.status_code == 201

    db_user = db_session.exec(
        select(User).where(
            User.email == payload["email"]
        )
    ).one()

    # The server-generated hash must be used.
    assert db_user.hashed_password != (
        payload["hashed_password"]
    )

    assert verify_password(
        payload["password"],
        db_user.hashed_password,
    ) is True


# ------------------------------------------------------------------
# Password is never stored in UserRead response
# ------------------------------------------------------------------


def test_registration_response_contains_only_safe_user_fields(
    client,
):
    payload = create_user_payload()

    response = client.post(
        f"{AUTH_PREFIX}/register",
        json=payload,
    )

    assert response.status_code == 201

    data = response.json()

    forbidden_fields = {
        "password",
        "hashed_password",
        "refresh_token",
        "token_hash",
    }

    assert forbidden_fields.isdisjoint(
        data.keys()
    )