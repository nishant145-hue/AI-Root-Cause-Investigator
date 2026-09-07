from app.agent.nodes.planner import planner_node
from app.agent.nodes.reflector import reflector_node


def test_reflector_triggers_dynamic_replanning():

    state = {
        "evidence": [
            {
                "log_line": "Database connection timeout",
                "reason": "Database connectivity failure",
            }
        ],
        "hypotheses": [
            {
                "cause": "Database connection failure",
                "confidence": 0.60,
            }
        ],
        "investigation_attempts": 1,
        "plan": [],
    }

    reflection = reflector_node(state)

    assert (
        reflection["investigation_status"]
        == "MORE_EVIDENCE_REQUIRED"
    )

    replanning_state = {
        **state,
        **reflection,
    }

    plan = planner_node(replanning_state)

    assert "next_action" in plan
    assert plan["next_action"]["tool"] == "search_logs"
