from app.notifications.manager import NotificationManager
from app.notifications.providers import (
    EmailNotificationProvider,
    SlackNotificationProvider,
    TeamsNotificationProvider,
)


def create_notification_manager() -> NotificationManager:
    """Create and configure the application's notification manager."""

    manager = NotificationManager()

    manager.register_provider(
        EmailNotificationProvider()
    )

    manager.register_provider(
        SlackNotificationProvider()
    )

    manager.register_provider(
        TeamsNotificationProvider()
    )

    return manager