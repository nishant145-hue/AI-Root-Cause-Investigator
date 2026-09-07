from app.agent.state_timeline import (
    propagate_timeline,
)


def test_timeline_propagation_preserves_existing_entries():

    state = {
        "execution_timeline": [
            {
                "agent": "orchestrator",
                "action": "route_investigation",
                "status": "COMPLETED",
            }
        ]
    }

    new_entries = [
        {
            "agent": "investigator",
            "action": "search_logs",
            "status": "COMPLETED",
        }
    ]

    result = propagate_timeline(
        state,
        new_entries,
    )

    assert len(
        result["execution_timeline"]
    ) == 2

    assert (
        result["execution_timeline"][0]["agent"]
        == "orchestrator"
    )

    assert (
        result["execution_timeline"][1]["agent"]
        == "investigator"
    )


def test_timeline_propagation_from_empty_state():

    state = {}

    new_entries = [
        {
            "agent": "investigator",
            "action": "search_logs",
            "status": "COMPLETED",
        }
    ]

    result = propagate_timeline(
        state,
        new_entries,
    )

    assert len(
        result["execution_timeline"]
    ) == 1


def test_timeline_propagation_does_not_mutate_original_state():

    existing = [
        {
            "agent": "orchestrator",
            "action": "route",
            "status": "COMPLETED",
        }
    ]

    state = {
        "execution_timeline": existing,
    }

    new_entry = {
        "agent": "memory",
        "action": "semantic_search",
        "status": "COMPLETED",
    }

    result = propagate_timeline(
        state,
        [new_entry],
    )

    assert len(
        state["execution_timeline"]
    ) == 1

    assert len(
        result["execution_timeline"]
    ) == 2


def test_multiple_nodes_preserve_timeline():

    state = {}

    state = propagate_timeline(
        state,
        [
            {
                "agent": "orchestrator",
                "action": "route",
                "status": "COMPLETED",
            }
        ],
    )

    state = propagate_timeline(
        state,
        [
            {
                "agent": "investigator",
                "action": "search_logs",
                "status": "COMPLETED",
            }
        ],
    )

    state = propagate_timeline(
        state,
        [
            {
                "agent": "reasoner",
                "action": "generate_hypotheses",
                "status": "COMPLETED",
            }
        ],
    )

    timeline = state[
        "execution_timeline"
    ]

    assert len(timeline) == 3

    assert [
        item["agent"]
        for item in timeline
    ] == [
        "orchestrator",
        "investigator",
        "reasoner",
    ]
