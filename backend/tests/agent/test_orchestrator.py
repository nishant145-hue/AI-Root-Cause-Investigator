from app.agent.agents.orchestrator import (
    MultiAgentOrchestrator,
)


def test_orchestrator_starts_with_planner():

    orchestrator = MultiAgentOrchestrator()

    state = {
        "investigation_status": "STARTING",
    }

    assert (
        orchestrator.decide(state)
        == "planner"
    )


def test_orchestrator_routes_to_validator():

    orchestrator = MultiAgentOrchestrator()

    state = {
        "investigation_status":
            "READY_FOR_VALIDATION",
    }

    assert (
        orchestrator.decide(state)
        == "validator"
    )


def test_orchestrator_stops_after_validation():

    orchestrator = MultiAgentOrchestrator()

    state = {
        "investigation_status":
            "ROOT_CAUSE_VALIDATED",
    }

    assert (
        orchestrator.decide(state)
        == "memory_writer"
    )
