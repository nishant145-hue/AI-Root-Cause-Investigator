from app.agent.state import InvestigationState
from app.agent.state_handoff import update_investigation_state


def test_investigator_handoff():

    state = {
        "observations": [],
        "evidence": [],
    }

    updated = update_investigation_state(
        state,
        observations=[
            {
                "component": "database",
                "message": "Connection timeout",
            }
        ],
        evidence=[
            {
                "message": "Database connection timeout",
            }
        ],
    )

    assert len(
        updated["observations"]
    ) == 1

    assert len(
        updated["evidence"]
    ) == 1

def test_memory_handoff():

    state = {
        "historical_incidents": [],
    }

    updated = update_investigation_state(
        state,
        historical_incidents=[
            {
                "investigation_id": 124,
                "similarity": 0.91,
                "root_cause": (
                    "Database connection pool exhaustion"
                ),
            }
        ],
    )

    assert len(
        updated["historical_incidents"]
    ) == 1

    assert (
        updated["historical_incidents"][0][
            "similarity"
        ]
        == 0.91
    )
def test_reasoner_handoff():

    state = {
        "hypotheses": [],
    }

    updated = update_investigation_state(
        state,
        hypotheses=[
            {
                "cause": "Database failure",
                "confidence": 0.82,
                "status": "CANDIDATE",
            }
        ],
    )

    assert len(
        updated["hypotheses"]
    ) == 1

    assert (
        updated["hypotheses"][0]["confidence"]
        == 0.82
    )
def test_validator_handoff():

    state = {
        "root_cause": None,
        "confidence": None,
        "investigation_status": "VALIDATING",
    }

    updated = update_investigation_state(
        state,
        root_cause="Database failure",
        confidence=0.91,
        investigation_status=(
            "ROOT_CAUSE_VALIDATED"
        ),
    )

    assert updated["root_cause"] == (
        "Database failure"
    )

    assert updated["confidence"] == 0.91

    assert updated["investigation_status"] == (
        "ROOT_CAUSE_VALIDATED"
    )
