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

def test_persisted_unified_analytics_are_normalized():
    result = (
        AnalyticsValidationService.build_dashboard(
            investigation_id=2701,
            analytics={
                "execution": {
                    "total_executions": 11,
                    "successful_executions": 7,
                    "failed_executions": 0,
                    "total_duration_ms": 0.04,
                    "retry_count": 2,
                    "agent_execution_counts": {
                        "memory": 1,
                        "orchestrator": 3,
                        "investigator": 3,
                        "reasoner": 3,
                        "validator": 1,
                    },
                    "slowest_agent": "orchestrator",
                    "slowest_agent_duration_ms": 0.02,
                },
                "agent_performance": {
                    "memory": {
                        "execution_count": 1,
                        "success_count": 1,
                        "failure_count": 0,
                        "total_duration_ms": 0.0,
                        "average_duration_ms": 0.0,
                        "failure_rate": 0.0,
                    },
                    "orchestrator": {
                        "execution_count": 3,
                        "success_count": 3,
                        "failure_count": 0,
                        "total_duration_ms": 0.04,
                        "average_duration_ms": 0.01,
                        "failure_rate": 0.0,
                    },
                    "investigator": {
                        "execution_count": 3,
                        "success_count": 3,
                        "failure_count": 0,
                        "total_duration_ms": 0.0,
                        "average_duration_ms": 0.0,
                        "failure_rate": 0.0,
                    },
                    "reasoner": {
                        "execution_count": 3,
                        "success_count": 0,
                        "failure_count": 0,
                        "total_duration_ms": 0.0,
                        "average_duration_ms": 0.0,
                        "failure_rate": 0.0,
                    },
                    "validator": {
                        "execution_count": 1,
                        "success_count": 0,
                        "failure_count": 0,
                        "total_duration_ms": 0.0,
                        "average_duration_ms": 0.0,
                        "failure_rate": 0.0,
                    },
                },
                "failure_retry": {
                    "total_failures": 0,
                    "total_retries": 2,
                    "failures_by_agent": {},
                    "retries_by_agent": {
                        "investigator": 2,
                    },
                },
                "bottlenecks": [
                    {
                        "agent": "orchestrator",
                        "average_duration_ms": 0.01,
                        "overall_average_duration_ms": 0.0,
                        "slowdown_ratio": 2.5,
                    }
                ],
                "efficiency": {
                    "score": 69.55,
                    "rating": "FAIR",
                    "success_rate": 0.6364,
                    "failure_rate": 0.0,
                    "retry_rate": 0.1818,
                    "bottleneck_count": 1,
                },
                "critical_path": {
                    "critical_path_ms": 125.50,
                    "executions": [
                        "execution-root",
                        "execution-child",
                    ],
                },
            },
        )
    )

    overview = result.overview

    assert overview.total_executions == 11
    assert overview.successful_executions == 7
    assert overview.failed_executions == 0
    assert overview.total_duration_ms == 0.04
    assert overview.average_duration_ms == (
        0.04 / 11
    )
    assert overview.retry_count == 2
    assert overview.success_rate == 0.6364
    assert overview.failure_rate == 0.0
    assert overview.efficiency_score == 69.55
    assert overview.slowest_agent == "orchestrator"
    assert overview.bottleneck_count == 1
    assert overview.total_agents == 5

    assert len(result.agent_performance) == 5

    orchestrator = next(
        agent
        for agent in result.agent_performance
        if agent.agent == "orchestrator"
    )

    assert orchestrator.executions == 3
    assert orchestrator.successful_executions == 3
    assert orchestrator.failed_executions == 0
    assert orchestrator.average_duration_ms == 0.01

    assert result.failure_retry_metrics.total_failures == 0
    assert result.failure_retry_metrics.total_retries == 2
    assert result.failure_retry_metrics.retry_by_agent[
        "investigator"
    ] == 2

    assert len(result.bottlenecks) == 1

    bottleneck = result.bottlenecks[0]

    assert bottleneck.agent == "orchestrator"
    assert bottleneck.execution_count == 3
    assert bottleneck.is_bottleneck is True
    assert result.critical_path.critical_path_ms == 125.50
    assert result.critical_path.executions == [
        "execution-root",
        "execution-child",
    ]

def test_invalid_critical_path_is_normalized():
    result = (
        AnalyticsValidationService.build_dashboard(
            investigation_id=7,
            analytics={
                "critical_path": {
                    "critical_path_ms": -500,
                    "executions": "invalid",
                }
            },
        )
    )

    assert result.critical_path.critical_path_ms == 0.0
    assert result.critical_path.executions == []