from datetime import datetime, timezone

import pytest
from sqlmodel import Session, create_engine, select

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
from app.notifications.preferences import NotificationPreferenceService

class FakeProvider(NotificationProviderBase):
    """Fake successful provider."""

    @property
    def name(self) -> str:
        return "email"

    async def send(self, notification: NotificationMessage) -> bool:
        return True


class FailingProvider(NotificationProviderBase):
    """Fake failing provider."""

    @property
    def name(self) -> str:
        return "email"

    async def send(self, notification: NotificationMessage) -> bool:
        return False

@pytest.fixture
def session():
    """Create an in-memory database session."""

    from app.models.user import User

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
    )

    from sqlmodel import SQLModel

    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        yield session

@pytest.mark.asyncio
async def test_create_notification(session):
    manager = NotificationManager()
    service = NotificationService(session, manager)

    notification = service.create_notification(
        user_id=1,
        provider=NotificationProvider.EMAIL,
        severity=NotificationSeverity.CRITICAL,
        subject="Critical Incident",
        message="Database failure detected.",
    )

    assert notification.id is not None
    assert notification.user_id == 1
    assert notification.status == NotificationStatus.PENDING
    assert notification.severity == NotificationSeverity.CRITICAL


@pytest.mark.asyncio
async def test_successful_delivery(session):
    manager = NotificationManager()
    manager.register_provider(FakeProvider())

    service = NotificationService(session, manager)

    notification = service.create_notification(
        user_id=1,
        provider=NotificationProvider.EMAIL,
        severity=NotificationSeverity.INFO,
        subject="Test",
        message="Test notification",
    )

    result = await service.deliver(
        notification,
        recipient="test@example.com",
    )

    assert result is True
    assert notification.status == NotificationStatus.SENT
    assert notification.sent_at is not None


@pytest.mark.asyncio
async def test_failed_delivery(session):
    manager = NotificationManager()
    manager.register_provider(FailingProvider())

    service = NotificationService(session, manager)

    notification = service.create_notification(
        user_id=1,
        provider=NotificationProvider.EMAIL,
        severity=NotificationSeverity.ERROR,
        subject="Test",
        message="Test notification",
    )

    result = await service.deliver(notification)

    assert result is False
    assert notification.status == NotificationStatus.FAILED


@pytest.mark.asyncio
async def test_create_and_deliver(session):
    manager = NotificationManager()
    manager.register_provider(FakeProvider())

    service = NotificationService(session, manager)

    notification = await service.create_and_deliver(
        user_id=1,
        provider=NotificationProvider.EMAIL,
        severity=NotificationSeverity.WARNING,
        subject="Warning",
        message="Something happened.",
    )

    assert notification.id is not None
    assert notification.status == NotificationStatus.SENT
    
@pytest.mark.asyncio
async def test_failed_delivery_increments_retry_count(session):
    manager = NotificationManager()
    manager.register_provider(FailingProvider())

    service = NotificationService(session, manager)

    notification = service.create_notification(
        user_id=1,
        provider=NotificationProvider.EMAIL,
        severity=NotificationSeverity.ERROR,
        subject="Test",
        message="Test notification",
    )

    assert notification.retry_count == 0

    result = await service.deliver(notification)

    assert result is False
    assert notification.status == NotificationStatus.FAILED
    assert notification.retry_count == 1
    
def test_notification_can_retry(session):
    manager = NotificationManager()

    service = NotificationService(
        session,
        manager,
    )

    notification = Notification(
        retry_count=0,
        provider=NotificationProvider.EMAIL,
        severity=NotificationSeverity.ERROR,
        status=NotificationStatus.FAILED,
        subject="Test",
        message="Test",
    )

    assert service.can_retry(notification) is True

    notification.retry_count = 3

    assert service.can_retry(notification) is False
    
@pytest.mark.asyncio
async def test_disabled_provider_is_not_delivered(session):
    manager = NotificationManager()

    provider = FakeProvider()
    manager.register_provider(provider)

    preference_service = NotificationPreferenceService(session)

    preference = preference_service.get_or_create(1)
    preference.email_enabled = False

    session.add(preference)
    session.commit()
    session.refresh(preference)

    service = NotificationService(
        session=session,
        manager=manager,
        preference_service=preference_service,
    )

    notification = service.create_notification(
        user_id=1,
        provider=NotificationProvider.EMAIL,
        severity=NotificationSeverity.CRITICAL,
        subject="Critical",
        message="Database failure.",
    )

    result = await service.deliver(notification)

    assert result is False
    assert notification.status == NotificationStatus.PENDING
    
@pytest.mark.asyncio
async def test_critical_only_blocks_non_critical(session):
    manager = NotificationManager()

    provider = FakeProvider()
    manager.register_provider(provider)

    preference_service = NotificationPreferenceService(session)

    preference = preference_service.get_or_create(1)
    preference.critical_only = True

    session.add(preference)
    session.commit()
    session.refresh(preference)

    service = NotificationService(
        session=session,
        manager=manager,
        preference_service=preference_service,
    )

    notification = service.create_notification(
        user_id=1,
        provider=NotificationProvider.EMAIL,
        severity=NotificationSeverity.WARNING,
        subject="Warning",
        message="Something happened.",
    )

    result = await service.deliver(notification)

    assert result is False
    assert notification.status == NotificationStatus.PENDING
    
@pytest.mark.asyncio
async def test_critical_only_allows_critical(session):
    manager = NotificationManager()

    provider = FakeProvider()
    manager.register_provider(provider)

    preference_service = NotificationPreferenceService(session)

    preference = preference_service.get_or_create(1)
    preference.critical_only = True

    session.add(preference)
    session.commit()
    session.refresh(preference)

    service = NotificationService(
        session=session,
        manager=manager,
        preference_service=preference_service,
    )

    notification = service.create_notification(
        user_id=1,
        provider=NotificationProvider.EMAIL,
        severity=NotificationSeverity.CRITICAL,
        subject="Critical",
        message="Database failure.",
    )

    result = await service.deliver(notification)

    assert result is True
    assert notification.status == NotificationStatus.SENT
    
@pytest.mark.asyncio
async def test_system_notification_bypasses_user_preferences(session):
    manager = NotificationManager()
    manager.register_provider(FakeProvider())

    preference_service = NotificationPreferenceService(session)

    # User 1 has email disabled.
    preference = preference_service.get_or_create(1)
    preference.email_enabled = False

    session.add(preference)
    session.commit()
    session.refresh(preference)

    service = NotificationService(
        session=session,
        manager=manager,
        preference_service=preference_service,
    )

    # System notification has no user, so preferences should not apply.
    notification = service.create_notification(
        user_id=None,
        provider=NotificationProvider.EMAIL,
        severity=NotificationSeverity.CRITICAL,
        subject="System Critical Alert",
        message="System-wide database failure.",
    )

    result = await service.deliver(
        notification,
        recipient="admin@example.com",
    )

    assert result is True
    assert notification.status == NotificationStatus.SENT
    assert notification.sent_at is not None