from typing import Any

from app.agent.execution_analytics import (
    InvestigationExecutionAnalytics,
)
from app.agent.state import InvestigationState


def analytics_node(
    state: InvestigationState,
) -> dict[str, Any]:
    """
    Calculate analytics from the current investigation
    execution timeline and persist them into LangGraph state.
    """

    timeline = list(
        state.get(
            "execution_timeline",
            [],
        )
    )

    analytics = (
        InvestigationExecutionAnalytics(
            timeline
        )
    )

    return {
        "execution_analytics": (
            analytics.unified_summary()
        )
    }
