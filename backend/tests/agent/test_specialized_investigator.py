import pytest

from app.agent.agents.investigator import (
    InvestigatorAgent,
)


def test_investigator_agent_name():
    agent = InvestigatorAgent()

    assert agent.name == "investigator"


def test_investigator_agent_role():
    agent = InvestigatorAgent()

    assert "logs" in agent.role.lower()


def test_investigator_owns_search_logs():
    agent = InvestigatorAgent()

    assert agent.owns_capability(
        "search_logs"
    )


def test_investigator_does_not_own_memory_search():
    agent = InvestigatorAgent()

    assert not agent.owns_capability(
        "search_historical_incidents"
    )


def test_investigator_rejects_unowned_capability():
    agent = InvestigatorAgent()

    with pytest.raises(PermissionError):
        agent.require_capability(
            "search_historical_incidents"
        )


def test_investigator_run():
    agent = InvestigatorAgent()

    result = agent.run({})

    assert result["agent"] == "investigator"

    assert (
        "search_logs"
        in result["capabilities"]
    )
