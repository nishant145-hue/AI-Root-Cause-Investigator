from __future__ import annotations

from typing import Any

from app.agent.circuit_breaker import CircuitState
from app.agent.circuit_breaker_runtime import (
    allow_agent_execution,
)


MAX_REROUTES = 3


class AgentIsolationError(RuntimeError):
    """Raised when no safe agent route is available."""


def get_isolated_agents(
    state: dict[str, Any],
) -> list[str]:
    """
    Return the agents currently isolated by the
    circuit breaker.
    """

    isolated = state.get(
        "isolated_agents",
        [],
    )

    if not isinstance(isolated, list):
        return []

    return [
        str(agent)
        for agent in isolated
        if agent
    ]


def refresh_agent_isolation(
    state: dict[str, Any],
    agent_name: str,
) -> bool:
    """
    Synchronize isolation with the circuit breaker.

    Important:
    An explicitly isolated agent must remain isolated even
    when no circuit-breaker state exists.

    Only an explicitly known circuit state is allowed to
    change the isolation status.
    """

    circuit_states = state.get(
        "circuit_breaker_states",
        {},
    )

    circuit_state = circuit_states.get(
        agent_name
    )

    isolated = get_isolated_agents(
        state
    )

    # ---------------------------------------------------------
    # Circuit explicitly OPEN
    # ---------------------------------------------------------

    if circuit_state == CircuitState.OPEN.value:

        if agent_name not in isolated:
            isolated.append(
                agent_name
            )

    # ---------------------------------------------------------
    # Circuit explicitly CLOSED
    # ---------------------------------------------------------

    elif circuit_state == CircuitState.CLOSED.value:

        isolated = [
            agent
            for agent in isolated
            if agent != agent_name
        ]

    # ---------------------------------------------------------
    # HALF_OPEN
    #
    # Do NOT automatically remove explicit isolation here.
    # The circuit-breaker runtime controls whether a probe
    # is allowed.
    # ---------------------------------------------------------

    elif circuit_state == CircuitState.HALF_OPEN.value:

        if agent_name not in isolated:
            isolated.append(
                agent_name
            )

    # ---------------------------------------------------------
    # Unknown / missing circuit state
    #
    # Preserve explicit isolation.
    # ---------------------------------------------------------

    else:
        pass

    state[
        "isolated_agents"
    ] = isolated

    return agent_name in isolated


def isolate_agent(
    state: dict[str, Any],
    agent_name: str,
) -> None:
    """
    Explicitly isolate an agent.
    """

    isolated = get_isolated_agents(
        state
    )

    if agent_name not in isolated:
        isolated.append(agent_name)

    state[
        "isolated_agents"
    ] = isolated


def release_agent(
    state: dict[str, Any],
    agent_name: str,
) -> None:
    """
    Remove an agent from the isolated list.
    """

    isolated = get_isolated_agents(
        state
    )

    state[
        "isolated_agents"
    ] = [
        agent
        for agent in isolated
        if agent != agent_name
    ]


def is_agent_isolated(
    state: dict[str, Any],
    agent_name: str,
) -> bool:
    """
    Check whether an agent is currently isolated.

    Explicit isolation remains authoritative when no
    circuit-breaker state has been recorded.
    """

    isolated = get_isolated_agents(
        state
    )

    # Explicitly isolated agents remain isolated unless
    # the circuit breaker explicitly reports a CLOSED state.
    if agent_name in isolated:

        circuit_states = state.get(
            "circuit_breaker_states",
            {},
        )

        circuit_state = circuit_states.get(
            agent_name
        )

        if circuit_state in {
            CircuitState.CLOSED.value,
            CircuitState.CLOSED.name,
        }:
            release_agent(
                state,
                agent_name,
            )

            return False

        return True

    # Agent isn't explicitly isolated. Synchronize with
    # the circuit breaker.
    return refresh_agent_isolation(
        state,
        agent_name,
    )


def select_reroute_agent(
    state: dict[str, Any],
    *,
    failed_agent: str,
    candidates: list[str],
) -> str | None:
    """
    Select the first candidate whose circuit is not OPEN.

    The failed agent is never selected again during the
    same rerouting decision.
    """

    reroute_count = int(
        state.get(
            "reroute_count",
            0,
        )
    )

    if reroute_count >= MAX_REROUTES:
        return None

    isolated = set(
        get_isolated_agents(state)
    )

    for candidate in candidates:

        if not candidate:
            continue

        if candidate == failed_agent:
            continue

        if candidate in isolated:
            continue

        circuit_states = state.get(
            "circuit_breaker_states",
            {},
        )

        if (
            circuit_states.get(candidate)
            == CircuitState.OPEN.value
        ):
            isolate_agent(
                state,
                candidate,
            )
            continue

        # Do not execute here.
        # This only checks whether the circuit permits
        # the candidate.
        if allow_agent_execution(
            state,
            candidate,
        ):
            # We consumed the HALF_OPEN probe if this
            # candidate was HALF_OPEN. The actual execution
            # boundary must therefore use the same decision
            # carefully.
            return candidate

    return None


def record_reroute(
    state: dict[str, Any],
    *,
    failed_agent: str,
    target_agent: str,
) -> None:
    """
    Record a rerouting decision.
    """

    state["reroute_count"] = (
        int(
            state.get(
                "reroute_count",
                0,
            )
        )
        + 1
    )

    state[
        "last_rerouted_agent"
    ] = failed_agent

    state[
        "next_agent"
    ] = target_agent
