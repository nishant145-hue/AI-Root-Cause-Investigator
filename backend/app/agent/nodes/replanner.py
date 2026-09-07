from typing import Any

from app.agent.nodes.planner import planner_node


def replanner_node(
    state: dict[str, Any],
) -> dict[str, Any]:
    """
    Re-plan the investigation when the current
    evidence is insufficient.
    """

    result = planner_node(state)

    return {
        **result,
        "investigation_status": "REPLANNING",
    }
