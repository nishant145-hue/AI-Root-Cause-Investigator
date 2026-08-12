from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    """Return the current UTC datetime."""
    return datetime.now(timezone.utc)


class NotificationPreference(SQLModel, table=True):
    """Stores user notification preferences."""

    __tablename__ = "notification_preferences"

    id: Optional[int] = Field(default=None, primary_key=True)

    user_id: int = Field(
        foreign_key="users.id",
        unique=True,
        index=True,
    )

    email_enabled: bool = Field(default=True)

    slack_enabled: bool = Field(default=False)

    teams_enabled: bool = Field(default=False)

    critical_only: bool = Field(default=False)

    daily_digest: bool = Field(default=False)

    weekly_digest: bool = Field(default=False)

    created_at: datetime = Field(
        default_factory=utc_now,
    )

    updated_at: datetime = Field(
        default_factory=utc_now,
    )