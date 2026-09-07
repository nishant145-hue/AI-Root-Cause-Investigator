from app.agent.nodes.orchestrator import (
    orchestrator_node,
)


def test_orchestrator_node_routes_to_investigator(
    monkeypatch,
):

    class FakeOrchestrator:

        def run(self, state):
            return {
            "next_agent": "investigator",
        }

        def execution_timeline_state(self):
            return []

    monkeypatch.setattr(
        "app.agent.nodes.orchestrator.MultiAgentOrchestrator",
        FakeOrchestrator,
    )

    result = orchestrator_node(
        {
            "investigation_status": "PLANNING",
        }
    )

    assert result["next_agent"] == "investigator"

def test_orchestrator_node_routes_to_validator(
    monkeypatch,
):

    class FakeOrchestrator:

        def run(self, state):
            return {
            "next_agent": "validator",
        }

        def execution_timeline_state(self):
            return []

    monkeypatch.setattr(
        "app.agent.nodes.orchestrator.MultiAgentOrchestrator",
        FakeOrchestrator,
    )

    result = orchestrator_node(
        {
            "investigation_status": (
                "READY_FOR_VALIDATION"
            ),
        }
    )

    assert result["next_agent"] == "validator"
