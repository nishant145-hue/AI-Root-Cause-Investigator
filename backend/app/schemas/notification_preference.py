from datetime import datetime

from sqlmodel import SQLModel


class NotificationPreferenceBase(SQLModel):
    """Base notification preference schema."""

    email_enabled: bool = True
    slack_enabled: bool = False
    teams_enabled: bool = False
    critical_only: bool = False
    daily_digest: bool = False
    weekly_digest: bool = False


class NotificationPreferenceCreate(NotificationPreferenceBase):
    """Schema for creating notification preferences."""

    user_id: int


class NotificationPreferenceUpdate(SQLModel):
    """Schema for updating notification preferences."""

    email_enabled: bool | None = None
    slack_enabled: bool | None = None
    teams_enabled: bool | None = None
    critical_only: bool | None = None
    daily_digest: bool | None = None
    weekly_digest: bool | None = None


class NotificationPreferenceRead(NotificationPreferenceBase):
    """Schema returned to API clients."""

    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime