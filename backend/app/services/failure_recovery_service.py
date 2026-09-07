from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlmodel import Session

from app.agent.failure import (
    AgentFailure,
    AgentFailureType,
    RecoveryAction,
    RecoveryDecision,
    RetryTracker,
    classify_failure,
    determine_recovery,
)
from app.models.investigation import (
    Investigation,
    InvestigationStatus,
)


class FailureRecoveryService:
    """
    Centralized failure and recovery handling for investigations.

    Responsibilities:
    - classify agent failures
    - determine recovery actions
    - update in-memory agent state
    - persist failure information
    - preserve partial investigation results
    - maintain retry metadata
    """

    def __init__(
        self,
        session: Session,
        *,
        max_retries: int = 2,
    ) -> None:
        self.session = session
        self.max_retries = max(
            0,
            int(max_retries),
        )

        self.retry_tracker = RetryTracker()

    # ============================================================
    # Failure classification
    # ============================================================

    def classify(
        self,
        *,
        agent: str,
        exc: Exception,
        attempt: int = 1,
    ) -> AgentFailure:
        """
        Convert an exception into a normalized AgentFailure.
        """

        return classify_failure(
            agent=agent,
            exc=exc,
            attempt=max(1, int(attempt)),
        )

    # ============================================================
    # Recovery decision
    # ============================================================

    def decide(
        self,
        failure: AgentFailure,
    ) -> RecoveryDecision:
        """
        Determine whether the investigation should retry,
        reroute, fallback, or stop.
        """

        return determine_recovery(
            failure=failure,
            max_retries=self.max_retries,
        )

    # ============================================================
    # Record failure
    # ============================================================

    def record_failure(
        self,
        *,
        investigation: Investigation,
        failure: AgentFailure,
        decision: RecoveryDecision,
        partial_state: dict[str, Any] | None = None,
    ) -> Investigation:
        """
        Persist failure information without destroying
        previously completed investigation results.
        """

        partial_state = (
            partial_state
            if isinstance(partial_state, dict)
            else {}
        )

        # --------------------------------------------------------
        # Retry tracking
        # --------------------------------------------------------

        attempt = max(
            1,
            int(failure.attempt),
        )

        # Keep retry tracking independent per agent.
        if failure.agent:
            self.retry_tracker.record_failure(
                failure.agent
            )

        # --------------------------------------------------------
        # Preserve existing analytics
        # --------------------------------------------------------

        analytics = investigation.execution_analytics

        if not isinstance(analytics, dict):
            analytics = {}

        analytics = dict(analytics)

        # --------------------------------------------------------
        # Failure metadata
        # --------------------------------------------------------

        failure_data = {
            "agent": failure.agent,
            "failure_type": failure.failure_type.value,
            "message": failure.message,
            "attempt": attempt,
            "recovery_action": decision.action.value,
            "recovery_reason": decision.reason,
            "next_agent": decision.next_agent,
            "recorded_at": datetime.now(
                timezone.utc
            ).isoformat(),
        }

        # Existing failure history.
        existing_failures = analytics.get(
            "failures",
            [],
        )

        if not isinstance(
            existing_failures,
            list,
        ):
            existing_failures = []

        existing_failures = list(
            existing_failures
        )

        existing_failures.append(
            failure_data
        )

        analytics["failures"] = (
            existing_failures
        )

        # --------------------------------------------------------
        # Retry metadata
        # --------------------------------------------------------

        retry_counts = analytics.get(
            "retry_counts",
            {},
        )

        if not isinstance(
            retry_counts,
            dict,
        ):
            retry_counts = {}

        retry_counts = dict(retry_counts)

        agent_name = failure.agent or "unknown"

        retry_counts[agent_name] = max(
            int(
                retry_counts.get(
                    agent_name,
                    0,
                )
                or 0
            ),
            max(
                0,
                attempt - 1,
            ),
        )

        analytics["retry_counts"] = (
            retry_counts
        )

        analytics["last_failed_agent"] = (
            agent_name
        )

        analytics["recovery_action"] = (
            decision.action.value
        )

        analytics["failure_type"] = (
            failure.failure_type.value
        )

        analytics["last_failure_at"] = (
            failure_data["recorded_at"]
        )

        # --------------------------------------------------------
        # Preserve partial state
        # --------------------------------------------------------

        if partial_state:
            existing_partial = analytics.get(
                "partial_state",
                {},
            )

            if not isinstance(
                existing_partial,
                dict,
            ):
                existing_partial = {}

            merged_partial = dict(
                existing_partial
            )

            merged_partial.update(
                partial_state
            )

            analytics["partial_state"] = (
                merged_partial
            )

        investigation.execution_analytics = (
            analytics
        )

        # --------------------------------------------------------
        # Failed component
        # --------------------------------------------------------

        investigation.failed_component = (
            agent_name
        )

        # --------------------------------------------------------
        # Recovery status
        # --------------------------------------------------------

        if decision.action == RecoveryAction.STOP:
            investigation.status = (
                InvestigationStatus.FAILED
            )

        elif decision.action in (
            RecoveryAction.RETRY,
            RecoveryAction.FALLBACK,
            RecoveryAction.REROUTE,
        ):
            # The investigation remains recoverable.
            investigation.status = (
                InvestigationStatus.IN_PROGRESS
            )

        # --------------------------------------------------------
        # Preserve existing results
        # --------------------------------------------------------

        self._preserve_partial_results(
            investigation,
            partial_state,
        )

        self.session.add(
            investigation
        )

        self.session.commit()

        self.session.refresh(
            investigation
        )

        return investigation

    # ============================================================
    # Partial result preservation
    # ============================================================

    @staticmethod
    def _preserve_partial_results(
        investigation: Investigation,
        partial_state: dict[str, Any],
    ) -> None:
        """
        Preserve completed work already produced by previous
        agents.

        Existing values are never overwritten by None.
        """

        if not partial_state:
            return

        field_mapping = {
            "summary": "summary",
            "root_cause": "root_cause",
            "failed_component": "failed_component",
            "severity": "severity",
            "confidence": "confidence",
            "additional_notes": "additional_notes",
        }

        for source_key, target_key in (
            field_mapping.items()
        ):
            value = partial_state.get(
                source_key
            )

            if value is None:
                continue

            # Never replace useful existing information
            # with an empty value.
            if isinstance(value, str):
                if not value.strip():
                    continue

            setattr(
                investigation,
                target_key,
                value,
            )

    # ============================================================
    # Retry check
    # ============================================================

    def can_retry(
        self,
        *,
        agent: str,
    ) -> bool:
        """
        Return whether another attempt is allowed.
        """

        return self.retry_tracker.can_retry(
            agent
        )

    # ============================================================
    # Reset after successful recovery
    # ============================================================

    def reset_agent(
        self,
        *,
        agent: str,
    ) -> None:
        """
        Clear retry tracking after successful recovery.
        """

        self.retry_tracker.reset(
            agent
        )

    # ============================================================
    # Recovery status
    # ============================================================

    @staticmethod
    def is_terminal(
        decision: RecoveryDecision,
    ) -> bool:
        """
        Return True when no further recovery should occur.
        """

        return decision.action == (
            RecoveryAction.STOP
        )

    # ============================================================
    # Safe recovery summary
    # ============================================================

    @staticmethod
    def recovery_summary(
        failure: AgentFailure,
        decision: RecoveryDecision,
    ) -> dict[str, Any]:
        """
        Return a JSON-safe representation useful for
        logging, analytics, and observability.
        """

        return {
            "agent": failure.agent,
            "failure_type": (
                failure.failure_type.value
            ),
            "message": failure.message,
            "attempt": failure.attempt,
            "recovery_action": (
                decision.action.value
            ),
            "reason": decision.reason,
            "next_agent": decision.next_agent,
        }
