from pydantic import BaseModel, Field
from typing import List, Optional


class Recommendation(BaseModel):
    """A single recommendation suggested by the AI."""

    title: str = Field(..., description="Short recommendation title")
    description: str = Field(..., description="Detailed recommendation")


class Evidence(BaseModel):
    """Evidence extracted from logs."""

    log_line: str = Field(..., description="Relevant log line")
    reason: str = Field(..., description="Why this line is important")


class AIInvestigationResponse(BaseModel):
    """Structured AI investigation response."""

    summary: str = Field(
        ...,
        description="Short summary of the investigation"
    )

    root_cause: str = Field(
        ...,
        description="Most likely root cause"
    )

    failed_component: str = Field(
        ...,
        description="Component responsible for the failure"
    )

    severity: str = Field(
        ...,
        description="Critical, High, Medium, Low"
    )

    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="AI confidence score between 0 and 1"
    )

    evidence: List[Evidence] = Field(
        default_factory=list,
        description="Supporting evidence from logs"
    )

    recommendations: List[Recommendation] = Field(
        default_factory=list,
        description="Suggested fixes"
    )

    additional_notes: Optional[str] = Field(
        default=None,
        description="Extra observations from the AI"
    )