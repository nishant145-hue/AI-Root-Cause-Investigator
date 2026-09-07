from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class AgentExecutionTrace:
    """
    Represents one execution of a specialized agent.
    """

    agent: str
    action: str
    status: str

    started_at: datetime
    completed_at: datetime | None = None

    duration_ms: float | None = None

    attempt: int = 1

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    error: str | None = None

    def complete(
        self,
        status: str = "COMPLETED",
        error: str | None = None,
    ) -> None:
        """
        Mark the execution as completed.
        """

        self.completed_at = (
            datetime.now(timezone.utc)
        )

        self.status = status
        self.error = error

        self.duration_ms = (
            self.completed_at
            - self.started_at
        ).total_seconds() * 1000

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize this execution trace.
        """

        return {
            "agent": self.agent,
            "action": self.action,
            "status": self.status,
            "started_at": (
                self.started_at.isoformat()
            ),
            "completed_at": (
                self.completed_at.isoformat()
                if self.completed_at
                else None
            ),
            "duration_ms": self.duration_ms,
            "attempt": self.attempt,
            "metadata": self.metadata,
            "error": self.error,
        }


class ExecutionTraceCollector:
    """
    Collects execution traces for an investigation.
    """

    def __init__(self) -> None:
        self._traces: list[
            AgentExecutionTrace
        ] = []

    def start(
        self,
        agent: str,
        action: str,
        attempt: int = 1,
        metadata: dict[str, Any] | None = None,
    ) -> AgentExecutionTrace:
        """
        Start tracking an agent execution.
        """

        trace = AgentExecutionTrace(
            agent=agent,
            action=action,
            status="RUNNING",
            started_at=(
                datetime.now(timezone.utc)
            ),
            attempt=attempt,
            metadata=metadata or {},
        )

        self._traces.append(trace)

        return trace

    def traces(
        self,
    ) -> list[AgentExecutionTrace]:
        """
        Return all recorded traces.
        """

        return list(self._traces)

    def summary(self) -> dict:
        traces = self._traces

        total_executions = len(
            traces
        )

        completed_executions = sum(
            1
            for trace in traces
            if trace.status == "COMPLETED"
        )

        failed_executions = sum(
            1
            for trace in traces
            if trace.status == "FAILED"
        )

        retries = sum(
            1
            for trace in traces
            if trace.attempt > 1
        )

        total_duration_ms = sum(
            trace.duration_ms or 0
            for trace in traces
        )

        return {
            "total_executions": total_executions,
            "completed_executions": (
                completed_executions
            ),
            "failed_executions": (
                failed_executions
            ),
            "retries": retries,
            "total_duration_ms": (
                total_duration_ms
            ),
        }

    def to_dict(
        self,
    ) -> list[dict[str, Any]]:
        """
        Serialize all execution traces.
        """

        return [
            trace.to_dict()
            for trace in self._traces
        ]

    def clear(self) -> None:
        """
        Clear all execution traces.
        """

        self._traces.clear()

class UnifiedExecutionTimeline:
    """
    Combines execution traces from multiple agents
    into one chronological investigation timeline.
    """

    def __init__(self) -> None:
        self._traces: list[
            AgentExecutionTrace
        ] = []

    def add_trace(
        self,
        trace: AgentExecutionTrace,
    ) -> None:
        """
        Add one agent execution trace.
        """

        self._traces.append(trace)

    def add_traces(
        self,
        traces: list[AgentExecutionTrace],
    ) -> None:
        """
        Add multiple execution traces.
        """

        self._traces.extend(traces)

    def traces(
        self,
    ) -> list[AgentExecutionTrace]:
        """
        Return all traces ordered chronologically.
        """

        return sorted(
            self._traces,
            key=lambda trace: trace.started_at,
        )

    def to_dict(
        self,
    ) -> list[dict[str, Any]]:
        """
        Serialize the unified timeline.
        """

        return [
            trace.to_dict()
            for trace in self.traces()
        ]

    def summary(self) -> dict[str, Any]:
        """
        Return summary statistics for the
        complete investigation timeline.
        """

        traces = self.traces()

        total_executions = len(traces)

        completed_executions = sum(
            1
            for trace in traces
            if trace.status == "COMPLETED"
        )

        failed_executions = sum(
            1
            for trace in traces
            if trace.status == "FAILED"
        )

        retries = sum(
            1
            for trace in traces
            if trace.attempt > 1
        )

        total_duration_ms = sum(
            trace.duration_ms or 0
            for trace in traces
        )

        agents = sorted(
            {
                trace.agent
                for trace in traces
            }
        )

        return {
            "total_executions": (
                total_executions
            ),
            "completed_executions": (
                completed_executions
            ),
            "failed_executions": (
                failed_executions
            ),
            "retries": retries,
            "total_duration_ms": (
                total_duration_ms
            ),
            "agents": agents,
        }

    def clear(self) -> None:
        """
        Clear the unified timeline.
        """

        self._traces.clear()
