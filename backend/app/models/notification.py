from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import Column, JSON
from sqlmodel import Field, SQLModel

from app.notifications.enums import (
    NotificationProvider,
    NotificationSeverity,
    NotificationStatus,
)


def utc_now() -> datetime:
    """Return the current UTC datetime."""
    return datetime.now(timezone.utc)


class Notification(SQLModel, table=True):
    """Stores notifications and their delivery status."""

    __tablename__ = "notifications"

    id: Optional[int] = Field(default=None, primary_key=True)

    user_id: Optional[int] = Field(
        default=None,
        foreign_key="users.id",
        index=True,
    )

    provider: NotificationProvider = Field(
        default=NotificationProvider.EMAIL,
        index=True,
    )

    severity: NotificationSeverity = Field(
        default=NotificationSeverity.INFO,
        index=True,
    )

    status: NotificationStatus = Field(
        default=NotificationStatus.PENDING,
        index=True,
    )

    subject: str
    message: str

    retry_count: int = Field(default=0)

    error_message: Optional[str] = None

    metadata_json: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column("metadata", JSON),
    )

    created_at: datetime = Field(
        default_factory=utc_now,
        index=True,
    )

    sent_at: Optional[datetime] = None
    is_read: bool = Field(
        default=False,
        index=True,
    )

    read_at: Optional[datetime] = None
    
    is_archived: bool = Field(
        default=False,
        index=True,
    )

    archived_at: Optional[datetime] = None