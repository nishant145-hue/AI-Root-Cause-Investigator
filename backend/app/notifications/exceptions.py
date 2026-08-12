class NotificationError(Exception):
    """Base exception for notification errors."""


class NotificationProviderError(NotificationError):
    """Raised when a notification provider fails."""


class UnsupportedNotificationProvider(NotificationError):
    """Raised when an unsupported provider is requested."""