from typing import Any

from app.agent.orchestrator import MultiAgentOrchestrator


def multi_agent_node(
    state: dict[str, Any],
    session: Any = None,
) -> dict[str, Any]:
    """
    LangGraph adapter for the multi-agent orchestrator.

    LangGraph owns workflow execution.
    MultiAgentOrchestrator owns agent selection.
    Specialized agents own their capabilities.
    """

    orchestrator = MultiAgentOrchestrator(
        session=session,
    )

    result = orchestrator.run(
        state=state,
    )

    if result is None:
        return {}

    if not isinstance(result, dict):
        raise TypeError(
            "MultiAgentOrchestrator must return a dictionary."
        )

    return result
