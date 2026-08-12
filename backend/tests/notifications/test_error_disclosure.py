import pytest

from app.models.notification import Notification
from app.notifications.enums import (
    NotificationProvider,
    NotificationSeverity,
    NotificationStatus,
)
from app.notifications.manager import NotificationManager
from app.notifications.providers.base import NotificationProviderBase
from app.notifications.service import NotificationService
from app.notifications.types import NotificationMessage


class SecretFailingProvider(NotificationProviderBase):
    """Provider that raises an exception containing sensitive data."""

    @property
    def name(self) -> str:
        return "email"

    async def send(
        self,
        notification: NotificationMessage,
    ) -> bool:
        raise RuntimeError(
            "API_KEY=SUPER_SECRET_123 "
            "postgresql://admin:password@internal-db "
            "C:\\production\\private\\config.env"
        )


@pytest.mark.asyncio
async def test_notification_failure_does_not_persist_sensitive_exception_details(
    db_session,
):
    manager = NotificationManager()
    manager.register_provider(
        SecretFailingProvider()
    )

    service = NotificationService(
        db_session,
        manager,
    )

    notification = service.create_notification(
        user_id=1,
        provider=NotificationProvider.EMAIL,
        severity=NotificationSeverity.CRITICAL,
        subject="Security Test",
        message="Sensitive exception persistence test",
    )

    result = await service.deliver(
        notification,
        recipient="test@example.com",
    )

    assert result is False
    assert notification.status == NotificationStatus.FAILED
    assert notification.retry_count == 1

    # The notification may contain a safe diagnostic,
    # but it must never contain the original exception.
    error_message = notification.error_message or ""

    assert "API_KEY=SUPER_SECRET_123" not in error_message
    assert "postgresql://admin:password@internal-db" not in error_message
    assert "C:\\production\\private\\config.env" not in error_message


@pytest.mark.asyncio
async def test_notification_failure_persists_safe_error_information(
    db_session,
):
    manager = NotificationManager()
    manager.register_provider(
        SecretFailingProvider()
    )

    service = NotificationService(
        db_session,
        manager,
    )

    notification = service.create_notification(
        user_id=1,
        provider=NotificationProvider.EMAIL,
        severity=NotificationSeverity.ERROR,
        subject="Safe Error Test",
        message="Safe notification error test",
    )

    result = await service.deliver(
        notification,
    )

    assert result is False

    db_session.refresh(notification)

    assert notification.status == NotificationStatus.FAILED
    assert notification.retry_count == 1

    error_message = notification.error_message or ""

    assert "API_KEY=" not in error_message
    assert "postgresql://" not in error_message
    assert "C:\\production" not in error_message