import pytest

from app.notifications.exceptions import UnsupportedNotificationProvider
from app.notifications.manager import NotificationManager
from app.notifications.providers.base import NotificationProviderBase
from app.notifications.types import NotificationMessage


class FakeProvider(NotificationProviderBase):
    """Fake provider used for unit testing."""

    @property
    def name(self) -> str:
        return "fake"

    async def send(self, notification: NotificationMessage) -> bool:
        return True


@pytest.mark.asyncio
async def test_register_provider():
    manager = NotificationManager()
    provider = FakeProvider()

    manager.register_provider(provider)

    assert manager.get_provider("fake") is provider


@pytest.mark.asyncio
async def test_send_notification():
    manager = NotificationManager()
    provider = FakeProvider()

    manager.register_provider(provider)

    notification = NotificationMessage(
        subject="Test Notification",
        message="This is a test notification.",
    )

    result = await manager.send(
        "fake",
        notification,
    )

    assert result is True


def test_unknown_provider():
    manager = NotificationManager()

    with pytest.raises(UnsupportedNotificationProvider):
        manager.get_provider("unknown")
        
def test_list_providers():
    manager = NotificationManager()

    manager.register_provider(FakeProvider())

    assert manager.list_providers() == ["fake"]