from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class DashboardOverview(BaseModel):
    """Dashboard summary response."""

    total_investigations: int

    critical: int
    high: int
    medium: int
    low: int

    resolved: int
    pending: int

    average_confidence: float
    average_duration_seconds: float

    model_config = ConfigDict(from_attributes=True)
    
class RecentInvestigation(BaseModel):
    """Recent investigation shown on dashboard."""

    id: int
    title: str
    status: str
    severity: str | None = None
    confidence: float | None = None
    root_cause: str | None = None
    failed_component: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
    
class TimelinePoint(BaseModel):
    """Timeline analytics point."""

    date: date
    count: int

    model_config = ConfigDict(from_attributes=True)
    
class SeverityAnalytics(BaseModel):
    """Severity distribution."""

    severity: str | None
    count: int

    model_config = ConfigDict(from_attributes=True)
    
class RootCauseAnalytics(BaseModel):
    """Root cause distribution."""

    root_cause: str
    count: int

    model_config = ConfigDict(from_attributes=True)
    
class FailedComponentAnalytics(BaseModel):
    """Failed component distribution."""

    component: str
    count: int

    model_config = ConfigDict(from_attributes=True)
    
class ConfidenceAnalytics(BaseModel):
    """AI confidence statistics."""

    average_confidence: float
    minimum_confidence: float
    maximum_confidence: float

    high_confidence: int
    medium_confidence: int
    low_confidence: int

    model_config = ConfigDict(from_attributes=True)