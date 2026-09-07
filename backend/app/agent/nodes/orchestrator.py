from typing import Any

from app.agent.agents.orchestrator import (
    MultiAgentOrchestrator,
)
from app.agent.state_timeline import (
    propagate_timeline,
)


def orchestrator_node(
    state: dict[str, Any],
) -> dict[str, Any]:
    """
    LangGraph adapter for the MultiAgentOrchestrator.

    The orchestrator decides which specialized agent
    should handle the next stage.

    It does not perform investigation work itself.
    """

    orchestrator = MultiAgentOrchestrator()

    result = orchestrator.run(
        state=state,
    )

    new_timeline = (
        orchestrator.execution_timeline_state()
    )

    return {
        "next_agent": result["next_agent"],
        "execution_timeline": (
            propagate_timeline(
                state,
                new_timeline,
            )["execution_timeline"]
        ),
        "current_step": (
            f"Orchestrator selected "
            f"{result['next_agent']} agent"
        ),
    }
