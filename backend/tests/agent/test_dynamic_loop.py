from app.agent.loop import (
    should_continue_investigation,
)


def test_investigation_continues_when_more_evidence_required():

    state = {
        "investigation_status": (
            "MORE_EVIDENCE_REQUIRED"
        ),
        "investigation_attempts": 1,
    }

    assert (
        should_continue_investigation(state)
        is True
    )
def test_investigation_stops_after_validation():

    state = {
        "investigation_status": (
            "ROOT_CAUSE_VALIDATED"
        ),
        "investigation_attempts": 1,
    }

    assert (
        should_continue_investigation(state)
        is False
    )
def test_investigation_stops_after_max_attempts():

    state = {
        "investigation_status": (
            "MORE_EVIDENCE_REQUIRED"
        ),
        "investigation_attempts": 3,
    }

    assert (
        should_continue_investigation(state)
        is False
    )
def test_replanning_requires_more_investigation():

    state = {
        "investigation_status": "REPLANNING",
        "investigation_attempts": 1,
    }

    assert (
        should_continue_investigation(state)
        is True
    )
