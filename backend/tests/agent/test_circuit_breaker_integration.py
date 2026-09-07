from app.agent.circuit_breaker import (
    CircuitState,
)
from app.agent.circuit_breaker_runtime import (
    allow_agent_execution,
    record_agent_failure,
    record_agent_success,
)


def test_agent_is_allowed_when_circuit_is_closed():
    state = {}

    assert (
        allow_agent_execution(
            state,
            "investigator",
        )
        is True
    )

    assert (
        state[
            "circuit_breaker_states"
        ]["investigator"]
        == "CLOSED"
    )


def test_repeated_failures_open_agent_circuit():
    state = {}

    for _ in range(3):
        record_agent_failure(
            state,
            "investigator",
        )

    assert (
        state[
            "circuit_breaker_states"
        ]["investigator"]
        == "OPEN"
    )

    assert (
        allow_agent_execution(
            state,
            "investigator",
        )
        is False
    )


def test_circuit_isolated_per_agent():
    state = {}

    for _ in range(3):
        record_agent_failure(
            state,
            "investigator",
        )

    assert (
        allow_agent_execution(
            state,
            "investigator",
        )
        is False
    )

    assert (
        allow_agent_execution(
            state,
            "reasoner",
        )
        is True
    )


def test_success_resets_agent_circuit():
    state = {}

    record_agent_failure(
        state,
        "investigator",
    )
    record_agent_failure(
        state,
        "investigator",
    )

    record_agent_success(
        state,
        "investigator",
    )

    assert (
        state[
            "circuit_breaker_states"
        ]["investigator"]
        == "CLOSED"
    )

    assert (
        state[
            "circuit_breaker_failures"
        ]["investigator"]
        == 0
    )
