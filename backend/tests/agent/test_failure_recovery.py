from app.agent.failure import (
    AgentFailure,
    AgentFailureType,
    RecoveryAction,
    classify_failure,
    determine_recovery,
)


def test_transient_failure_is_classified():

    failure = classify_failure(
        agent="memory",
        exc=TimeoutError("Qdrant timeout"),
    )

    assert (
        failure.failure_type
        == AgentFailureType.TRANSIENT
    )

    assert failure.agent == "memory"


def test_transient_failure_retries():

    failure = AgentFailure(
        agent="memory",
        failure_type=AgentFailureType.TRANSIENT,
        message="Qdrant timeout",
        attempt=1,
    )

    decision = determine_recovery(failure)

    assert decision.action == RecoveryAction.RETRY
    assert decision.next_agent == "memory"


def test_transient_failure_reroutes_after_retry_limit():

    failure = AgentFailure(
        agent="memory",
        failure_type=AgentFailureType.TRANSIENT,
        message="Qdrant timeout",
        attempt=3,
    )

    decision = determine_recovery(
        failure,
        max_retries=2,
    )

    assert decision.action == RecoveryAction.REROUTE


def test_recoverable_failure_reroutes():

    failure = AgentFailure(
        agent="reasoner",
        failure_type=AgentFailureType.RECOVERABLE,
        message="Invalid reasoning response",
    )

    decision = determine_recovery(failure)

    assert decision.action == RecoveryAction.REROUTE


def test_critical_failure_stops():

    failure = AgentFailure(
        agent="validator",
        failure_type=AgentFailureType.CRITICAL,
        message="Invalid investigation state",
    )

    decision = determine_recovery(failure)

    assert decision.action == RecoveryAction.STOP
