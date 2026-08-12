from datetime import datetime
from typing import Any, Optional

from pydantic import Field, field_validator
from sqlmodel import SQLModel

from app.notifications.enums import (
    NotificationProvider,
    NotificationSeverity,
    NotificationStatus,
)


def _validate_text(value: str, field_name: str) -> str:
    """
    Validate notification text fields.

    Security goals:
    - Reject empty/whitespace-only values.
    - Reject control characters.
    - Normalize surrounding whitespace.
    """
    value = value.strip()

    if not value:
        raise ValueError(
            f"{field_name} must not be empty."
        )

    # Reject ASCII control characters except normal
    # horizontal tab, newline and carriage return.
    for char in value:
        if ord(char) < 32 and char not in "\t\n\r":
            raise ValueError(
                f"{field_name} contains invalid control characters."
            )

    return value


class NotificationBase(SQLModel):
    """Base notification schema."""

    provider: NotificationProvider
    severity: NotificationSeverity

    subject: str = Field(
        min_length=1,
        max_length=255,
    )

    message: str = Field(
        min_length=1,
        max_length=10_000,
    )

    metadata_json: dict[str, Any] = Field(
        default_factory=dict,
    )

    @field_validator("subject")
    @classmethod
    def validate_subject(cls, value: str) -> str:
        return _validate_text(value, "Subject")

    @field_validator("message")
    @classmethod
    def validate_message(cls, value: str) -> str:
        return _validate_text(value, "Message")


class NotificationCreate(NotificationBase):
    """Schema for creating a notification."""

    user_id: Optional[int] = Field(
        default=None,
        gt=0,
    )


class NotificationRead(NotificationBase):
    """Schema returned to API clients."""

    id: int
    user_id: Optional[int]

    status: NotificationStatus

    retry_count: int

    error_message: Optional[str]

    created_at: datetime

    sent_at: Optional[datetime]

    is_read: bool
    read_at: Optional[datetime]

    is_archived: bool
    archived_at: Optional[datetime]