from dataclasses import dataclass


@dataclass(frozen=True)
class AgentCapability:
    """
    Defines the responsibility and tools owned by an agent.
    """

    name: str
    description: str
    tools: tuple[str, ...]


AGENT_CAPABILITIES = {
    "orchestrator": AgentCapability(
        name="orchestrator",
        description=(
            "Coordinates the investigation workflow "
            "and selects the next capability."
        ),
        tools=(
            "route_investigation",
        ),
    ),

    "planner": AgentCapability(
        name="planner",
        description=(
            "Creates and updates the investigation plan."
        ),
        tools=(
            "create_investigation_plan",
        ),
    ),

    "investigator": AgentCapability(
        name="investigator",
        description=(
            "Collects observations from application logs "
            "and system evidence."
        ),
        tools=(
            "search_logs",
        ),
    ),

    "memory": AgentCapability(
        name="memory",
        description=(
            "Retrieves similar historical investigations "
            "using structured and semantic memory."
        ),
        tools=(
            "search_historical_incidents",
            "semantic_memory_search",
        ),
    ),

    "evidence": AgentCapability(
        name="evidence",
        description=(
            "Extracts relevant evidence from investigation "
            "observations."
        ),
        tools=(
            "extract_evidence",
        ),
    ),

    "reasoner": AgentCapability(
        name="reasoner",
        description=(
            "Generates competing root-cause hypotheses "
            "from evidence and historical context."
        ),
        tools=(
            "generate_hypotheses",
        ),
    ),

    "reflector": AgentCapability(
        name="reflector",
        description=(
            "Evaluates evidence sufficiency and determines "
            "whether more investigation is required."
        ),
        tools=(
            "evaluate_evidence_sufficiency",
        ),
    ),

    "validator": AgentCapability(
        name="validator",
        description=(
            "Validates the strongest root-cause hypothesis "
            "against collected evidence."
        ),
        tools=(
            "validate_root_cause",
        ),
    ),

    "memory_writer": AgentCapability(
        name="memory_writer",
        description=(
            "Stores validated investigations as future "
            "historical memory."
        ),
        tools=(
            "store_investigation_memory",
        ),
    ),
}
def get_agent_capability(
    agent_name: str,
) -> AgentCapability:
    """
    Return the capability definition for an agent.
    """

    try:
        return AGENT_CAPABILITIES[
            agent_name
        ]

    except KeyError as exc:
        raise ValueError(
            f"Unknown agent: {agent_name}"
        ) from exc
