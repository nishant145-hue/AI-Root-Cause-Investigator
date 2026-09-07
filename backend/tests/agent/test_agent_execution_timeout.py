import time

from app.agent.recovery import (
    run_with_failure_capture,
)


def test_agent_timeout_is_captured():
    def slow_node(state):
        time.sleep(0.2)
        return {"result": "completed"}

    result = run_with_failure_capture(
        {},
        agent_name="investigator",
        node=slow_node,
        timeout_seconds=0.05,
    )

    assert result["last_failed_agent"] == "investigator"
    assert result["last_failure_type"] == "TRANSIENT"
    assert "timeout" in (
        result["last_failure_message"].lower()
    )
    assert (
        result["failure_metadata"]["failure_type"]
        == "TIMEOUT"
    )


def test_fast_agent_completes_before_timeout():
    def fast_node(state):
        return {"result": "completed"}

    result = run_with_failure_capture(
        {},
        agent_name="investigator",
        node=fast_node,
        timeout_seconds=1.0,
    )

    assert result == {
        "result": "completed"
    }


def test_agent_exception_is_captured():
    def failing_node(state):
        raise RuntimeError(
            "Injected agent failure"
        )

    result = run_with_failure_capture(
        {},
        agent_name="investigator",
        node=failing_node,
        timeout_seconds=1.0,
    )

    assert (
        result["last_failed_agent"]
        == "investigator"
    )

    assert (
        result["last_failure_type"]
        == "CRITICAL"
    )

    assert (
        result["last_failure_message"]
        == "Injected agent failure"
    )
