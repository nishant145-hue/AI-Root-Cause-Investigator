from __future__ import annotations

from typing import Any

from app.agent.circuit_breaker import (
    CircuitBreaker,
    CircuitState,
)


class CircuitBreakerBlockedError(RuntimeError):
    """
    Raised when an agent is blocked by an OPEN circuit.
    """

    def __init__(
        self,
        agent_name: str,
        state: CircuitState,
    ) -> None:
        self.agent_name = agent_name
        self.state = state

        super().__init__(
            f"Agent '{agent_name}' is blocked because "
            f"its circuit is {state.value}."
        )


def get_circuit_breaker(
    state: dict[str, Any],
) -> CircuitBreaker:
    """
    Return the circuit breaker associated with the
    current execution context.

    The breaker itself is kept on the execution state
    so the graph can preserve circuit information.
    """

    breaker = state.get(
        "_circuit_breaker"
    )

    if isinstance(
        breaker,
        CircuitBreaker,
    ):
        return breaker

    breaker = CircuitBreaker()

    state[
        "_circuit_breaker"
    ] = breaker

    return breaker


def sync_circuit_state(
    state: dict[str, Any],
    agent_name: str,
    breaker: CircuitBreaker,
) -> None:
    """
    Copy the circuit-breaker state into serializable
    LangGraph state fields.
    """

    snapshot = breaker.snapshot(
        agent_name
    )

    circuit_states = dict(
        state.get(
            "circuit_breaker_states",
            {},
        )
    )

    circuit_failures = dict(
        state.get(
            "circuit_breaker_failures",
            {},
        )
    )

    circuit_opened_at = dict(
        state.get(
            "circuit_breaker_opened_at",
            {},
        )
    )

    circuit_states[agent_name] = (
        snapshot["state"]
    )

    circuit_failures[agent_name] = int(
        snapshot["failure_count"]
    )

    opened_at = snapshot["opened_at"]

    if opened_at is None:
        circuit_opened_at.pop(
            agent_name,
            None,
        )
    else:
        from datetime import datetime

        circuit_opened_at[agent_name] = (
            datetime.fromisoformat(
                opened_at
            ).timestamp()
        )

    state[
        "circuit_breaker_states"
    ] = circuit_states

    state[
        "circuit_breaker_failures"
    ] = circuit_failures

    state[
        "circuit_breaker_opened_at"
    ] = circuit_opened_at


def allow_agent_execution(
    state: dict[str, Any],
    agent_name: str,
) -> bool:
    """
    Determine whether an agent may execute.

    The circuit breaker is checked before the actual
    agent execution.
    """

    breaker = get_circuit_breaker(
        state
    )

    allowed = breaker.allow_request(
        agent_name
    )

    sync_circuit_state(
        state,
        agent_name,
        breaker,
    )

    return allowed


def record_agent_success(
    state: dict[str, Any],
    agent_name: str,
) -> None:
    """
    Record successful execution and close/reset
    the agent circuit.
    """

    breaker = get_circuit_breaker(
        state
    )

    breaker.record_success(
        agent_name
    )

    sync_circuit_state(
        state,
        agent_name,
        breaker,
    )


def record_agent_failure(
    state: dict[str, Any],
    agent_name: str,
) -> CircuitState:
    """
    Record an agent failure.

    Returns the resulting circuit state.
    """

    breaker = get_circuit_breaker(
        state
    )

    circuit_state = breaker.record_failure(
        agent_name
    )

    sync_circuit_state(
        state,
        agent_name,
        breaker,
    )

    return circuit_state
