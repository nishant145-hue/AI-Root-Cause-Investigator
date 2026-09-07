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
