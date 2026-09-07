import pytest

from app.agent.timeout import AgentTimeoutError


def test_agent_timeout_error():
    error = AgentTimeoutError(
        agent_name="investigator",
        timeout_seconds=60.0,
    )

    assert isinstance(error, TimeoutError)
    assert error.agent_name == "investigator"
    assert error.timeout_seconds == 60.0
    assert "investigator" in str(error)
    assert "60.00" in str(error)
