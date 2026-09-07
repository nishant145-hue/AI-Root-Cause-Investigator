from app.agent.agents.orchestrator import (
    MultiAgentOrchestrator,
)


def test_orchestrator_retries_transient_failure():

    orchestrator = MultiAgentOrchestrator()

    result = orchestrator.handle_agent_failure(
        agent="memory",
        failure_type="TRANSIENT",
        message="Qdrant timeout",
    )

    assert result["status"] == "AGENT_FAILURE"
    assert result["failed_agent"] == "memory"
    assert result["attempt"] == 1
    assert result["recovery_action"] == "RETRY"
    assert result["next_agent"] == "memory"


def test_orchestrator_reroutes_after_retry_limit():

    orchestrator = MultiAgentOrchestrator()

    first = orchestrator.handle_agent_failure(
        agent="memory",
        failure_type="TRANSIENT",
        message="Qdrant timeout",
    )

    second = orchestrator.handle_agent_failure(
        agent="memory",
        failure_type="TRANSIENT",
        message="Qdrant timeout",
    )

    third = orchestrator.handle_agent_failure(
        agent="memory",
        failure_type="TRANSIENT",
        message="Qdrant timeout",
    )

    assert first["recovery_action"] == "RETRY"
    assert second["recovery_action"] == "RETRY"
    assert third["recovery_action"] == "REROUTE"


def test_orchestrator_reroutes_recoverable_failure():

    orchestrator = MultiAgentOrchestrator()

    result = orchestrator.handle_agent_failure(
        agent="reasoner",
        failure_type="RECOVERABLE",
        message="Invalid LLM response",
    )

    assert result["recovery_action"] == "REROUTE"


def test_orchestrator_stops_critical_failure():

    orchestrator = MultiAgentOrchestrator()

    result = orchestrator.handle_agent_failure(
        agent="validator",
        failure_type="CRITICAL",
        message="Invalid investigation state",
    )

    assert result["recovery_action"] == "STOP"


def test_orchestrator_tracks_agents_independently():

    orchestrator = MultiAgentOrchestrator()

    memory = orchestrator.handle_agent_failure(
        agent="memory",
        failure_type="TRANSIENT",
        message="Qdrant timeout",
    )

    reasoner = orchestrator.handle_agent_failure(
        agent="reasoner",
        failure_type="TRANSIENT",
        message="LLM timeout",
    )

    assert memory["attempt"] == 1
    assert reasoner["attempt"] == 1


def test_orchestrator_resets_agent_after_success():

    orchestrator = MultiAgentOrchestrator()

    result = orchestrator.handle_agent_failure(
        agent="memory",
        failure_type="TRANSIENT",
        message="Qdrant timeout",
    )

    assert result["attempt"] == 1

    orchestrator.mark_agent_success(
        "memory"
    )

    result = orchestrator.handle_agent_failure(
        agent="memory",
        failure_type="TRANSIENT",
        message="Qdrant timeout again",
    )

    assert result["attempt"] == 1
