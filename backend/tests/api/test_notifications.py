from datetime import datetime, timezone

from app.models.notification import Notification
from app.models.user import User
from app.notifications.enums import (
    NotificationProvider,
    NotificationSeverity,
    NotificationStatus,
)
from sqlmodel import select

def get_authenticated_user(db_session):
    """Get the user created by the auth_headers fixture."""

    statement = select(User).where(
        User.email == "pytest@example.com"
    )

    user = db_session.exec(statement).first()

    assert user is not None

    return user

def get_other_user(db_session, current_user):
    """Get or create a second valid user for isolation tests."""

    statement = select(User).where(
        User.username == "notification_other_user"
    )

    user = db_session.exec(statement).first()

    if user is not None:
        return user

    user = User(
        username="notification_other_user",
        email="notification_other@example.com",
        full_name="Notification Other User",
        hashed_password="test-hashed-password",
        role="user",
        is_active=True,
        is_verified=True,
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    return user

def create_notification(
    db_session,
    user_id: int,
    *,
    is_read: bool = False,
):
    """Create a notification directly for API testing."""

    notification = Notification(
        user_id=user_id,
        provider=NotificationProvider.EMAIL,
        severity=NotificationSeverity.INFO,
        status=NotificationStatus.SENT,
        subject="Test notification",
        message="Test message",
        is_read=is_read,
        read_at=(
            datetime.now(timezone.utc)
            if is_read
            else None
        ),
    )

    db_session.add(notification)
    db_session.commit()
    db_session.refresh(notification)

    return notification


def test_get_notifications_returns_current_user_notifications_only(
    client,
    db_session,
    auth_headers,
):
    """Authenticated users should only receive their own notifications."""

    user = get_authenticated_user(db_session)

    own_notification = create_notification(
        db_session,
        user.id,
    )

    other_user = get_other_user(
    db_session,
    user,
)

    other_notification = create_notification(
        db_session,
        other_user.id,
    )

    response = client.get(
        "/api/v1/notifications",
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    ids = {item["id"] for item in data}

    assert own_notification.id in ids
    assert other_notification.id not in ids


def test_filter_unread_notifications(
    client,
    db_session,
    auth_headers,
):
    """is_read=false should return only unread notifications."""

    user = get_authenticated_user(db_session)

    unread = create_notification(
        db_session,
        user.id,
        is_read=False,
    )

    create_notification(
        db_session,
        user.id,
        is_read=True,
    )

    response = client.get(
        "/api/v1/notifications?is_read=false",
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert all(
        item["is_read"] is False
        for item in data
    )

    ids = {item["id"] for item in data}

    assert unread.id in ids


def test_filter_read_notifications(
    client,
    db_session,
    auth_headers,
):
    """is_read=true should return only read notifications."""

    user = get_authenticated_user(db_session)

    create_notification(
        db_session,
        user.id,
        is_read=False,
    )

    read_notification = create_notification(
        db_session,
        user.id,
        is_read=True,
    )

    response = client.get(
        "/api/v1/notifications?is_read=true",
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert all(
        item["is_read"] is True
        for item in data
    )

    ids = {item["id"] for item in data}

    assert read_notification.id in ids


def test_unread_count(
    client,
    db_session,
    auth_headers,
):
    """Unread count should count only the current user's unread notifications."""

    user = get_authenticated_user(db_session)

    create_notification(
        db_session,
        user.id,
        is_read=False,
    )

    create_notification(
        db_session,
        user.id,
        is_read=False,
    )

    create_notification(
        db_session,
        user.id,
        is_read=True,
    )

    response = client.get(
        "/api/v1/notifications/unread-count",
        headers=auth_headers,
    )

    assert response.status_code == 200

    assert response.json() >= 2


def test_mark_notification_read(
    client,
    db_session,
    auth_headers,
):
    """A user can mark their own notification as read."""

    user = get_authenticated_user(db_session)

    notification = create_notification(
        db_session,
        user.id,
        is_read=False,
    )

    response = client.patch(
        f"/api/v1/notifications/{notification.id}/read",
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == notification.id
    assert data["is_read"] is True
    assert data["read_at"] is not None

    db_session.refresh(notification)

    assert notification.is_read is True
    assert notification.read_at is not None


def test_mark_already_read_notification(
    client,
    db_session,
    auth_headers,
):
    """Marking an already-read notification should remain successful."""

    user = get_authenticated_user(db_session)

    notification = create_notification(
        db_session,
        user.id,
        is_read=True,
    )

    original_read_at = notification.read_at

    response = client.patch(
        f"/api/v1/notifications/{notification.id}/read",
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["is_read"] is True
    assert data["read_at"] is not None

    db_session.refresh(notification)

    assert notification.is_read is True
    assert notification.read_at == original_read_at


def test_mark_all_notifications_read(
    client,
    db_session,
    auth_headers,
):
    """Mark all unread notifications for the current user as read."""

    user = get_authenticated_user(db_session)

    first = create_notification(
        db_session,
        user.id,
        is_read=False,
    )

    second = create_notification(
        db_session,
        user.id,
        is_read=False,
    )

    create_notification(
        db_session,
        user.id,
        is_read=True,
    )

    response = client.patch(
        "/api/v1/notifications/read-all",
        headers=auth_headers,
    )

    assert response.status_code == 200

    assert response.json() >= 2

    db_session.refresh(first)
    db_session.refresh(second)

    assert first.is_read is True
    assert first.read_at is not None

    assert second.is_read is True
    assert second.read_at is not None


def test_mark_all_does_not_modify_other_users_notifications(
    client,
    db_session,
    auth_headers,
):
    """read-all must not modify another user's notifications."""

    user = get_authenticated_user(db_session)

    other_user = get_other_user(
    db_session,
    user,
)

    other_notification = create_notification(
        db_session,
        other_user.id,
        is_read=False,
    )

    response = client.patch(
        "/api/v1/notifications/read-all",
        headers=auth_headers,
    )

    assert response.status_code == 200

    db_session.refresh(other_notification)

    assert other_notification.is_read is False
    assert other_notification.read_at is None


def test_cannot_mark_another_users_notification_read(
    client,
    db_session,
    auth_headers,
):
    """A user cannot mark another user's notification as read."""

    user = get_authenticated_user(db_session)

    other_user = get_other_user(
    db_session,
    user,
    )

    other_notification = create_notification(
        db_session,
        other_user.id,
        is_read=False,
    )
    response = client.patch(
        f"/api/v1/notifications/{other_notification.id}/read",
        headers=auth_headers,
    )

    assert response.status_code == 404

    db_session.refresh(other_notification)

    assert other_notification.is_read is False
    assert other_notification.read_at is None


def test_nonexistent_notification_read_returns_404(
    client,
    auth_headers,
):
    """Reading a nonexistent notification should return 404."""

    response = client.patch(
        "/api/v1/notifications/999999999/read",
        headers=auth_headers,
    )

    assert response.status_code == 404


def test_notifications_require_authentication(
    client,
):
    """Notification endpoints require authentication."""

    response = client.get(
        "/api/v1/notifications"
    )

    assert response.status_code in {401, 403}
    
