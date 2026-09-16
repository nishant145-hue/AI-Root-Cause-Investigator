from typing import Any, Callable

from app.agent.observability import (
    ExecutionTraceCollector,
)


def append_timeline_entries(
    state: dict[str, Any],
    entries: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Append new execution timeline entries to the
    investigation state.
    """

    existing = list(
        state.get(
            "execution_timeline",
            [],
        )
    )

    existing.extend(entries)

    return existing


def propagate_timeline(
    state: dict[str, Any],
    entries: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Return a state update containing the existing
    execution timeline plus newly generated entries.
    """

    return {
        "execution_timeline": append_timeline_entries(
            state,
            entries,
        )
    }


def execute_timeline_operation(
    state: dict[str, Any],
    *,
    agent: str,
    action: str,
    operation: Callable[[], Any],
    attempt: int = 1,
    metadata: dict[str, Any] | None = None,
) -> tuple[Any, dict[str, Any]]:
    """
    Execute a LangGraph operation while recording
    a complete execution trace.

    The existing ExecutionTraceCollector is used so
    LangGraph node telemetry follows the same timing
    model as specialized agents.
    """

    collector = ExecutionTraceCollector()

    trace = collector.start(
        agent=agent,
        action=action,
        attempt=attempt,
        metadata=metadata,
    )

    try:
        result = operation()

        trace.complete(
            status="COMPLETED",
        )

        return (
            result,
            trace.to_dict(),
        )

    except Exception as exc:
        trace.complete(
            status="FAILED",
            error=str(exc),
        )

        raise