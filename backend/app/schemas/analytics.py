from typing import Any

from pydantic import BaseModel, Field


class AnalyticsOverview(BaseModel):
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0

    total_duration_ms: float = 0.0
    average_duration_ms: float = 0.0

    retry_count: int = 0

    success_rate: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
    )

    failure_rate: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
    )

    efficiency_score: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
    )

    slowest_agent: str | None = None

    bottleneck_count: int = 0

    total_agents: int = 0

class AgentPerformanceRead(BaseModel):
    agent: str

    executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0

    total_duration_ms: float = 0.0
    average_duration_ms: float = 0.0

    failure_rate: float = 0.0


class BottleneckRead(BaseModel):
    agent: str

    average_duration_ms: float = 0.0
    execution_count: int = 0

    threshold_ms: float = 0.0

    is_bottleneck: bool = False


class FailureRetryMetricsRead(BaseModel):
    total_failures: int = 0
    total_retries: int = 0

    failed_agents: dict[str, int] = Field(
        default_factory=dict
    )

    retry_by_agent: dict[str, int] = Field(
        default_factory=dict
    )


class ExecutionTimelineEntryRead(BaseModel):
    agent: str | None = None
    action: str | None = None
    status: str | None = None

    started_at: str | None = None
    completed_at: str | None = None

    duration_ms: float | None = None

    metadata: dict[str, Any] = Field(
        default_factory=dict
    )


class InvestigationAnalyticsDashboardRead(BaseModel):
    investigation_id: int

    overview: AnalyticsOverview

    agent_performance: list[
        AgentPerformanceRead
    ] = Field(default_factory=list)

    bottlenecks: list[
        BottleneckRead
    ] = Field(default_factory=list)

    failure_retry_metrics: (
        FailureRetryMetricsRead
    )

    timeline: list[
        ExecutionTimelineEntryRead
    ] = Field(default_factory=list)
