from app.agent.failure import (
    AgentFailureType,
    RecoveryAction,
)
from app.models.investigation import (
    Investigation,
    InvestigationStatus,
)
from app.services.failure_recovery_service import (
    FailureRecoveryService,
)


def create_investigation(
    db_session,
    test_user,
):
    investigation = Investigation(
        title="Failure Recovery Test",
        description="Testing recovery",
        user_id=test_user.id,
        status=InvestigationStatus.IN_PROGRESS,
        summary="Completed summary",
        root_cause="Existing root cause",
        severity="HIGH",
        confidence=0.85,
        additional_notes="Existing notes",
        execution_analytics={
            "execution": {
                "total_executions": 3,
            }
        },
    )

    db_session.add(investigation)
    db_session.commit()
    db_session.refresh(investigation)

    return investigation


def test_transient_failure_is_retryable(
    db_session,
    test_user,
):
    service = FailureRecoveryService(
        db_session,
        max_retries=2,
    )

    investigation = create_investigation(
        db_session,
        test_user,
    )

    failure = service.classify(
        agent="investigator",
        exc=TimeoutError(
            "temporary timeout"
        ),
        attempt=1,
    )

    decision = service.decide(
        failure
    )

    assert (
        failure.failure_type
        == AgentFailureType.TRANSIENT
    )

    assert (
        decision.action
        == RecoveryAction.RETRY
    )


def test_critical_failure_stops_investigation(
    db_session,
    test_user,
):
    service = FailureRecoveryService(
        db_session
    )

    investigation = create_investigation(
        db_session,
        test_user,
    )

    failure = service.classify(
        agent="validator",
        exc=RuntimeError(
            "critical failure"
        ),
        attempt=1,
    )

    decision = service.decide(
        failure
    )

    updated = service.record_failure(
        investigation=investigation,
        failure=failure,
        decision=decision,
    )

    assert (
        decision.action
        == RecoveryAction.STOP
    )

    assert (
        updated.status
        == InvestigationStatus.FAILED
    )

    assert (
        updated.failed_component
        == "validator"
    )


def test_failure_preserves_partial_results(
    db_session,
    test_user,
):
    service = FailureRecoveryService(
        db_session
    )

    investigation = create_investigation(
        db_session,
        test_user,
    )

    original_root_cause = (
        investigation.root_cause
    )

    failure = service.classify(
        agent="reasoner",
        exc=RuntimeError(
            "reasoner failed"
        ),
    )

    decision = service.decide(
        failure
    )

    updated = service.record_failure(
        investigation=investigation,
        failure=failure,
        decision=decision,
        partial_state={
            "summary": (
                "Updated partial summary"
            ),
        },
    )

    assert (
        updated.summary
        == "Updated partial summary"
    )

    assert (
        updated.root_cause
        == original_root_cause
    )

    assert (
        updated.execution_analytics[
            "last_failed_agent"
        ]
        == "reasoner"
    )


def test_failure_metadata_is_persisted(
    db_session,
    test_user,
):
    service = FailureRecoveryService(
        db_session
    )

    investigation = create_investigation(
        db_session,
        test_user,
    )

    failure = service.classify(
        agent="investigator",
        exc=TimeoutError(
            "Qdrant timeout"
        ),
        attempt=2,
    )

    decision = service.decide(
        failure
    )

    updated = service.record_failure(
        investigation=investigation,
        failure=failure,
        decision=decision,
    )

    analytics = (
        updated.execution_analytics
    )

    assert "failures" in analytics
    assert len(
        analytics["failures"]
    ) == 1

    failure_data = (
        analytics["failures"][0]
    )

    assert (
        failure_data["agent"]
        == "investigator"
    )

    assert (
        failure_data["attempt"]
        == 2
    )

    assert (
        analytics["retry_counts"][
            "investigator"
        ]
        == 1
    )


def test_recovery_summary_is_json_safe(
    db_session,
):
    service = FailureRecoveryService(
        db_session
    )

    failure = service.classify(
        agent="memory",
        exc=TimeoutError(
            "temporary failure"
        ),
        attempt=1,
    )

    decision = service.decide(
        failure
    )

    summary = (
        service.recovery_summary(
            failure,
            decision,
        )
    )

    assert isinstance(
        summary,
        dict,
    )

    assert (
        summary["agent"]
        == "memory"
    )

    assert (
        summary["failure_type"]
        == "TRANSIENT"
    )

    assert (
        summary["recovery_action"]
        == "RETRY"
    )
