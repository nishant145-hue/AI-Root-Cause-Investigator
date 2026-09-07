from abc import ABC, abstractmethod
from typing import Any

from app.agent.observability import (
    ExecutionTraceCollector,
)


class BaseAgent(ABC):
    """
    Base class for all specialized investigation agents.

    Every agent has:
    - a name
    - a role
    - a defined set of capabilities
    """

    name: str = ""
    role: str = ""

    def __init__(
        self,
        capabilities: list[str] | None = None,
    ) -> None:
        self.capabilities = capabilities or []

        self.trace_collector = (
            ExecutionTraceCollector()
        )
    @abstractmethod
    def run(
        self,
        state: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Execute the agent against the current investigation state.
        """
        raise NotImplementedError

    def owns_capability(
        self,
        capability: str,
    ) -> bool:
        """
        Check whether this agent owns a capability.
        """

        return capability in self.capabilities

    def require_capability(
        self,
        capability: str,
    ) -> None:
        """
        Ensure this agent owns the requested capability.
        """

        if not self.owns_capability(capability):
            raise PermissionError(
                f"Agent '{self.name}' does not own "
                f"capability '{capability}'."
            )

    def start_trace(
        self,
        action: str,
        attempt: int = 1,
        metadata: dict[str, Any] | None = None,
    ):
        """
        Start an execution trace for this agent.
        """

        return self.trace_collector.start(
            agent=self.name,
            action=action,
            attempt=attempt,
            metadata=metadata,
        )


    def execution_traces(
        self,
    ) -> list[dict[str, Any]]:
        """
        Return serialized execution traces.
        """

        return self.trace_collector.to_dict()


    def execution_summary(
        self,
    ) -> dict[str, Any]:
        """
        Return execution statistics.
        """

        return self.trace_collector.summary()
    def trace_execution(
        self,
        action: str,
        attempt: int,
        operation,
        metadata: dict[str, Any] | None = None,
    ):
        """
        Execute an operation while recording its
        success/failure and attempt number.

        The operation itself is responsible for
        performing the actual agent work.
        """

        trace = self.start_trace(
            action=action,
            attempt=attempt,
            metadata=metadata,
        )

        try:
            result = operation()

            trace.complete(
                status="COMPLETED"
            )

            return result

        except Exception as exc:

            trace.complete(
                status="FAILED",
                error=str(exc),
            )

            raise

    def add_traces_to_timeline(
        self,
        timeline,
    ) -> None:
        """
        Add this agent's execution traces to
        a unified investigation timeline.
        """

        timeline.add_traces(
            self.trace_collector.traces()
        )

    def timeline_entries(
        self,
    ) -> list[dict[str, Any]]:
        """
        Return this agent's execution traces as
        serializable timeline entries.
        """

        return [
            trace.to_dict()
            for trace in self.trace_collector.traces()
        ]
