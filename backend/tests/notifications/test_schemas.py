from app.notifications.enums import (
    NotificationProvider,
    NotificationSeverity,
    NotificationStatus,
)
from app.schemas.notification import (
    NotificationCreate,
    NotificationRead,
)
from app.schemas.notification_preference import (
    NotificationPreferenceCreate,
    NotificationPreferenceRead,
    NotificationPreferenceUpdate,
)


def test_notification_create_schema():
    notification = NotificationCreate(
        user_id=1,
        provider=NotificationProvider.EMAIL,
        severity=NotificationSeverity.CRITICAL,
        subject="Critical Incident",
        message="Database connection pool exhausted.",
    )

    assert notification.user_id == 1
    assert notification.provider == NotificationProvider.EMAIL
    assert notification.severity == NotificationSeverity.CRITICAL


def test_notification_preference_create_schema():
    preference = NotificationPreferenceCreate(
        user_id=1,
        email_enabled=True,
        slack_enabled=True,
        teams_enabled=False,
        critical_only=True,
    )

    assert preference.user_id == 1
    assert preference.email_enabled is True
    assert preference.slack_enabled is True
    assert preference.critical_only is True


def test_notification_preference_update_schema():
    update = NotificationPreferenceUpdate(
        email_enabled=False,
        slack_enabled=True,
    )

    assert update.email_enabled is False
    assert update.slack_enabled is True


def test_notification_read_schema():
    from datetime import datetime, timezone

    notification = NotificationRead(
        id=1,
        user_id=1,
        provider=NotificationProvider.EMAIL,
        severity=NotificationSeverity.INFO,
        subject="Test",
        message="Test message",
        status=NotificationStatus.SENT,
        retry_count=0,
        error_message=None,
        created_at=datetime.now(timezone.utc),
        sent_at=datetime.now(timezone.utc),
        is_read=False,
        read_at=None,
        is_archived=False,
        archived_at=None,
    )

    assert notification.id == 1
    assert notification.status == NotificationStatus.SENT