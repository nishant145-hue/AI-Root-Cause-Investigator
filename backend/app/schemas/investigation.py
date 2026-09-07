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
    summary: str | None = None
    root_cause: str | None = None
    failed_component: str | None = None
    severity: str | None = None
    confidence: float | None = None
    additional_notes: str | None = None

class InvestigationList(SQLModel):
    items: list[InvestigationRead]

    total: int

    skip: int

    limit: int

    has_next: bool

class RunAIInvestigationRequest(SQLModel):
    """
    Request body for running an AI investigation.

    Security:
    - log_file_id must be a positive database identifier.
    - Ownership/existence is still checked by the service layer.
    """

    log_file_id: int = Field(
        gt=0,
        description="ID of the uploaded log file to investigate.",
    )

class InvestigationAnalyticsRead(SQLModel):
    investigation_id: int
    analytics: dict
