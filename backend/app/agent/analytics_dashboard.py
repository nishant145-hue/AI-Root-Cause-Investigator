from typing import Any

from app.agent.execution_analytics import (
    InvestigationExecutionAnalytics,
)

from app.schemas.analytics import (
    AgentPerformanceRead,
    AnalyticsOverview,
    BottleneckRead,
    ExecutionTimelineEntryRead,
    FailureRetryMetricsRead,
    InvestigationAnalyticsDashboardRead,
)


def build_analytics_dashboard(
    investigation_id: int,
    timeline: list[dict[str, Any]] | None = None,
) -> InvestigationAnalyticsDashboardRead:
    """
    Build a dashboard-ready analytics response from
    the investigation execution timeline.

    This function is read-only and does not modify
    the supplied timeline.
    """

    # ---------------------------------------------------------
    # Analytics engine
    # ---------------------------------------------------------

    analytics = InvestigationExecutionAnalytics(
        timeline=timeline or []
    )

    unified = analytics.unified_summary()

    # ---------------------------------------------------------
    # Extract execution metrics safely
    # ---------------------------------------------------------

    execution = unified.get(
        "execution",
        {},
    )

    total_executions = int(
        execution.get(
            "total_executions",
            0,
        )
        or 0
    )

    successful_executions = int(
        execution.get(
            "successful_executions",
            0,
        )
        or 0
    )

    failed_executions = int(
        execution.get(
            "failed_executions",
            0,
        )
        or 0
    )

    total_duration_ms = float(
        execution.get(
            "total_duration_ms",
            0.0,
        )
        or 0.0
    )

    retry_count = int(
        execution.get(
            "retry_count",
            0,
        )
        or 0
    )

    # ---------------------------------------------------------
    # Derived reporting metrics
    # ---------------------------------------------------------

    average_duration_ms = (
        total_duration_ms / total_executions
        if total_executions > 0
        else 0.0
    )

    success_rate = (
        successful_executions
        / total_executions
        if total_executions > 0
        else 0.0
    )

    failure_rate = (
        failed_executions
        / total_executions
        if total_executions > 0
        else 0.0
    )

    # Keep percentages in the expected ranges.
    success_rate = max(
        0.0,
        min(1.0, success_rate),
    )

    failure_rate = max(
        0.0,
        min(1.0, failure_rate),
    )

    # ---------------------------------------------------------
    # Efficiency
    # ---------------------------------------------------------

    efficiency = unified.get(
        "efficiency",
        {},
    )

    efficiency_score = float(
        efficiency.get(
            "score",
            0.0,
        )
        or 0.0
    )

    # AnalyticsOverview requires 0-100.
    efficiency_score = max(
        0.0,
        min(100.0, efficiency_score),
    )

    # ---------------------------------------------------------
    # Agent performance source
    # ---------------------------------------------------------

    agent_metrics = unified.get(
        "agent_performance",
        {},
    )

    # ---------------------------------------------------------
    # Slowest agent
    # ---------------------------------------------------------

    slowest_agent = analytics.slowest_agent()

    # ---------------------------------------------------------
    # Bottleneck source
    # ---------------------------------------------------------

    bottleneck_items = unified.get(
        "bottlenecks",
        [],
    )

    # ---------------------------------------------------------
    # Overview
    # ---------------------------------------------------------

    overview = AnalyticsOverview(
        total_executions=total_executions,

        successful_executions=(
            successful_executions
        ),

        failed_executions=(
            failed_executions
        ),

        total_duration_ms=(
            total_duration_ms
        ),

        average_duration_ms=(
            average_duration_ms
        ),

        retry_count=retry_count,

        success_rate=success_rate,

        failure_rate=failure_rate,

        efficiency_score=(
            efficiency_score
        ),

        slowest_agent=slowest_agent,

        bottleneck_count=len(
            bottleneck_items
        ),

        total_agents=len(
            agent_metrics
        ),
    )

    # ---------------------------------------------------------
    # Agent performance
    # ---------------------------------------------------------

    agent_performance = []

    for agent, metrics in agent_metrics.items():

        execution_count = int(
            metrics.get(
                "execution_count",
                0,
            )
            or 0
        )

        success_count = int(
            metrics.get(
                "success_count",
                0,
            )
            or 0
        )

        failure_count = int(
            metrics.get(
                "failure_count",
                0,
            )
            or 0
        )

        agent_total_duration = float(
            metrics.get(
                "total_duration_ms",
                0.0,
            )
            or 0.0
        )

        agent_average_duration = float(
            metrics.get(
                "average_duration_ms",
                0.0,
            )
            or 0.0
        )

        agent_failure_rate = float(
            metrics.get(
                "failure_rate",
                0.0,
            )
            or 0.0
        )

        # Keep failure rate valid.
        agent_failure_rate = max(
            0.0,
            min(
                1.0,
                agent_failure_rate,
            ),
        )

        agent_performance.append(
            AgentPerformanceRead(
                agent=str(agent),

                executions=execution_count,

                successful_executions=(
                    success_count
                ),

                failed_executions=(
                    failure_count
                ),

                total_duration_ms=(
                    agent_total_duration
                ),

                average_duration_ms=(
                    agent_average_duration
                ),

                failure_rate=(
                    agent_failure_rate
                ),
            )
        )

    # ---------------------------------------------------------
    # Bottlenecks
    # ---------------------------------------------------------

    bottlenecks = []

    for item in bottleneck_items:

        if not isinstance(item, dict):
            continue

        agent = item.get(
            "agent",
            "",
        )

        average_duration = float(
            item.get(
                "average_duration_ms",
                0.0,
            )
            or 0.0
        )

        overall_average = float(
            item.get(
                "overall_average_duration_ms",
                0.0,
            )
            or 0.0
        )

        agent_data = agent_metrics.get(
            agent,
            {},
        )

        execution_count = int(
            agent_data.get(
                "execution_count",
                0,
            )
            or 0
        )

        # Existing analytics uses 1.5x overall average
        # as the default bottleneck threshold.
        threshold_ms = (
            overall_average * 1.5
        )

        bottlenecks.append(
            BottleneckRead(
                agent=str(agent),

                average_duration_ms=(
                    average_duration
                ),

                execution_count=(
                    execution_count
                ),

                threshold_ms=(
                    threshold_ms
                ),

                is_bottleneck=True,
            )
        )

    # ---------------------------------------------------------
    # Failure / retry metrics
    # ---------------------------------------------------------

    failure_retry = unified.get(
        "failure_retry",
        {},
    )

    total_failures = int(
        failure_retry.get(
            "total_failures",
            0,
        )
        or 0
    )

    total_retries = int(
        failure_retry.get(
            "total_retries",
            0,
        )
        or 0
    )

    failed_agents = dict(
        failure_retry.get(
            "failures_by_agent",
            {},
        )
        or {}
    )

    retry_by_agent = dict(
        failure_retry.get(
            "retries_by_agent",
            {},
        )
        or {}
    )

    failure_retry_metrics = (
        FailureRetryMetricsRead(
            total_failures=(
                total_failures
            ),

            total_retries=(
                total_retries
            ),

            failed_agents=(
                failed_agents
            ),

            retry_by_agent=(
                retry_by_agent
            ),
        )
    )

    # ---------------------------------------------------------
    # Timeline
    # ---------------------------------------------------------

    timeline_entries = []

    for trace in analytics.timeline:

        if not isinstance(trace, dict):
            continue

        started_at = trace.get(
            "started_at"
        )

        completed_at = trace.get(
            "completed_at"
        )

        duration_ms = trace.get(
            "duration_ms"
        )

        metadata = trace.get(
            "metadata",
            {},
        )

        if not isinstance(
            metadata,
            dict,
        ):
            metadata = {}

        timeline_entries.append(
            ExecutionTimelineEntryRead(
                agent=trace.get(
                    "agent"
                ),

                action=trace.get(
                    "action"
                ),

                status=trace.get(
                    "status"
                ),

                started_at=(
                    str(started_at)
                    if started_at is not None
                    else None
                ),

                completed_at=(
                    str(completed_at)
                    if completed_at is not None
                    else None
                ),

                duration_ms=(
                    float(duration_ms)
                    if duration_ms is not None
                    else None
                ),

                metadata=dict(
                    metadata
                ),
            )
        )

    # ---------------------------------------------------------
    # Final dashboard response
    # ---------------------------------------------------------

    return InvestigationAnalyticsDashboardRead(
        investigation_id=investigation_id,

        overview=overview,

        agent_performance=(
            agent_performance
        ),

        bottlenecks=bottlenecks,

        failure_retry_metrics=(
            failure_retry_metrics
        ),

        timeline=timeline_entries,
    )
