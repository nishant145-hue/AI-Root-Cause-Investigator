import pytest

from app.agent.timeout_policy import AgentTimeoutPolicy


def test_timeout_policy_has_expected_defaults():
    policy = AgentTimeoutPolicy(
        agent_timeout_seconds=60.0,
        investigation_timeout_seconds=300.0,
        recovery_timeout_seconds=30.0,
    )

    assert policy.timeout_for("agent") == 60.0
    assert policy.timeout_for("investigation") == 300.0
    assert policy.timeout_for("recovery") == 30.0


def test_unknown_operation_raises():
    policy = AgentTimeoutPolicy(
        agent_timeout_seconds=60.0,
        investigation_timeout_seconds=300.0,
        recovery_timeout_seconds=30.0,
    )

    with pytest.raises(ValueError):
        policy.timeout_for("unknown")
