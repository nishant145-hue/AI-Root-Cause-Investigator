from app.agent.nodes.analytics import (
    analytics_node,
)


def test_analytics_node_persists_summary():

    state = {
        "execution_timeline": [
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
        ]
    }

    result = analytics_node(state)

    assert "execution_analytics" in result

    analytics = result[
        "execution_analytics"
    ]

    assert "execution" in analytics
    assert "agent_performance" in analytics
    assert "failure_retry" in analytics
    assert "bottlenecks" in analytics
    assert "efficiency" in analytics


def test_analytics_node_empty_timeline():

    state = {
        "execution_timeline": []
    }

    result = analytics_node(state)

    analytics = result[
        "execution_analytics"
    ]

    assert analytics[
        "execution"
    ]["total_executions"] == 0

    assert analytics[
        "agent_performance"
    ] == {}

    assert analytics[
        "failure_retry"
    ] == {
        "total_failures": 0,
        "total_retries": 0,
        "failures_by_agent": {},
        "retries_by_agent": {},
    }

    assert analytics[
        "bottlenecks"
    ] == []

    assert analytics[
        "efficiency"
    ]["rating"] == "NO_DATA"


def test_analytics_node_does_not_modify_timeline():

    timeline = [
        {
            "agent": "reasoner",
            "status": "COMPLETED",
            "duration_ms": 250.0,
            "attempt": 1,
        }
    ]

    state = {
        "execution_timeline": timeline
    }

    original_timeline = list(
        timeline
    )

    analytics_node(state)

    assert (
        state["execution_timeline"]
        == original_timeline
    )


def test_analytics_node_handles_missing_timeline():

    state = {}

    result = analytics_node(state)

    assert (
        result[
            "execution_analytics"
        ]["execution"][
            "total_executions"
        ]
        == 0
    )
