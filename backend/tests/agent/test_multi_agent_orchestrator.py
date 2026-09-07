from app.agent.agents.orchestrator import (
    MultiAgentOrchestrator,
)


def test_orchestrator_name():

    agent = MultiAgentOrchestrator()

    assert agent.name == "orchestrator"


def test_orchestrator_owns_routing():

    agent = MultiAgentOrchestrator()

    assert agent.owns_capability(
        "route_investigation"
    )


def test_orchestrator_does_not_own_log_search():

    agent = MultiAgentOrchestrator()

    assert not agent.owns_capability(
        "search_logs"
    )


def test_orchestrator_does_not_own_memory_search():

    agent = MultiAgentOrchestrator()

    assert not agent.owns_capability(
        "semantic_memory_search"
    )


def test_orchestrator_does_not_own_hypothesis_generation():

    agent = MultiAgentOrchestrator()

    assert not agent.owns_capability(
        "generate_hypotheses"
    )


def test_orchestrator_does_not_own_validation():

    agent = MultiAgentOrchestrator()

    assert not agent.owns_capability(
        "validate_root_cause"
    )


def test_orchestrator_has_specialized_agents():

    agent = MultiAgentOrchestrator()

    assert agent.investigator.name == (
        "investigator"
    )

    assert agent.memory.name == "memory"

    assert agent.reasoner.name == "reasoner"

    assert agent.validator.name == "validator"


def test_orchestrator_routes_to_investigator():

    agent = MultiAgentOrchestrator()

    state = {
        "investigation_status": "STARTING",
    }

    assert agent.route(state) == (
        "investigator"
    )


def test_orchestrator_routes_to_memory():

    agent = MultiAgentOrchestrator()

    state = {
        "investigation_status": "EVIDENCE_COLLECTED",
    }

    assert agent.route(state) == "memory"


def test_orchestrator_routes_to_reasoner():

    agent = MultiAgentOrchestrator()

    state = {
        "investigation_status": "MEMORY_RETRIEVED",
    }

    assert agent.route(state) == "reasoner"


def test_orchestrator_routes_to_validator():

    agent = MultiAgentOrchestrator()

    state = {
        "investigation_status": "READY_FOR_VALIDATION",
    }

    assert agent.route(state) == "validator"


def test_orchestrator_stops_after_validation():

    agent = MultiAgentOrchestrator()

    state = {
        "investigation_status": (
            "ROOT_CAUSE_VALIDATED"
        ),
    }

    assert agent.route(state) == "completed"


def test_orchestrator_run():

    agent = MultiAgentOrchestrator()

    state = {
        "investigation_status": "STARTING",
    }

    result = agent.run(state)

    assert result["agent"] == "orchestrator"

    assert result["status"] == "ROUTING"

    assert result["next_agent"] == "investigator"

def test_orchestrator_routes_replanning_to_planner():

    orchestrator = MultiAgentOrchestrator()

    state = {
        "investigation_status": "REPLANNING",
    }

    assert (
        orchestrator.route(state)
        == "planner"
    )
