from enum import Enum


class NotificationProvider(str, Enum):
    """Supported notification providers."""

    EMAIL = "email"
    SLACK = "slack"
    TEAMS = "teams"


class NotificationSeverity(str, Enum):
    """Severity levels for notifications."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class NotificationStatus(str, Enum):
    """Delivery status of a notification."""

    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"