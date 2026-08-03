from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.user import User


class InvestigationStatus(str, Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Investigation(SQLModel, table=True):
    __tablename__ = "investigations"

    id: int | None = Field(default=None, primary_key=True)

    title: str = Field(index=True, max_length=255)

    description: Optional[str] = Field(default=None)

    status: InvestigationStatus = Field(
        default=InvestigationStatus.OPEN
    )

    user_id: int = Field(foreign_key="users.id")

    created_at: datetime = Field(default_factory=datetime.utcnow)

    updated_at: datetime = Field(default_factory=datetime.utcnow)

    user: "User" = Relationship(back_populates="investigations")