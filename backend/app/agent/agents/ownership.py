from app.agent.agents.capabilities import (
    get_agent_capability,
)


def agent_owns_tool(
    agent_name: str,
    tool_name: str,
) -> bool:
    """
    Check whether an agent owns a specific tool.
    """

    capability = get_agent_capability(
        agent_name
    )

    return tool_name in capability.tools
