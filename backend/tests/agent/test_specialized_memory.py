import pytest

from app.agent.agents.memory import MemoryAgent


def test_memory_agent_name():
    agent = MemoryAgent()

    assert agent.name == "memory"


def test_memory_agent_role():
    agent = MemoryAgent()

    assert "historical" in agent.role.lower()


def test_memory_owns_historical_search():
    agent = MemoryAgent()

    assert agent.owns_capability(
        "search_historical_incidents"
    )


def test_memory_owns_semantic_search():
    agent = MemoryAgent()

    assert agent.owns_capability(
        "semantic_memory_search"
    )


def test_memory_does_not_own_log_search():
    agent = MemoryAgent()

    assert not agent.owns_capability(
        "search_logs"
    )


def test_memory_rejects_unowned_capability():
    agent = MemoryAgent()

    with pytest.raises(PermissionError):
        agent.require_capability(
            "search_logs"
        )


def test_memory_run():
    agent = MemoryAgent()

    result = agent.run({})

    assert result["agent"] == "memory"

    assert (
        "search_historical_incidents"
        in result["capabilities"]
    )

    assert (
        "semantic_memory_search"
        in result["capabilities"]
    )
