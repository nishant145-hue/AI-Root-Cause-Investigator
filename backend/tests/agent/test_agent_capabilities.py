import pytest
from app.agent.agents.capabilities import (
    AGENT_CAPABILITIES,
    get_agent_capability,
)
from app.agent.agents.ownership import (
    agent_owns_tool,
)


def test_investigator_owns_search_logs():

    assert agent_owns_tool(
        "investigator",
        "search_logs",
    )


def test_investigator_does_not_own_memory_search():

    assert not agent_owns_tool(
        "investigator",
        "semantic_memory_search",
    )


def test_memory_owns_historical_search():

    assert agent_owns_tool(
        "memory",
        "search_historical_incidents",
    )


def test_reasoner_does_not_own_log_search():

    assert not agent_owns_tool(
        "reasoner",
        "search_logs",
    )
def test_all_expected_agents_exist():

    expected_agents = {
        "orchestrator",
        "planner",
        "investigator",
        "memory",
        "evidence",
        "reasoner",
        "reflector",
        "validator",
        "memory_writer",
    }

    assert expected_agents == set(
        AGENT_CAPABILITIES.keys()
    )


def test_investigator_owns_log_search():

    capability = get_agent_capability(
        "investigator"
    )

    assert (
        "search_logs"
        in capability.tools
    )


def test_memory_owns_semantic_search():

    capability = get_agent_capability(
        "memory"
    )

    assert (
        "semantic_memory_search"
        in capability.tools
    )


def test_reasoner_owns_hypothesis_generation():

    capability = get_agent_capability(
        "reasoner"
    )

    assert (
        "generate_hypotheses"
        in capability.tools
    )


def test_validator_owns_root_cause_validation():

    capability = get_agent_capability(
        "validator"
    )

    assert (
        "validate_root_cause"
        in capability.tools
    )


def test_unknown_agent_fails():

    with pytest.raises(ValueError):

        get_agent_capability(
            "unknown_agent"
        )
