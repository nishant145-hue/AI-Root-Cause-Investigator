from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Session

from app.models.notification import Notification
from app.notifications.enums import (
    NotificationProvider,
    NotificationSeverity,
    NotificationStatus,
)
from app.notifications.exceptions import NotificationError
from app.notifications.manager import NotificationManager
from app.notifications.preferences import (
    NotificationPreferenceService,
)
from app.notifications.retry import RetryPolicy
from app.notifications.types import NotificationMessage


class NotificationService:
    """Service responsible for creating and delivering notifications."""

    def __init__(
    self,
    session: Session,
    manager: NotificationManager,
    retry_policy: RetryPolicy | None = None,
    preference_service: NotificationPreferenceService | None = None,
) -> None:
        self.session = session
        self.manager = manager
        self.retry_policy = retry_policy or RetryPolicy()

        self.preference_service = (
            preference_service
            or NotificationPreferenceService(session)
        )
    def create_notification(
        self,
        *,
        user_id: Optional[int],
        provider: NotificationProvider,
        severity: NotificationSeverity,
        subject: str,
        message: str,
        metadata: Optional[dict] = None,
    ) -> Notification:
        """Create and persist a notification."""

        notification = Notification(
            user_id=user_id,
            provider=provider,
            severity=severity,
            status=NotificationStatus.PENDING,
            subject=subject,
            message=message,
            metadata_json=metadata or {},
        )

        self.session.add(notification)
        self.session.commit()
        self.session.refresh(notification)

        return notification
    
    async def deliver(
    self,
    notification: Notification,
    recipient: Optional[str] = None,
) -> bool:
        """Deliver an existing notification through its provider."""

        # Check user notification preferences before delivery.
        if not self.should_deliver(notification):
            return False

        notification_message = NotificationMessage(
            subject=notification.subject,
            message=notification.message,
            severity=notification.severity,
            recipient=recipient,
            metadata=notification.metadata_json,
        )

        try:
            provider = self.manager.get_provider(
                notification.provider.value
            )

            success = await provider.send(notification_message)

            if success:
                notification.status = NotificationStatus.SENT
                notification.sent_at = datetime.now(timezone.utc)
                notification.error_message = None
            else:
                notification.status = NotificationStatus.FAILED
                notification.retry_count += 1

            self.session.add(notification)
            self.session.commit()
            self.session.refresh(notification)

            return success

        except Exception:
            notification.status = NotificationStatus.FAILED
            notification.retry_count += 1
            notification.error_message = (
                "Notification delivery failed."
            )

            self.session.add(notification)
            self.session.commit()
            self.session.refresh(notification)

            return False
        

    async def create_and_deliver(
        self,
        *,
        user_id: Optional[int],
        provider: NotificationProvider,
        severity: NotificationSeverity,
        subject: str,
        message: str,
        recipient: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> Notification:
        """Create a notification and immediately attempt delivery."""

        notification = self.create_notification(
            user_id=user_id,
            provider=provider,
            severity=severity,
            subject=subject,
            message=message,
            metadata=metadata,
        )

        await self.deliver(
            notification,
            recipient=recipient,
        )

        return notification
    
    def can_retry(self, notification: Notification) -> bool:
        """Return whether the notification can be retried."""

        return self.retry_policy.can_retry(
            notification.retry_count
        )
        
    async def retry_delivery(
    self,
    notification: Notification,
    recipient: Optional[str] = None,
) -> bool:
        """Retry delivery of a failed notification."""

        if not self.can_retry(notification):
            return False

        return await self.deliver(
            notification,
            recipient=recipient,
        )
        
    def should_deliver(
    self,
    notification: Notification,
) -> bool:
        """Determine whether notification should be delivered."""

        if notification.user_id is None:
            return True

        preference = self.preference_service.get_or_create(
            notification.user_id
        )

        return self.preference_service.should_send(
            preference,
            notification.provider,
            notification.severity,
        )