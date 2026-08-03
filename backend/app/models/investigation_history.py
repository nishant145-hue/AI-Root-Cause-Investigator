from datetime import datetime
from enum import Enum
from typing import Optional

from sqlmodel import Field, SQLModel


class InvestigationAction(str, Enum):
    CREATED = "CREATED"
    UPDATED = "UPDATED"
    STATUS_CHANGED = "STATUS_CHANGED"
    DELETED = "DELETED"


class InvestigationHistory(SQLModel, table=True):
    __tablename__ = "investigation_history"

    id: int | None = Field(default=None, primary_key=True)

    investigation_id: int = Field(
        foreign_key="investigations.id",
        index=True,
    )

    user_id: int = Field(
        foreign_key="users.id",
        index=True,
    )

    action: InvestigationAction

    old_value: Optional[str] = None

    new_value: Optional[str] = None

    created_at: datetime = Field(
        default_factory=datetime.utcnow
    )