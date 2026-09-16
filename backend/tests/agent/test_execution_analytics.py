from app.agent.execution_analytics import (
    InvestigationExecutionAnalytics,
)


def test_execution_metrics():

    timeline = [
        {
            "agent": "planner",
            "status": "COMPLETED",
            "duration_ms": 100.0,
            "attempt": 1,
        },
        {
            "agent": "investigator",
            "status": "COMPLETED",
            "duration_ms": 300.0,
            "attempt": 1,
        },
        {
            "agent": "reasoner",
            "status": "COMPLETED",
            "duration_ms": 500.0,
            "attempt": 1,
        },
    ]

    analytics = (
        InvestigationExecutionAnalytics(
            timeline
        )
    )

    assert (
        analytics.total_executions()
        == 3
    )

    assert (
        analytics.successful_executions()
        == 3
    )

    assert (
        analytics.failed_executions()
        == 0
    )

    assert (
        analytics.total_duration_ms()
        == 900.0
    )


def test_failed_execution_metrics():

    timeline = [
        {
            "agent": "investigator",
            "status": "FAILED",
            "duration_ms": 200.0,
            "attempt": 1,
        },
        {
            "agent": "investigator",
            "status": "COMPLETED",
            "duration_ms": 300.0,
            "attempt": 2,
        },
    ]

    analytics = (
        InvestigationExecutionAnalytics(
            timeline
        )
    )

    assert (
        analytics.failed_executions()
        == 1
    )

    assert (
        analytics.successful_executions()
        == 1
    )

    assert (
        analytics.retry_count()
        == 1
    )


def test_agent_execution_counts():

    timeline = [
        {
            "agent": "investigator",
            "status": "COMPLETED",
            "duration_ms": 100.0,
        },
        {
            "agent": "investigator",
            "status": "COMPLETED",
            "duration_ms": 200.0,
        },
        {
            "agent": "reasoner",
            "status": "COMPLETED",
            "duration_ms": 500.0,
        },
    ]

    analytics = (
        InvestigationExecutionAnalytics(
            timeline
        )
    )

    assert (
        analytics.agent_execution_counts()
        == {
            "investigator": 2,
            "reasoner": 1,
        }
    )


def test_slowest_agent():

    timeline = [
        {
            "agent": "planner",
            "status": "COMPLETED",
            "duration_ms": 100.0,
        },
        {
            "agent": "reasoner",
            "status": "COMPLETED",
            "duration_ms": 750.0,
        },
        {
            "agent": "validator",
            "status": "COMPLETED",
            "duration_ms": 250.0,
        },
    ]

    analytics = (
        InvestigationExecutionAnalytics(
            timeline
        )
    )

    assert (
        analytics.slowest_agent()
        == "reasoner"
    )

    assert (
        analytics.slowest_agent_duration_ms()
        == 750.0
    )

def test_duration_analytics_uses_real_timeline_durations():

    timeline = [
        {
            "agent": "memory",
            "status": "COMPLETED",
            "duration_ms": 13710.0,
            "attempt": 1,
        },
        {
            "agent": "orchestrator",
            "status": "COMPLETED",
            "duration_ms": 0.02,
            "attempt": 1,
        },
        {
            "agent": "investigator",
            "status": "COMPLETED",
            "duration_ms": 8.6,
            "attempt": 1,
        },
        {
            "agent": "reasoner",
            "status": "NO_EVIDENCE",
            "duration_ms": 0.01,
            "attempt": 1,
        },
        {
            "agent": "validator",
            "status": "REJECTED",
            "duration_ms": 0.02,
            "attempt": 1,
        },
    ]

    analytics = InvestigationExecutionAnalytics(
        timeline
    )

    expected_total = (
        13710.0
        + 0.02
        + 8.6
        + 0.01
        + 0.02
    )

    assert (
        analytics.total_duration_ms()
        == round(expected_total, 2)
    )

    assert (
        analytics.slowest_agent()
        == "memory"
    )

    assert (
        analytics.slowest_agent_duration_ms()
        == 13710.0
    )

    performance = analytics.agent_performance()

    assert (
        performance["memory"]["total_duration_ms"]
        == 13710.0
    )

    assert (
        performance["investigator"]["average_duration_ms"]
        == 8.6
    )

def test_agent_performance_aggregates_real_timeline_data():

    timeline = [
        {
            "agent": "investigator",
            "action": "search_logs",
            "status": "COMPLETED",
            "duration_ms": 8.6,
            "attempt": 1,
        },
        {
            "agent": "investigator",
            "action": "search_logs",
            "status": "COMPLETED",
            "duration_ms": 3.8,
            "attempt": 2,
        },
        {
            "agent": "reasoner",
            "action": "generate_hypotheses",
            "status": "NO_EVIDENCE",
            "duration_ms": 0.03,
            "attempt": 1,
        },
        {
            "agent": "validator",
            "action": "validate_root_cause",
            "status": "REJECTED",
            "duration_ms": 0.02,
            "attempt": 1,
        },
    ]

    analytics = InvestigationExecutionAnalytics(
        timeline
    )

    performance = analytics.agent_performance()

    investigator = performance["investigator"]

    assert investigator["execution_count"] == 2

    assert (
        investigator["total_duration_ms"]
        == 12.4
    )

    assert (
        investigator["average_duration_ms"]
        == 6.2
    )

    assert (
        investigator["success_count"]
        == 2
    )

    assert (
        investigator["failure_count"]
        == 0
    )

    reasoner = performance["reasoner"]

    assert reasoner["execution_count"] == 1

    assert (
        reasoner["failure_count"]
        == 0
    )

    validator = performance["validator"]

    assert validator["execution_count"] == 1

    assert (
        validator["failure_count"]
        == 0
    )

def test_empty_timeline():

    analytics = (
        InvestigationExecutionAnalytics()
    )

    summary = analytics.summary()

    assert (
        summary["total_executions"]
        == 0
    )

    assert (
        summary["total_duration_ms"]
        == 0.0
    )

    assert (
        summary["slowest_agent"]
        is None
    )

def test_agent_performance():

    timeline = [
        {
            "agent": "investigator",
            "status": "COMPLETED",
            "duration_ms": 100.0,
        },
        {
            "agent": "investigator",
            "status": "FAILED",
            "duration_ms": 300.0,
        },
        {
            "agent": "reasoner",
            "status": "COMPLETED",
            "duration_ms": 500.0,
        },
    ]

    analytics = (
        InvestigationExecutionAnalytics(
            timeline
        )
    )

    performance = (
        analytics.agent_performance()
    )

    assert performance[
        "investigator"
    ] == {
        "execution_count": 2,
        "success_count": 1,
        "failure_count": 1,
        "total_duration_ms": 400.0,
        "average_duration_ms": 200.0,
        "failure_rate": 0.5,
    }

    assert performance[
        "reasoner"
    ] == {
        "execution_count": 1,
        "success_count": 1,
        "failure_count": 0,
        "total_duration_ms": 500.0,
        "average_duration_ms": 500.0,
        "failure_rate": 0.0,
    }


def test_agent_performance_empty():

    analytics = (
        InvestigationExecutionAnalytics()
    )

    assert (
        analytics.agent_performance()
        == {}
    )

def test_failure_retry_metrics():

    timeline = [
        {
            "agent": "investigator",
            "status": "FAILED",
            "duration_ms": 100.0,
            "attempt": 1,
        },
        {
            "agent": "investigator",
            "status": "FAILED",
            "duration_ms": 200.0,
            "attempt": 2,
        },
        {
            "agent": "investigator",
            "status": "COMPLETED",
            "duration_ms": 300.0,
            "attempt": 3,
        },
        {
            "agent": "reasoner",
            "status": "FAILED",
            "duration_ms": 150.0,
            "attempt": 1,
        },
    ]

    analytics = (
        InvestigationExecutionAnalytics(
            timeline
        )
    )

    metrics = (
        analytics.failure_retry_metrics()
    )

    assert metrics[
        "total_failures"
    ] == 3

    assert metrics[
        "total_retries"
    ] == 2

    assert metrics[
        "failures_by_agent"
    ] == {
        "investigator": 2,
        "reasoner": 1,
    }

    assert metrics[
        "retries_by_agent"
    ] == {
        "investigator": 2,
    }


def test_failure_retry_metrics_empty():

    analytics = (
        InvestigationExecutionAnalytics()
    )

    metrics = (
        analytics.failure_retry_metrics()
    )

    assert metrics == {
        "total_failures": 0,
        "total_retries": 0,
        "failures_by_agent": {},
        "retries_by_agent": {},
    }

def test_retry_count_counts_retry_attempts_only():

    timeline = [
        {
            "agent": "investigator",
            "status": "COMPLETED",
            "duration_ms": 100.0,
            "attempt": 1,
        },
        {
            "agent": "investigator",
            "status": "COMPLETED",
            "duration_ms": 200.0,
            "attempt": 2,
        },
        {
            "agent": "investigator",
            "status": "COMPLETED",
            "duration_ms": 300.0,
            "attempt": 3,
        },
    ]

    analytics = (
        InvestigationExecutionAnalytics(
            timeline
        )
    )

    assert analytics.retry_count() == 2

    assert (
        analytics.failure_retry_metrics()[
            "total_retries"
        ]
        == 2
    )

def test_non_failure_business_statuses_are_not_agent_failures():

    timeline = [
        {
            "agent": "reasoner",
            "status": "NO_EVIDENCE",
            "duration_ms": 10.0,
        },
        {
            "agent": "validator",
            "status": "REJECTED",
            "duration_ms": 5.0,
        },
    ]

    analytics = (
        InvestigationExecutionAnalytics(
            timeline
        )
    )

    assert (
        analytics.successful_executions()
        == 0
    )

    assert (
        analytics.failed_executions()
        == 0
    )

    performance = (
        analytics.agent_performance()
    )

    assert (
        performance["reasoner"][
            "failure_count"
        ]
        == 0
    )

    assert (
        performance["validator"][
            "failure_count"
        ]
        == 0
    )

    metrics = (
        analytics.failure_retry_metrics()
    )

    assert metrics[
        "total_failures"
    ] == 0

def test_bottleneck_detection():

    timeline = [
        {
            "agent": "planner",
            "status": "COMPLETED",
            "duration_ms": 100.0,
        },
        {
            "agent": "memory",
            "status": "COMPLETED",
            "duration_ms": 120.0,
        },
        {
            "agent": "reasoner",
            "status": "COMPLETED",
            "duration_ms": 500.0,
        },
    ]

    analytics = (
        InvestigationExecutionAnalytics(
            timeline
        )
    )

    bottlenecks = (
        analytics.bottleneck_agents()
    )

    assert len(bottlenecks) == 1

    assert (
        bottlenecks[0]["agent"]
        == "reasoner"
    )

    assert (
        bottlenecks[0][
            "average_duration_ms"
        ]
        == 500.0
    )


def test_bottleneck_detection_empty():

    analytics = (
        InvestigationExecutionAnalytics()
    )

    assert (
        analytics.bottleneck_agents()
        == []
    )


def test_bottleneck_custom_threshold():

    timeline = [
        {
            "agent": "planner",
            "status": "COMPLETED",
            "duration_ms": 100.0,
        },
        {
            "agent": "reasoner",
            "status": "COMPLETED",
            "duration_ms": 200.0,
        },
    ]

    analytics = (
        InvestigationExecutionAnalytics(
            timeline
        )
    )

    bottlenecks = (
        analytics.bottleneck_agents(
            threshold_multiplier=1.2
        )
    )

    assert len(bottlenecks) == 1

    assert (
        bottlenecks[0]["agent"]
        == "reasoner"
    )

def test_efficiency_score():

    timeline = [
        {
            "agent": "planner",
            "status": "COMPLETED",
            "duration_ms": 100.0,
            "attempt": 1,
        },
        {
            "agent": "investigator",
            "status": "COMPLETED",
            "duration_ms": 200.0,
            "attempt": 1,
        },
        {
            "agent": "reasoner",
            "status": "COMPLETED",
            "duration_ms": 300.0,
            "attempt": 1,
        },
    ]

    analytics = (
        InvestigationExecutionAnalytics(
            timeline
        )
    )

    result = (
        analytics.efficiency_score()
    )

    assert result["score"] == 100.0

    assert result[
        "rating"
    ] == "EXCELLENT"

    assert result[
        "success_rate"
    ] == 1.0

    assert result[
        "failure_rate"
    ] == 0.0

    assert result[
        "retry_rate"
    ] == 0.0

    assert result[
        "bottleneck_count"
    ] == 0


def test_efficiency_score_with_failures():

    timeline = [
        {
            "agent": "investigator",
            "status": "COMPLETED",
            "duration_ms": 100.0,
            "attempt": 1,
        },
        {
            "agent": "investigator",
            "status": "FAILED",
            "duration_ms": 200.0,
            "attempt": 1,
        },
        {
            "agent": "investigator",
            "status": "COMPLETED",
            "duration_ms": 300.0,
            "attempt": 2,
        },
    ]

    analytics = (
        InvestigationExecutionAnalytics(
            timeline
        )
    )

    result = (
        analytics.efficiency_score()
    )

    assert 0 <= result[
        "score"
    ] <= 100

    assert result[
        "failure_rate"
    ] == round(
        1 / 3,
        4,
    )

    assert result[
        "retry_rate"
    ] == round(
        1 / 3,
        4,
    )


def test_efficiency_score_empty():

    analytics = (
        InvestigationExecutionAnalytics()
    )

    result = (
        analytics.efficiency_score()
    )

    assert result == {
        "score": 0.0,
        "rating": "NO_DATA",
        "success_rate": 0.0,
        "failure_rate": 0.0,
        "retry_rate": 0.0,
        "bottleneck_count": 0,
    }

def test_unified_analytics_summary():

    timeline = [
        {
            "agent": "planner",
            "status": "COMPLETED",
            "duration_ms": 100.0,
            "attempt": 1,
        },
        {
            "agent": "investigator",
            "status": "FAILED",
            "duration_ms": 200.0,
            "attempt": 1,
        },
        {
            "agent": "investigator",
            "status": "COMPLETED",
            "duration_ms": 300.0,
            "attempt": 2,
        },
    ]

    analytics = (
        InvestigationExecutionAnalytics(
            timeline
        )
    )

    summary = analytics.unified_summary()

    assert "execution" in summary
    assert "agent_performance" in summary
    assert "failure_retry" in summary
    assert "bottlenecks" in summary
    assert "efficiency" in summary

    assert (
        summary["execution"][
            "total_executions"
        ]
        == analytics.total_executions()
    )

    assert (
        summary["agent_performance"]
        == analytics.agent_performance()
    )

    assert (
        summary["failure_retry"]
        == analytics.failure_retry_metrics()
    )

    assert (
        summary["bottlenecks"]
        == analytics.bottleneck_agents()
    )

    assert (
        summary["efficiency"]
        == analytics.efficiency_score()
    )


def test_unified_analytics_summary_empty():

    analytics = (
        InvestigationExecutionAnalytics()
    )

    summary = analytics.unified_summary()

    assert summary[
        "execution"
    ]["total_executions"] == 0

    assert summary[
        "execution"
    ]["successful_executions"] == 0

    assert summary[
        "execution"
    ]["failed_executions"] == 0

    assert summary[
        "agent_performance"
    ] == {}

    assert summary[
        "failure_retry"
    ] == {
        "total_failures": 0,
        "total_retries": 0,
        "failures_by_agent": {},
        "retries_by_agent": {},
    }

    assert summary[
        "bottlenecks"
    ] == []

    assert summary[
        "efficiency"
    ]["rating"] == "NO_DATA"

def test_slowest_agent_uses_real_duration():

    timeline = [
        {
            "agent": "memory",
            "status": "COMPLETED",
            "duration_ms": 13710.0,
        },
        {
            "agent": "orchestrator",
            "status": "COMPLETED",
            "duration_ms": 0.02,
        },
        {
            "agent": "investigator",
            "status": "COMPLETED",
            "duration_ms": 8.6,
        },
        {
            "agent": "reasoner",
            "status": "NO_EVIDENCE",
            "duration_ms": 0.04,
        },
        {
            "agent": "validator",
            "status": "REJECTED",
            "duration_ms": 0.02,
        },
    ]

    analytics = InvestigationExecutionAnalytics(
        timeline
    )

    assert analytics.slowest_agent() == "memory"

    assert (
        analytics.slowest_agent_duration_ms()
        == 13710.0
    )

def test_bottleneck_agents_uses_agent_average_duration():

    timeline = [
        {
            "agent": "memory",
            "status": "COMPLETED",
            "duration_ms": 13710.0,
        },
        {
            "agent": "investigator",
            "status": "COMPLETED",
            "duration_ms": 8.6,
        },
        {
            "agent": "reasoner",
            "status": "NO_EVIDENCE",
            "duration_ms": 0.04,
        },
        {
            "agent": "validator",
            "status": "REJECTED",
            "duration_ms": 0.02,
        },
    ]

    analytics = InvestigationExecutionAnalytics(
        timeline
    )

    bottlenecks = analytics.bottleneck_agents()

    assert len(bottlenecks) == 1

    bottleneck = bottlenecks[0]

    assert bottleneck["agent"] == "memory"

    assert (
        bottleneck["average_duration_ms"]
        == 13710.0
    )

    assert (
        bottleneck["slowdown_ratio"]
        > 1.5
    )

    assert (
        bottleneck["overall_average_duration_ms"]
        > 0
    )

def test_bottleneck_agents_respects_threshold_multiplier():

    timeline = [
        {
            "agent": "fast",
            "status": "COMPLETED",
            "duration_ms": 10.0,
        },
        {
            "agent": "slow",
            "status": "COMPLETED",
            "duration_ms": 40.0,
        },
    ]

    analytics = InvestigationExecutionAnalytics(
        timeline
    )

    bottlenecks = analytics.bottleneck_agents(
        threshold_multiplier=1.5
    )

    assert len(bottlenecks) == 1

    assert (
        bottlenecks[0]["agent"]
        == "slow"
    )

    assert (
        bottlenecks[0]["slowdown_ratio"]
        == round(40.0 / 25.0, 2)
    )

def test_failure_retry_metrics_correlates_failures_and_retries():

    timeline = [
        {
            "agent": "investigator",
            "status": "FAILED",
            "attempt": 1,
        },
        {
            "agent": "investigator",
            "status": "FAILED",
            "attempt": 2,
        },
        {
            "agent": "investigator",
            "status": "COMPLETED",
            "attempt": 3,
        },
        {
            "agent": "reasoner",
            "status": "NO_EVIDENCE",
            "attempt": 1,
        },
        {
            "agent": "validator",
            "status": "REJECTED",
            "attempt": 1,
        },
    ]

    analytics = InvestigationExecutionAnalytics(
        timeline
    )

    metrics = analytics.failure_retry_metrics()

    assert metrics["total_failures"] == 2

    assert metrics["total_retries"] == 2

    assert (
        metrics["failures_by_agent"]["investigator"]
        == 2
    )

    assert (
        metrics["retries_by_agent"]["investigator"]
        == 2
    )

    assert (
        "reasoner"
        not in metrics["failures_by_agent"]
    )

    assert (
        "validator"
        not in metrics["failures_by_agent"]
    )

def test_business_rejections_are_not_execution_failures():

    timeline = [
        {
            "agent": "reasoner",
            "status": "NO_EVIDENCE",
            "attempt": 1,
        },
        {
            "agent": "validator",
            "status": "REJECTED",
            "attempt": 1,
        },
        {
            "agent": "validator",
            "status": "COMPLETED",
            "attempt": 1,
        },
    ]

    analytics = InvestigationExecutionAnalytics(
        timeline
    )

    metrics = analytics.failure_retry_metrics()

    assert metrics["total_failures"] == 0

    assert metrics["total_retries"] == 0

    assert metrics["failures_by_agent"] == {}

    assert metrics["retries_by_agent"] == {}