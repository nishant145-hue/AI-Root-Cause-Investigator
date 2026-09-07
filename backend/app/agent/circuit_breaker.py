from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum


class CircuitState(str, Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


@dataclass(frozen=True)
class CircuitBreakerPolicy:
    """
    Configuration for agent circuit breakers.
    """

    failure_threshold: int = 3
    recovery_timeout_seconds: float = 30.0
    half_open_max_calls: int = 1

    def __post_init__(self) -> None:
        if self.failure_threshold <= 0:
            raise ValueError(
                "failure_threshold must be greater than 0"
            )

        if self.recovery_timeout_seconds <= 0:
            raise ValueError(
                "recovery_timeout_seconds must be greater than 0"
            )

        if self.half_open_max_calls <= 0:
            raise ValueError(
                "half_open_max_calls must be greater than 0"
            )


@dataclass
class CircuitBreakerState:
    """
    Runtime state for one agent circuit.
    """

    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    opened_at: datetime | None = None
    half_open_calls: int = 0


class CircuitBreaker:
    """
    Per-agent circuit breaker.

    CLOSED:
        Agent executions are allowed.

    OPEN:
        Agent executions are blocked until the recovery
        timeout expires.

    HALF_OPEN:
        A limited number of probe executions are allowed
        to determine whether the agent recovered.
    """

    def __init__(
        self,
        policy: CircuitBreakerPolicy | None = None,
    ) -> None:
        self.policy = (
            policy
            or CircuitBreakerPolicy()
        )

        self._states: dict[
            str,
            CircuitBreakerState,
        ] = {}

    def _state_for(
        self,
        agent: str,
    ) -> CircuitBreakerState:
        if not agent:
            raise ValueError(
                "agent must not be empty"
            )

        if agent not in self._states:
            self._states[agent] = (
                CircuitBreakerState()
            )

        return self._states[agent]

    def state(
        self,
        agent: str,
    ) -> CircuitState:
        """
        Return the current state of an agent.
        """

        return self._state_for(agent).state

    def allow_request(
        self,
        agent: str,
    ) -> bool:
        """
        Determine whether an agent execution is allowed.
        """

        state = self._state_for(agent)

        if state.state == CircuitState.CLOSED:
            return True

        if state.state == CircuitState.OPEN:
            if self._recovery_timeout_elapsed(
                state
            ):
                state.state = (
                    CircuitState.HALF_OPEN
                )
                state.half_open_calls = 0

            else:
                return False

        if state.state == CircuitState.HALF_OPEN:
            if (
                state.half_open_calls
                >= self.policy.half_open_max_calls
            ):
                return False

            state.half_open_calls += 1
            return True

        return False

    def record_success(
        self,
        agent: str,
    ) -> None:
        """
        Successful execution closes the circuit.
        """

        state = self._state_for(agent)

        state.state = CircuitState.CLOSED
        state.failure_count = 0
        state.opened_at = None
        state.half_open_calls = 0

    def record_failure(
        self,
        agent: str,
    ) -> CircuitState:
        """
        Record an agent failure and update its circuit.
        """

        state = self._state_for(agent)

        state.failure_count += 1

        if (
            state.failure_count
            >= self.policy.failure_threshold
        ):
            state.state = CircuitState.OPEN
            state.opened_at = (
                datetime.now(timezone.utc)
            )
            state.half_open_calls = 0

        return state.state

    def reset(
        self,
        agent: str,
    ) -> None:
        """
        Reset an agent circuit to CLOSED.
        """

        state = self._state_for(agent)

        state.state = CircuitState.CLOSED
        state.failure_count = 0
        state.opened_at = None
        state.half_open_calls = 0

    def snapshot(
        self,
        agent: str,
    ) -> dict:
        """
        Return serializable circuit state.
        """

        state = self._state_for(agent)

        return {
            "agent": agent,
            "state": state.state.value,
            "failure_count": state.failure_count,
            "opened_at": (
                state.opened_at.isoformat()
                if state.opened_at
                else None
            ),
            "half_open_calls": (
                state.half_open_calls
            ),
        }

    def _recovery_timeout_elapsed(
        self,
        state: CircuitBreakerState,
    ) -> bool:
        if state.opened_at is None:
            return False

        now = datetime.now(timezone.utc)

        elapsed = now - state.opened_at

        return elapsed >= timedelta(
            seconds=(
                self.policy
                .recovery_timeout_seconds
            )
        )
