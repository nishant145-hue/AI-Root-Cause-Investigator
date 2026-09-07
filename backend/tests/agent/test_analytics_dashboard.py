from app.agent.analytics_dashboard import (
    build_analytics_dashboard,
)


def test_dashboard_analytics_empty():

    result = build_analytics_dashboard(
        investigation_id=1,
        timeline=[],
    )

    assert result.investigation_id == 1

    assert (
        result.overview.total_executions
        == 0
    )

    assert (
        result.overview.successful_executions
        == 0
    )

    assert (
        result.overview.failed_executions
        == 0
    )

    assert (
        result.overview.efficiency_score
        == 0.0
    )

    assert result.agent_performance == []

    assert result.bottlenecks == []

    assert result.timeline == []


def test_dashboard_analytics_builds_overview():

    timeline = [
        {
            "agent": "investigator",
            "action": "search_logs",
            "status": "COMPLETED",
            "duration_ms": 100.0,
            "attempt": 1,
        },
        {
            "agent": "reasoner",
            "action": "generate_hypothesis",
            "status": "COMPLETED",
            "duration_ms": 200.0,
            "attempt": 1,
        },
        {
            "agent": "validator",
            "action": "validate",
            "status": "FAILED",
            "duration_ms": 50.0,
            "attempt": 2,
        },
    ]

    result = build_analytics_dashboard(
        investigation_id=10,
        timeline=timeline,
    )

    assert result.investigation_id == 10

    assert (
        result.overview.total_executions
        == 3
    )

    assert (
        result.overview.successful_executions
        == 2
    )

    assert (
        result.overview.failed_executions
        == 1
    )

    assert (
        result.overview.total_duration_ms
        == 350.0
    )

    assert (
        result.overview.retry_count
        == 1
    )

    assert (
        result.overview.efficiency_score
        >= 0
    )

    assert len(
        result.agent_performance
    ) == 3

    assert len(result.timeline) == 3


def test_dashboard_agent_performance():

    timeline = [
        {
            "agent": "investigator",
            "status": "COMPLETED",
            "duration_ms": 100,
        },
        {
            "agent": "investigator",
            "status": "FAILED",
            "duration_ms": 300,
        },
    ]

    result = build_analytics_dashboard(
        investigation_id=1,
        timeline=timeline,
    )

    investigator = next(
        item
        for item in result.agent_performance
        if item.agent == "investigator"
    )

    assert investigator.executions == 2

    assert (
        investigator.successful_executions
        == 1
    )

    assert (
        investigator.failed_executions
        == 1
    )

    assert (
        investigator.total_duration_ms
        == 400
    )

    assert (
        investigator.average_duration_ms
        == 200
    )

    assert (
        investigator.failure_rate
        == 0.5
    )


def test_dashboard_failure_retry_metrics():

    timeline = [
        {
            "agent": "investigator",
            "status": "FAILED",
            "duration_ms": 100,
            "attempt": 1,
        },
        {
            "agent": "investigator",
            "status": "COMPLETED",
            "duration_ms": 120,
            "attempt": 2,
        },
    ]

    result = build_analytics_dashboard(
        investigation_id=1,
        timeline=timeline,
    )

    assert (
        result.failure_retry_metrics
        .total_failures
        == 1
    )

    assert (
        result.failure_retry_metrics
        .total_retries
        == 1
    )

    assert (
        result.failure_retry_metrics
        .failed_agents[
            "investigator"
        ]
        == 1
    )

    assert (
        result.failure_retry_metrics
        .retry_by_agent[
            "investigator"
        ]
        == 1
    )

def test_dashboard_reporting_metrics():

    timeline = [
        {
            "agent": "investigator",
            "status": "COMPLETED",
            "duration_ms": 100.0,
            "attempt": 1,
        },
        {
            "agent": "reasoner",
            "status": "COMPLETED",
            "duration_ms": 300.0,
            "attempt": 1,
        },
        {
            "agent": "validator",
            "status": "FAILED",
            "duration_ms": 100.0,
            "attempt": 1,
        },
        {
            "agent": "validator",
            "status": "COMPLETED",
            "duration_ms": 150.0,
            "attempt": 2,
        },
    ]

    result = build_analytics_dashboard(
        investigation_id=100,
        timeline=timeline,
    )

    overview = result.overview

    assert overview.total_executions == 4

    assert overview.successful_executions == 3

    assert overview.failed_executions == 1

    assert overview.total_duration_ms == 650.0

    assert overview.average_duration_ms == 162.5

    assert overview.retry_count == 1

    assert overview.success_rate == 0.75

    assert overview.failure_rate == 0.25

    assert overview.efficiency_score >= 0

    assert overview.total_agents == 3

    assert overview.slowest_agent == "reasoner"

    assert overview.bottleneck_count >= 0

def test_dashboard_reporting_metrics_empty():

    result = build_analytics_dashboard(
        investigation_id=101,
        timeline=[],
    )

    overview = result.overview

    assert overview.total_executions == 0

    assert overview.average_duration_ms == 0.0

    assert overview.success_rate == 0.0

    assert overview.failure_rate == 0.0

    assert overview.slowest_agent is None

    assert overview.bottleneck_count == 0

    assert overview.total_agents == 0
