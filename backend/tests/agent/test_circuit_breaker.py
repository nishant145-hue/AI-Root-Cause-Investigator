from datetime import timedelta
from unittest.mock import patch

import pytest

from app.agent.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerPolicy,
    CircuitState,
)


def test_circuit_starts_closed():
    breaker = CircuitBreaker()

    assert (
        breaker.state("memory")
        == CircuitState.CLOSED
    )

    assert breaker.allow_request("memory") is True


def test_circuit_opens_after_failure_threshold():
    breaker = CircuitBreaker(
        CircuitBreakerPolicy(
            failure_threshold=3,
        )
    )

    breaker.record_failure("memory")
    assert (
        breaker.state("memory")
        == CircuitState.CLOSED
    )

    breaker.record_failure("memory")
    assert (
        breaker.state("memory")
        == CircuitState.CLOSED
    )

    breaker.record_failure("memory")
    assert (
        breaker.state("memory")
        == CircuitState.OPEN
    )

    assert (
        breaker.allow_request("memory")
        is False
    )


def test_success_resets_circuit():
    breaker = CircuitBreaker(
        CircuitBreakerPolicy(
            failure_threshold=2,
        )
    )

    breaker.record_failure("memory")
    breaker.record_failure("memory")

    assert (
        breaker.state("memory")
        == CircuitState.OPEN
    )

    breaker.record_success("memory")

    assert (
        breaker.state("memory")
        == CircuitState.CLOSED
    )

    assert (
        breaker.allow_request("memory")
        is True
    )


def test_circuits_are_isolated_per_agent():
    breaker = CircuitBreaker(
        CircuitBreakerPolicy(
            failure_threshold=2,
        )
    )

    breaker.record_failure("memory")
    breaker.record_failure("memory")

    assert (
        breaker.state("memory")
        == CircuitState.OPEN
    )

    assert (
        breaker.state("reasoner")
        == CircuitState.CLOSED
    )

    assert (
        breaker.allow_request("reasoner")
        is True
    )

    assert (
        breaker.allow_request("memory")
        is False
    )


def test_open_circuit_moves_to_half_open_after_timeout():
    breaker = CircuitBreaker(
        CircuitBreakerPolicy(
            failure_threshold=1,
            recovery_timeout_seconds=30,
        )
    )

    breaker.record_failure("memory")

    assert (
        breaker.state("memory")
        == CircuitState.OPEN
    )

    state = breaker._state_for("memory")

    state.opened_at = (
        state.opened_at
        - timedelta(seconds=31)
    )

    assert (
        breaker.allow_request("memory")
        is True
    )

    assert (
        breaker.state("memory")
        == CircuitState.HALF_OPEN
    )


def test_half_open_allows_only_one_probe():
    breaker = CircuitBreaker(
        CircuitBreakerPolicy(
            failure_threshold=1,
            recovery_timeout_seconds=30,
            half_open_max_calls=1,
        )
    )

    breaker.record_failure("memory")

    state = breaker._state_for("memory")

    state.opened_at = (
        state.opened_at
        - timedelta(seconds=31)
    )

    assert (
        breaker.allow_request("memory")
        is True
    )

    assert (
        breaker.allow_request("memory")
        is False
    )


def test_half_open_success_closes_circuit():
    breaker = CircuitBreaker(
        CircuitBreakerPolicy(
            failure_threshold=1,
            recovery_timeout_seconds=30,
        )
    )

    breaker.record_failure("memory")

    state = breaker._state_for("memory")

    state.opened_at = (
        state.opened_at
        - timedelta(seconds=31)
    )

    assert breaker.allow_request("memory") is True

    assert (
        breaker.state("memory")
        == CircuitState.HALF_OPEN
    )

    breaker.record_success("memory")

    assert (
        breaker.state("memory")
        == CircuitState.CLOSED
    )

    assert (
        breaker.allow_request("memory")
        is True
    )


def test_half_open_failure_reopens_circuit():
    breaker = CircuitBreaker(
        CircuitBreakerPolicy(
            failure_threshold=1,
            recovery_timeout_seconds=30,
        )
    )

    breaker.record_failure("memory")

    state = breaker._state_for("memory")

    state.opened_at = (
        state.opened_at
        - timedelta(seconds=31)
    )

    assert breaker.allow_request("memory") is True

    breaker.record_failure("memory")

    assert (
        breaker.state("memory")
        == CircuitState.OPEN
    )


def test_invalid_policy_is_rejected():
    with pytest.raises(ValueError):
        CircuitBreakerPolicy(
            failure_threshold=0
        )

    with pytest.raises(ValueError):
        CircuitBreakerPolicy(
            recovery_timeout_seconds=0
        )

    with pytest.raises(ValueError):
        CircuitBreakerPolicy(
            half_open_max_calls=0
        )


def test_snapshot_is_serializable():
    breaker = CircuitBreaker()

    snapshot = breaker.snapshot("memory")

    assert snapshot["agent"] == "memory"
    assert snapshot["state"] == "CLOSED"
    assert snapshot["failure_count"] == 0
    assert snapshot["opened_at"] is None
    assert snapshot["half_open_calls"] == 0
