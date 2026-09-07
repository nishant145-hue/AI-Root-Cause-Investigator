from typing import Any


def update_investigation_state(
    state: dict[str, Any],
    **updates: Any,
) -> dict[str, Any]:
    """
    Create a controlled state update for agent handoff.

    The original state is not mutated.
    """

    result = dict(state)

    for key, value in updates.items():
        result[key] = value

    return result
