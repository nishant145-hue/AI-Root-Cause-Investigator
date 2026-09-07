from typing import Any

from app.agent.agents.base import BaseAgent
from app.agent.agents.investigator import InvestigatorAgent
from app.agent.agents.memory import MemoryAgent
from app.agent.agents.reasoner import ReasonerAgent
from app.agent.agents.validator import ValidatorAgent
from app.agent.failure import (
    AgentFailure,
    RecoveryAction,
    RetryPolicy,
    RetryTracker,
    determine_recovery,
)
from app.agent.failure_telemetry import (
    FailureTelemetryCollector,
)
from app.agent.observability import (
    ExecutionTraceCollector,
    UnifiedExecutionTimeline,
)
from app.agent.state_timeline import (
    propagate_timeline,
)


class MultiAgentOrchestrator(BaseAgent):
    """
    Coordinates specialized investigation agents.

    The orchestrator owns workflow coordination only.

    It does not directly:
    - search logs
    - retrieve memory
    - generate hypotheses
    - validate root causes
    """

    name = "orchestrator"

    role = (
        "Coordinate specialized investigation agents "
        "and route work through the investigation lifecycle."
    )

    def __init__(self) -> None:
        super().__init__(
            capabilities=[
                "route_investigation",
            ]
        )

        self.trace_collector = (
            ExecutionTraceCollector()
        )

        self.failure_telemetry = (
            FailureTelemetryCollector()
        )

        self.investigator = InvestigatorAgent()
        self.memory = MemoryAgent()
        self.reasoner = ReasonerAgent()
        self.validator = ValidatorAgent()
        self.retry_tracker = RetryTracker(
            RetryPolicy(max_retries=2)
        )

    def route(
        self,
        state: dict[str, Any],
    ) -> str:
        """
        Determine which specialized agent should
        handle the next stage.

        Routing decisions are recorded in the
        execution trace.
        """

        self.require_capability(
            "route_investigation"
        )

        status = state.get(
            "investigation_status",
            "STARTING",
        )

        trace = self.trace_collector.start(
            agent=self.name,
            action="route_investigation",
            attempt=1,
            metadata={
                "investigation_status": status,
            },
        )

        try:

            if status == "PLANNING":
                next_agent = "investigator"

            elif status in {
                "MORE_EVIDENCE_REQUIRED",
                "REPLANNING",
            }:
                next_agent = "planner"

            elif status in {
                "STARTING",
                "INVESTIGATING",
                "MORE_EVIDENCE_REQUIRED",
            }:
                next_agent = "investigator"

            elif status in {
                "EVIDENCE_COLLECTED",
                "MEMORY_REQUIRED",
            }:
                next_agent = "memory"

            elif status in {
                "MEMORY_RETRIEVED",
                "REASONING",
            }:
                next_agent = "reasoner"

            elif status in {
                "READY_FOR_VALIDATION",
                "VALIDATING",
            }:
                next_agent = "validator"

            elif status == "ROOT_CAUSE_VALIDATED":
                next_agent = "completed"

            else:
                next_agent = "investigator"

            trace.metadata[
                "next_agent"
            ] = (
                "memory_writer"
                if next_agent == "completed"
                else next_agent
            )
            trace.complete(
                status="COMPLETED"
            )

            return next_agent

        except Exception as exc:

            trace.complete(
                status="FAILED",
                error=str(exc),
            )

            raise

    def decide(
        self,
        state: dict[str, Any],
    ) -> str:
        """
        Decide which specialized agent should handle
        the next investigation stage.

        This is the public orchestration decision interface.
        """

        self.require_capability(
            "route_investigation"
        )

        status = state.get(
            "investigation_status",
            "STARTING",
        )

        # -----------------------------------------------------
        # Initial investigation
        # -----------------------------------------------------

        if status == "STARTING":
            return "planner"

        # -----------------------------------------------------
        # Planner has produced an action
        # -----------------------------------------------------

        if status == "PLANNING":
            return "investigator"

        # -----------------------------------------------------
        # Dynamic re-planning
        # -----------------------------------------------------

        if status in {
            "MORE_EVIDENCE_REQUIRED",
            "REPLANNING",
        }:
            return "planner"

        # -----------------------------------------------------
        # Investigation completed
        # -----------------------------------------------------

        if status in {
            "INVESTIGATING",
            "EVIDENCE_COLLECTED",
        }:
            return "memory"

        # -----------------------------------------------------
        # Memory retrieved
        # -----------------------------------------------------

        if status in {
            "MEMORY_REQUIRED",
            "MEMORY_RETRIEVED",
        }:
            return "reasoner"

        # -----------------------------------------------------
        # Reasoning completed
        # -----------------------------------------------------

        if status == "REASONING":
            return "validator"

        # -----------------------------------------------------
        # Validation
        # -----------------------------------------------------

        if status in {
            "READY_FOR_VALIDATION",
            "VALIDATING",
        }:
            return "validator"

        # -----------------------------------------------------
        # Investigation finished
        # -----------------------------------------------------

        if status == "ROOT_CAUSE_VALIDATED":
            return "memory_writer"

        # -----------------------------------------------------
        # Safe fallback
        # -----------------------------------------------------

        return "planner"

    def run(
        self,
        state: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Return orchestration information.

        Specialized agents perform the actual work.

        The orchestrator's logical route may return
        ``completed`` when the investigation is finished.
        For execution purposes, LangGraph continues to
        the memory_writer node.
        """

        self.require_capability(
            "route_investigation"
        )

        next_agent = self.route(state)

        execution_agent = (
            "memory_writer"
            if next_agent == "completed"
            else next_agent
        )

        # Update the most recent routing trace so that
        # the execution-facing destination matches the
        # actual LangGraph node.
        traces = self.trace_collector.traces()

        if traces:
            traces[-1].metadata[
                "next_agent"
            ] = execution_agent

        return {
            "agent": self.name,
            "status": "ROUTING",
            "next_agent": execution_agent,
        }

    def recover(
        self,
        failure: AgentFailure,
    ) -> dict[str, Any]:
        """
        Decide how the investigation should recover
        from an agent failure.
        """

        self.require_capability(
            "route_investigation"
        )

        decision = determine_recovery(
            failure
        )

        result = {
            "agent": self.name,
            "failure_agent": failure.agent,
            "failure_type": failure.failure_type.value,
            "recovery_action": decision.action.value,
            "recovery_reason": decision.reason,
        }

        if decision.next_agent:
            result["next_agent"] = decision.next_agent

        return result

    def handle_agent_failure(
        self,
        agent: str,
        failure_type: str,
        message: str,
    ) -> dict[str, Any]:
        """
        Handle an agent failure and determine
        the appropriate recovery action.
        """

        self.require_capability(
            "route_investigation"
        )

        attempt = self.retry_tracker.record_failure(
            agent
        )

        try:
            from app.agent.failure import (
                AgentFailureType,
            )

            normalized_type = AgentFailureType(
                failure_type
            )

        except ValueError:
            normalized_type = (
                AgentFailureType.CRITICAL
            )

        failure = AgentFailure(
            agent=agent,
            failure_type=normalized_type,
            message=message,
            attempt=attempt,
        )

        decision = determine_recovery(
            failure,
            max_retries=(
                self.retry_tracker.policy.max_retries
            ),
        )

        if hasattr(
            self,
            "failure_telemetry",
        ):

            self.failure_telemetry.record_failure(
                agent_name=agent,
                failure_type=failure_type,
                message=message,
                attempt=attempt,
                metadata={
                "source": "orchestrator",
                "recovery_action": (
                    decision.action.value
                ),
                "next_agent": (
                    decision.next_agent
                ),
            },
        )

            if decision.action == RecoveryAction.RETRY:

                self.failure_telemetry.record_retry(
                agent_name=agent,
                attempt=attempt,
                recovery_action=(
                    decision.action.value
                ),
                reason=decision.reason,
                failure_type=failure_type,
                metadata={
                    "source": "orchestrator",
                    "next_agent": (
                        decision.next_agent
                    ),
                },
            )

        result = {
            "agent": self.name,
            "status": "AGENT_FAILURE",
            "failed_agent": agent,
            "failure_type": (
                failure.failure_type.value
            ),
            "attempt": attempt,
            "recovery_action": (
                decision.action.value
            ),
            "recovery_reason": decision.reason,
        }

        if decision.next_agent:
            result["next_agent"] = (
                decision.next_agent
            )

        return result

    def mark_agent_success(
        self,
        agent: str,
    ) -> None:
        """
        Clear retry state after successful execution.
        """

        self.retry_tracker.reset(
            agent
        )

    def handle_state_failure(
        self,
        state: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Handle an agent failure using retry counts
        stored in shared investigation state.
        """

        self.require_capability(
            "route_investigation"
        )

        failed_agent = state.get(
            "last_failed_agent"
        )

        failure_type = state.get(
            "last_failure_type",
            "CRITICAL",
    )

        message = state.get(
            "last_failure_message",
            "Unknown agent failure.",
        )

        if not failed_agent:
            return {
                "recovery_action": "STOP",
                "investigation_status": "FAILED",
            }

        retry_counts = dict(
            state.get(
                "retry_counts",
                {},
            )
        )

        attempt = (
            retry_counts.get(
                failed_agent,
                0,
            )
            + 1
        )

        retry_counts[
            failed_agent
        ] = attempt

        from app.agent.failure import (
            AgentFailure,
            AgentFailureType,
            determine_recovery,
        )

        try:
            failure_enum = AgentFailureType(
                failure_type
            )
        except ValueError:
            failure_enum = (
                AgentFailureType.CRITICAL
            )

        failure = AgentFailure(
            agent=failed_agent,
            failure_type=failure_enum,
            message=message,
            attempt=attempt,
        )

        decision = determine_recovery(
            failure,
            max_retries=(
                self.retry_tracker.policy.max_retries
            ),
        )

        if hasattr(
            self,
            "failure_telemetry",
        ):

            self.failure_telemetry.record_failure(
                agent_name=failed_agent,
                failure_type=failure_type,
                message=message,
                attempt=attempt,
                investigation_id=state.get(
                    "investigation_id"
                ),
                metadata={
                    "source": "state_failure",
                    "recovery_action": (
                        decision.action.value
                    ),
                    "next_agent": (
                        decision.next_agent
                    ),
                },
            )

            if decision.action == RecoveryAction.RETRY:

                self.failure_telemetry.record_retry(
                agent_name=failed_agent,
                attempt=attempt,
                recovery_action=(
                    decision.action.value
                ),
                reason=decision.reason,
                investigation_id=state.get(
                    "investigation_id"
                ),
                failure_type=failure_type,
                metadata={
                    "source": "state_failure",
                    "next_agent": (
                        decision.next_agent
                    ),
                },
            )

        update = {
            "retry_counts": retry_counts,
            "recovery_action": (
                decision.action.value
            ),
        }

        if decision.action == RecoveryAction.RETRY:
            update[
                "investigation_status"
            ] = "RETRYING"

        elif decision.action == RecoveryAction.REROUTE:
            update[
                "investigation_status"
            ] = "REPLANNING"

        else:
            update[
                "investigation_status"
            ] = "FAILED"

        return update

    def execution_traces(
        self,
    ) -> list[dict[str, Any]]:
        """
        Return serialized orchestrator execution traces.
        """

        return self.trace_collector.to_dict()

    def build_execution_timeline(
        self,
    ) -> UnifiedExecutionTimeline:
        """
        Build one unified execution timeline from
        all specialized agents owned by the orchestrator.
        """

        timeline = UnifiedExecutionTimeline()

        timeline.add_traces(
            self.trace_collector.traces()
        )

        timeline.add_traces(
            self.investigator.trace_collector.traces()
        )

        timeline.add_traces(
            self.memory.trace_collector.traces()
        )

        timeline.add_traces(
            self.reasoner.trace_collector.traces()
        )

        timeline.add_traces(
            self.validator.trace_collector.traces()
        )

        return timeline

    def execution_timeline(
        self,
    ) -> list[dict[str, Any]]:
        """
        Return the complete serialized investigation
        execution timeline.
        """

        timeline = (
            self.build_execution_timeline()
        )

        return timeline.to_dict()

    def execution_timeline_summary(
        self,
    ) -> dict[str, Any]:
        """
        Return summary statistics for the complete
        investigation execution.
        """

        timeline = (
            self.build_execution_timeline()
        )

        return timeline.summary()

    def execution_timeline_state(
        self,
    ) -> list[dict[str, Any]]:
        """
        Return the complete execution timeline in
        a LangGraph-state-compatible format.
        """

        return (
            self.build_execution_timeline()
            .to_dict()
        )


    def failure_telemetry_snapshot(
        self,
    ) -> dict[str, Any]:
        """
        Return failure/retry/timeout telemetry.
        """

        return self.failure_telemetry.snapshot()


    def failure_telemetry_aggregate(
        self,
    ) -> dict[str, Any]:
        """
        Return aggregate failure/retry/timeout telemetry.
        """

        return self.failure_telemetry.aggregate()


    def reset_failure_telemetry(
        self,
    ) -> None:
        """
        Reset failure/retry/timeout telemetry.
        """

        self.failure_telemetry.reset()
