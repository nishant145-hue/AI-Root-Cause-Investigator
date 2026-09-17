from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    """Return the current UTC datetime."""
    return datetime.now(timezone.utc)


class ReportHistory(SQLModel, table=True):
    """Stores successfully generated report records."""

    __tablename__ = "report_history"

    id: Optional[int] = Field(
        default=None,
        primary_key=True,
    )

    user_id: int = Field(
        foreign_key="users.id",
        index=True,
    )

    investigation_id: Optional[int] = Field(
        default=None,
        foreign_key="investigations.id",
        index=True,
    )

    report_type: str = Field(
        index=True,
    )

    format: str = Field(
        index=True,
    )

    filename: str

    status: str = Field(
        default="COMPLETED",
        index=True,
    )

    created_at: datetime = Field(
        default_factory=utc_now,
        index=True,
    )
