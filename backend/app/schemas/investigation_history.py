from datetime import datetime
from typing import Optional

from pydantic import ConfigDict
from sqlmodel import SQLModel

from app.models.investigation_history import InvestigationAction


class InvestigationHistoryBase(SQLModel):
    """Base schema for investigation history."""

    action: InvestigationAction
    old_value: Optional[str] = None
    new_value: Optional[str] = None


class InvestigationHistoryCreate(InvestigationHistoryBase):
    """Schema used when creating a history record."""

    investigation_id: int
    user_id: int


class InvestigationHistoryRead(InvestigationHistoryBase):
    """Schema returned in API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    investigation_id: int
    user_id: int
    created_at: datetime


class InvestigationHistoryList(SQLModel):
    """Schema for returning a list of history records."""

    items: list[InvestigationHistoryRead]
    total: int