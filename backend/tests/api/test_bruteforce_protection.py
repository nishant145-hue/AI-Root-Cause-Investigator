from datetime import datetime, timedelta

from sqlmodel import select

from app.core.config import settings
from app.models.user import User


AUTH_PREFIX = "/api/v1/auth"


def create_bruteforce_test_user(client):
    """
    Create a unique user for brute-force protection tests.
    """
    suffix = datetime.utcnow().strftime("%f")

    user = {
        "username": f"brute_{suffix}",
        "email": f"brute_{suffix}@example.com",
        "password": "Password123!",
        "full_name": "Brute Force Test",
    }

    response = client.post(
        f"{AUTH_PREFIX}/register",
        json=user,
    )

    assert response.status_code == 201

    return user


def failed_login(client, email):
    """
    Perform one failed login attempt.
    """
    response = client.post(
        f"{AUTH_PREFIX}/login",
        data={
            "username": email,
            "password": "WrongPassword123!",
        },
    )

    assert response.status_code == 401

    return response


def successful_login(client, email, password):
    """
    Perform a successful login.
    """
    return client.post(
        f"{AUTH_PREFIX}/login",
        data={
            "username": email,
            "password": password,
        },
    )


# ------------------------------------------------------------------
# Failed login attempt tracking
# ------------------------------------------------------------------


def test_login_failed_attempts_are_tracked(
    client,
    db_session,
):
    """
    Failed login attempts must be persisted.
    """
    user = create_bruteforce_test_user(client)

    # First failed login.
    failed_login(
        client,
        user["email"],
    )

    # Second failed login.
    failed_login(
        client,
        user["email"],
    )

    # The API uses a different database session.
    # Refresh our test-session object before checking
    # the value committed by the API session.
    db_user = db_session.exec(
        select(User).where(
            User.email == user["email"]
        )
    ).first()

    assert db_user is not None

    db_session.refresh(db_user)

    assert db_user.failed_login_attempts == 2
    assert db_user.locked_until is None


# ------------------------------------------------------------------
# Account lockout
# ------------------------------------------------------------------


def test_login_locks_account_after_max_failed_attempts(
    client,
    db_session,
):
    """
    Account must be temporarily locked after the
    configured number of failed login attempts.
    """
    user = create_bruteforce_test_user(client)

    for _ in range(
        settings.MAX_FAILED_LOGIN_ATTEMPTS
    ):
        failed_login(
            client,
            user["email"],
        )

    db_user = db_session.exec(
        select(User).where(
            User.email == user["email"]
        )
    ).first()

    assert db_user is not None

    db_session.refresh(db_user)

    assert (
        db_user.failed_login_attempts
        >= settings.MAX_FAILED_LOGIN_ATTEMPTS
    )

    assert db_user.locked_until is not None

    assert (
        db_user.locked_until
        > datetime.utcnow()
    )


# ------------------------------------------------------------------
# Locked account protection
# ------------------------------------------------------------------


def test_locked_account_cannot_login_with_correct_password(
    client,
    db_session,
):
    """
    A locked account must not be able to authenticate
    even when the correct password is supplied.
    """
    user = create_bruteforce_test_user(client)

    # Trigger account lockout.
    for _ in range(
        settings.MAX_FAILED_LOGIN_ATTEMPTS
    ):
        failed_login(
            client,
            user["email"],
        )

    db_user = db_session.exec(
        select(User).where(
            User.email == user["email"]
        )
    ).first()

    assert db_user is not None

    db_session.refresh(db_user)

    assert db_user.locked_until is not None

    # Correct password must still be rejected.
    response = successful_login(
        client,
        user["email"],
        user["password"],
    )

    assert response.status_code == 401


# ------------------------------------------------------------------
# Successful login resets failed attempts
# ------------------------------------------------------------------


def test_successful_login_resets_failed_attempts(
    client,
    db_session,
):
    """
    A successful login must reset failed login attempts
    and clear any active lock.
    """
    user = create_bruteforce_test_user(client)

    # Create failed attempts without reaching lockout.
    failed_attempts = max(
        1,
        settings.MAX_FAILED_LOGIN_ATTEMPTS - 1,
    )

    for _ in range(failed_attempts):
        failed_login(
            client,
            user["email"],
        )

    db_user = db_session.exec(
        select(User).where(
            User.email == user["email"]
        )
    ).first()

    assert db_user is not None

    db_session.refresh(db_user)

    assert (
        db_user.failed_login_attempts
        == failed_attempts
    )

    # Successful login.
    response = successful_login(
        client,
        user["email"],
        user["password"],
    )

    assert response.status_code == 200

    # Refresh because login uses another DB session.
    db_session.refresh(db_user)

    assert db_user.failed_login_attempts == 0
    assert db_user.locked_until is None


# ------------------------------------------------------------------
# Expired lock
# ------------------------------------------------------------------


def test_expired_lock_is_cleared(
    client,
    db_session,
):
    """
    An expired account lock must be automatically cleared
    and the user must be allowed to log in.
    """
    user = create_bruteforce_test_user(client)

    db_user = db_session.exec(
        select(User).where(
            User.email == user["email"]
        )
    ).first()

    assert db_user is not None

    # Simulate an expired lock.
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

    assert db_user.locked_until is not None

    # Login should succeed because the lock has expired.
    response = successful_login(
        client,
        user["email"],
        user["password"],
    )

    assert response.status_code == 200

    # Reload the database state written by the API.
    db_session.refresh(db_user)

    assert db_user.failed_login_attempts == 0
    assert db_user.locked_until is None