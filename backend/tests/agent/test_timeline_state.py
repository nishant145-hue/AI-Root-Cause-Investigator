from app.agent.state_timeline import (
    append_timeline_entries,
)

def test_investigation_state_supports_execution_timeline():

    state = {
        "incident_summary": "Database timeout",
        "investigation_status": "INVESTIGATING",
        "execution_timeline": [],
    }

    assert "execution_timeline" in state

    assert state[
        "execution_timeline"
    ] == []

def test_timeline_entries_are_preserved():

    existing = [
        {
            "agent": "investigator",
            "action": "search_logs",
            "status": "COMPLETED",
        }
    ]

    new_entry = {
        "agent": "reasoner",
        "action": "generate_hypotheses",
        "status": "COMPLETED",
    }

    state = {
        "execution_timeline": existing,
    }

    result = append_timeline_entries(
        state,
        [new_entry],
    )

    assert len(result) == 2

    assert result[0]["agent"] == (
        "investigator"
    )

    assert result[1]["agent"] == (
        "reasoner"
    )
def test_timeline_append_to_empty_state():

    state = {}

    entry = {
        "agent": "orchestrator",
        "action": "route_investigation",
        "status": "COMPLETED",
    }

    result = append_timeline_entries(
        state,
        [entry],
    )

    assert len(result) == 1

    assert result[0]["agent"] == (
        "orchestrator"
    )
def test_multiple_timeline_entries():

    state = {
        "execution_timeline": [
            {
                "agent": "orchestrator",
                "action": "route",
                "status": "COMPLETED",
            }
        ]
    }

    entries = [
        {
            "agent": "investigator",
            "action": "search_logs",
            "status": "COMPLETED",
        },
        {
            "agent": "reasoner",
            "action": "generate_hypotheses",
            "status": "COMPLETED",
        },
    ]

    result = append_timeline_entries(
        state,
        entries,
    )

    assert len(result) == 3

    assert [
        item["agent"]
        for item in result
    ] == [
        "orchestrator",
        "investigator",
        "reasoner",
    ]
