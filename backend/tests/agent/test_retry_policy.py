from app.agent.failure import (
    AgentFailure,
    AgentFailureType,
    RecoveryAction,
    RetryPolicy,
    RetryTracker,
    determine_recovery,
)


def test_retry_policy_allows_retry():

    policy = RetryPolicy(
        max_retries=2
    )

    assert policy.can_retry(1) is True
    assert policy.can_retry(2) is True


def test_retry_policy_blocks_after_limit():

    policy = RetryPolicy(
        max_retries=2
    )

    assert policy.can_retry(3) is False


def test_retry_tracker_tracks_agents_independently():

    tracker = RetryTracker(
        RetryPolicy(max_retries=2)
    )

    assert tracker.record_failure(
        "memory"
    ) == 1

    assert tracker.record_failure(
        "memory"
    ) == 2

    assert tracker.record_failure(
        "reasoner"
    ) == 1

    assert tracker.attempts(
        "memory"
    ) == 2

    assert tracker.attempts(
        "reasoner"
    ) == 1


def test_retry_tracker_blocks_after_limit():

    tracker = RetryTracker(
        RetryPolicy(max_retries=2)
    )

    tracker.record_failure("memory")
    tracker.record_failure("memory")

    assert tracker.can_retry(
        "memory"
    ) is True

    tracker.record_failure("memory")

    assert tracker.can_retry(
        "memory"
    ) is False


def test_retry_tracker_reset():

    tracker = RetryTracker(
        RetryPolicy(max_retries=2)
    )

    tracker.record_failure("memory")

    assert tracker.attempts(
        "memory"
    ) == 1

    tracker.reset("memory")

    assert tracker.attempts(
        "memory"
    ) == 0


def test_transient_failure_retries():

    failure = AgentFailure(
        agent="memory",
        failure_type=AgentFailureType.TRANSIENT,
        message="Qdrant timeout",
        attempt=1,
    )

    decision = determine_recovery(
        failure,
        max_retries=2,
    )

    assert decision.action == RecoveryAction.RETRY
    assert decision.next_agent == "memory"


def test_transient_failure_reroutes_after_limit():

    failure = AgentFailure(
        agent="memory",
        failure_type=AgentFailureType.TRANSIENT,
        message="Qdrant unavailable",
        attempt=3,
    )

    decision = determine_recovery(
        failure,
        max_retries=2,
    )

    assert decision.action == RecoveryAction.REROUTE


def test_recoverable_failure_does_not_retry():

    failure = AgentFailure(
        agent="reasoner",
        failure_type=AgentFailureType.RECOVERABLE,
        message="Invalid LLM response",
        attempt=1,
    )

    decision = determine_recovery(
        failure
    )

    assert decision.action == RecoveryAction.REROUTE


def test_critical_failure_stops():

    failure = AgentFailure(
        agent="validator",
        failure_type=AgentFailureType.CRITICAL,
        message="Invalid investigation state",
        attempt=1,
    )

    decision = determine_recovery(
        failure
    )

    assert decision.action == RecoveryAction.STOP
