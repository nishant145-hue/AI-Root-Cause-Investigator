from datetime import datetime, timedelta
from uuid import uuid4

from sqlmodel import select

from app.core.config import settings
from app.models.user import User


AUTH_PREFIX = "/api/v1/auth"


def create_user(client):
    suffix = uuid4().hex[:10]

    user = {
        "username": f"lockout_{suffix}",
        "email": f"lockout_{suffix}@example.com",
        "password": "Password123!",
        "full_name": "Lockout Security User",
    }

    response = client.post(
        f"{AUTH_PREFIX}/register",
        json=user,
    )

    assert response.status_code == 201

    return user


def login(client, user, password=None):
    response = client.post(
        f"{AUTH_PREFIX}/login",
        data={
            "username": user["email"],
            "password": password or user["password"],
        },
    )

    return response


# ------------------------------------------------------------------
# Failed login counter
# ------------------------------------------------------------------


def test_failed_login_increments_attempt_counter(
    client,
    db_session,
):
    user = create_user(client)

    response = login(
        client,
        user,
        password="WrongPassword123!",
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"

    db_user = db_session.exec(
        select(User).where(
            User.email == user["email"]
        )
    ).one()

    assert db_user.failed_login_attempts == 1
    assert db_user.locked_until is None


# ------------------------------------------------------------------
# Successful login resets failed attempts
# ------------------------------------------------------------------


def test_successful_login_resets_failed_attempts(
    client,
    db_session,
):
    user = create_user(client)

    # Create failed attempts first.
    for _ in range(2):
        response = login(
            client,
            user,
            password="WrongPassword123!",
        )
        assert response.status_code == 401

    db_user = db_session.exec(
        select(User).where(
            User.email == user["email"]
        )
    ).one()

    assert db_user.failed_login_attempts == 2

    # Correct password should reset the counter.
    response = login(client, user)

    assert response.status_code == 200

    db_session.refresh(db_user)

    assert db_user.failed_login_attempts == 0
    assert db_user.locked_until is None


# ------------------------------------------------------------------
# Account lockout threshold
# ------------------------------------------------------------------


def test_account_locks_after_max_failed_attempts(
    client,
    db_session,
):
    user = create_user(client)

    for attempt in range(
        settings.MAX_FAILED_LOGIN_ATTEMPTS
    ):
        response = login(
            client,
            user,
            password="WrongPassword123!",
        )

        assert response.status_code == 401

    db_user = db_session.exec(
        select(User).where(
            User.email == user["email"]
        )
    ).one()

    assert (
        db_user.failed_login_attempts
        == settings.MAX_FAILED_LOGIN_ATTEMPTS
    )

    assert db_user.locked_until is not None

    assert (
        db_user.locked_until
        > datetime.utcnow()
    )


# ------------------------------------------------------------------
# Correct password cannot bypass active lock
# ------------------------------------------------------------------


def test_locked_account_rejects_correct_password(
    client,
    db_session,
):
    user = create_user(client)

    for _ in range(
        settings.MAX_FAILED_LOGIN_ATTEMPTS
    ):
        response = login(
            client,
            user,
            password="WrongPassword123!",
        )

        assert response.status_code == 401

    # Correct password must still be rejected
    # while the account remains locked.
    response = login(client, user)

    assert response.status_code == 401
    assert response.json()["detail"] == (
        "Invalid email or password"
    )


# ------------------------------------------------------------------
# Lockout duration
# ------------------------------------------------------------------


def test_lockout_uses_configured_duration(
    client,
    db_session,
):
    user = create_user(client)

    for _ in range(
        settings.MAX_FAILED_LOGIN_ATTEMPTS
    ):
        response = login(
            client,
            user,
            password="WrongPassword123!",
        )

        assert response.status_code == 401

    db_user = db_session.exec(
        select(User).where(
            User.email == user["email"]
        )
    ).one()

    now = datetime.utcnow()

    expected_minimum = (
        now
        + timedelta(
            minutes=settings.LOGIN_LOCKOUT_MINUTES
        )
        - timedelta(seconds=5)
    )

    expected_maximum = (
        now
        + timedelta(
            minutes=settings.LOGIN_LOCKOUT_MINUTES
        )
        + timedelta(seconds=5)
    )

    assert (
        db_user.locked_until
        >= expected_minimum
    )

    assert (
        db_user.locked_until
        <= expected_maximum
    )


# ------------------------------------------------------------------
# Expired lock is automatically cleared
# ------------------------------------------------------------------


def test_expired_lock_is_automatically_cleared(
    client,
    db_session,
):
    user = create_user(client)

    db_user = db_session.exec(
        select(User).where(
            User.email == user["email"]
        )
    ).one()

    # Simulate an expired account lock.
    db_user.failed_login_attempts = (
        settings.MAX_FAILED_LOGIN_ATTEMPTS
    )

    db_user.locked_until = (
        datetime.utcnow()
        - timedelta(minutes=1)
    )

    db_session.add(db_user)
    db_session.commit()
    db_session.refresh(db_user)

    # Correct credentials should work because
    # the lock has expired.
    response = login(client, user)

    assert response.status_code == 200

    db_session.refresh(db_user)

    assert db_user.failed_login_attempts == 0
    assert db_user.locked_until is None


# ------------------------------------------------------------------
# Failed attempts are isolated per user
# ------------------------------------------------------------------


def test_failed_attempts_do_not_affect_another_user(
    client,
    db_session,
):
    user_a = create_user(client)
    user_b = create_user(client)

    for _ in range(2):
        response = login(
            client,
            user_a,
            password="WrongPassword123!",
        )

        assert response.status_code == 401

    db_user_a = db_session.exec(
        select(User).where(
            User.email == user_a["email"]
        )
    ).one()

    db_user_b = db_session.exec(
        select(User).where(
            User.email == user_b["email"]
        )
    ).one()

    assert db_user_a.failed_login_attempts == 2
    assert db_user_b.failed_login_attempts == 0

    # User B should still be able to log in.
    response = login(client, user_b)

    assert response.status_code == 200


# ------------------------------------------------------------------
# Account enumeration protection
# ------------------------------------------------------------------


def test_unknown_user_uses_same_authentication_error(
    client,
):
    suffix = uuid4().hex[:10]

    response = client.post(
        f"{AUTH_PREFIX}/login",
        data={
            "username": f"doesnotexist_{suffix}@example.com",
            "password": "WrongPassword123!",
        },
    )

    assert response.status_code == 401

    assert response.json()["detail"] == (
        "Invalid email or password"
    )