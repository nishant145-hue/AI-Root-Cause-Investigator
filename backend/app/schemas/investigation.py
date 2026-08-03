from datetime import datetime
from typing import Optional

from pydantic import ConfigDict, Field, field_validator
from sqlmodel import SQLModel

from app.models.investigation import InvestigationStatus


class InvestigationCreate(SQLModel):
    title: str = Field(
        min_length=3,
        max_length=255,
        description="Investigation title",
    )

    description: Optional[str] = Field(
        default=None,
        max_length=5000,
    )

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError(
                "Title cannot be empty."
            )

        return value


class InvestigationUpdate(SQLModel):
    title: Optional[str] = Field(
        default=None,
        min_length=3,
        max_length=255,
    )

    description: Optional[str] = Field(
        default=None,
        max_length=5000,
    )

    status: Optional[InvestigationStatus] = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value

        value = value.strip()

        if not value:
            raise ValueError(
                "Title cannot be empty."
            )

        return value


class InvestigationRead(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: Optional[str]
    status: InvestigationStatus
    user_id: int
    created_at: datetime
    updated_at: datetime
    
class InvestigationList(SQLModel):
    items: list[InvestigationRead]

    total: int

    skip: int

    limit: int

    has_next: bool