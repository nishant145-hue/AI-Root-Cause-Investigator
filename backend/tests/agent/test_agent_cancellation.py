import time

from app.agent.recovery import run_with_failure_capture


def test_agent_timeout_records_cancellation_metadata():
    def slow_node(state):
        time.sleep(0.5)
        return {"result": "completed"}

    result = run_with_failure_capture(
        {},
        agent_name="investigator",
        node=slow_node,
        timeout_seconds=0.05,
    )

    assert result["last_failed_agent"] == "investigator"
    assert result["last_failure_type"] == "TRANSIENT"

    assert result["failure_metadata"]["failure_type"] == "TIMEOUT"

    assert result["cancellation_metadata"]["cancelled"] is True
    assert (
        result["cancellation_metadata"]["agent"]
        == "investigator"
    )


def test_fast_agent_is_not_cancelled():
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


def test_exception_does_not_report_as_cancellation():
    def failing_node(state):
        raise RuntimeError("Injected failure")

    result = run_with_failure_capture(
        {},
        agent_name="investigator",
        node=failing_node,
        timeout_seconds=1.0,
    )

    assert result["last_failed_agent"] == "investigator"
    assert result["last_failure_type"] == "CRITICAL"

    assert result.get(
        "cancellation_metadata",
        {},
    ).get("cancelled", False) is False
