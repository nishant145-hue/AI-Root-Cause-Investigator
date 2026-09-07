from typing import Any

from app.agent.observability import (
    AgentExecutionTrace,
    UnifiedExecutionTimeline,
)


def build_timeline(
    traces: list[AgentExecutionTrace],
) -> list[dict[str, Any]]:
    """
    Convert execution traces into a unified,
    chronologically ordered timeline.
    """

    timeline = UnifiedExecutionTimeline()

    timeline.add_traces(traces)

    return timeline.to_dict()

def merge_timeline(
    existing: list[dict[str, Any]] | None,
    new_traces: list[AgentExecutionTrace],
) -> list[dict[str, Any]]:
    """
    Merge existing timeline entries with newly
    generated execution traces.
    """

    timeline = UnifiedExecutionTimeline()

    existing = existing or []

    for item in existing:
        timeline_trace = AgentExecutionTrace.from_dict(
            item
        )

        timeline.add_trace(
            timeline_trace
        )

    timeline.add_traces(
        new_traces
    )

    return timeline.to_dict()
