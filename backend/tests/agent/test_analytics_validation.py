from app.services.analytics_validation_service import (
    AnalyticsValidationService,
)


def test_empty_analytics_is_safe():
    result = (
        AnalyticsValidationService.build_dashboard(
            investigation_id=1,
            analytics={},
        )
    )

    assert result.investigation_id == 1
    assert result.overview.total_executions == 0
    assert result.overview.efficiency_score == 0.0
    assert result.agent_performance == []
    assert result.bottlenecks == []
    assert result.timeline == []


def test_invalid_container_types_are_normalized():
    result = (
        AnalyticsValidationService.build_dashboard(
            investigation_id=2,
            analytics={
                "overview": None,
                "agent_performance": "invalid",
                "bottlenecks": None,
                "failure_retry_metrics": None,
                "timeline": "invalid",
            },
        )
    )

    assert result.overview.total_executions == 0
    assert result.agent_performance == []
    assert result.bottlenecks == []
    assert result.timeline == []


def test_legacy_agent_metric_names_are_supported():
    result = (
        AnalyticsValidationService.build_dashboard(
            investigation_id=3,
            analytics={
                "agent_performance": [
                    {
                        "agent": "investigator",
                        "execution_count": 5,
                        "success_count": 4,
                        "failure_count": 1,
                        "total_duration_ms": 5000,
                        "average_duration_ms": 1000,
                        "failure_rate": 0.2,
                    }
                ]
            },
        )
    )

    agent = result.agent_performance[0]

    assert agent.agent == "investigator"
    assert agent.executions == 5
    assert agent.successful_executions == 4
    assert agent.failed_executions == 1


def test_legacy_failure_retry_names_are_supported():
    result = (
        AnalyticsValidationService.build_dashboard(
            investigation_id=4,
            analytics={
                "failure_retry": {
                    "total_failures": 2,
                    "total_retries": 3,
                    "failures_by_agent": {
                        "investigator": 2,
                    },
                    "retries_by_agent": {
                        "investigator": 3,
                    },
                }
            },
        )
    )

    metrics = result.failure_retry_metrics

    assert metrics.total_failures == 2
    assert metrics.total_retries == 3
    assert metrics.failed_agents[
        "investigator"
    ] == 2
    assert metrics.retry_by_agent[
        "investigator"
    ] == 3


def test_negative_metrics_are_clamped():
    result = (
        AnalyticsValidationService.build_dashboard(
            investigation_id=5,
            analytics={
                "overview": {
                    "total_executions": -10,
                    "failed_executions": -5,
                    "retry_count": -2,
                    "efficiency_score": 500,
                    "success_rate": -1,
                }
            },
        )
    )

    overview = result.overview

    assert overview.total_executions == 0
    assert overview.failed_executions == 0
    assert overview.retry_count == 0
    assert overview.efficiency_score == 100
    assert overview.success_rate == 0


def test_invalid_timeline_entries_are_ignored():
    result = (
        AnalyticsValidationService.build_dashboard(
            investigation_id=6,
            analytics={
                "timeline": [
                    None,
                    "invalid",
                    {
                        "agent": "investigator",
                        "status": "COMPLETED",
                        "duration_ms": "invalid",
                    },
                ]
            },
        )
    )

    assert len(result.timeline) == 1

    entry = result.timeline[0]

    assert entry.agent == "investigator"
    assert entry.status == "COMPLETED"
    assert entry.duration_ms is None
