from dataclasses import dataclass, field
from typing import Any, Optional

from .enums import NotificationSeverity


@dataclass
class NotificationMessage:
    """Represents a notification before delivery."""

    subject: str
    message: str
    severity: NotificationSeverity = NotificationSeverity.INFO

    recipient: Optional[str] = None

    metadata: dict[str, Any] = field(default_factory=dict)