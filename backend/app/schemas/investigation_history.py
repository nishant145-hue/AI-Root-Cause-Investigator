from datetime import datetime

from pydantic import ConfigDict
from sqlmodel import SQLModel

from app.models.investigation_history import (
    InvestigationAction,
)


class InvestigationHistoryCreate(SQLModel):
    investigation_id: int
    user_id: int

    action: InvestigationAction

    old_value: str | None = None
    new_value: str | None = None


class InvestigationHistoryRead(SQLModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int

    investigation_id: int

    user_id: int

    action: InvestigationAction

    old_value: str | None = None
    new_value: str | None = None

    created_at: datetime


class InvestigationHistoryList(SQLModel):
    items: list[InvestigationHistoryRead]

    total: int