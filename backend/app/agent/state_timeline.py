from typing import Any


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
