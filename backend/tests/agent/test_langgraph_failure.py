from app.agent.nodes.failure import failure_node


def test_failure_node_records_transient_failure():

    state = {
        "last_failed_agent": "memory",
        "last_failure_type": "TRANSIENT",
        "last_failure_message": "Qdrant timeout",
        "agent_failures": [],
        "retry_counts": {},
    }

    result = failure_node(state)

    assert result["recovery_action"] == "RETRY"
    assert (
        result["investigation_status"]
        == "RETRYING"
    )

    assert len(
        result["agent_failures"]
    ) == 1

    assert (
        result["retry_counts"]["memory"]
        == 1
    )


def test_failure_node_reroutes_after_retries():

    state = {
        "last_failed_agent": "memory",
        "last_failure_type": "TRANSIENT",
        "last_failure_message": "Qdrant timeout",
        "agent_failures": [],
        "retry_counts": {
            "memory": 2,
        },
    }

    result = failure_node(state)

    assert (
        result["recovery_action"]
        == "REROUTE"
    )

    assert (
        result["investigation_status"]
        == "REPLANNING"
    )

    assert (
        result["retry_counts"]["memory"]
        == 3
    )


def test_failure_node_stops_on_critical_failure():

    state = {
        "last_failed_agent": "validator",
        "last_failure_type": "CRITICAL",
        "last_failure_message": (
            "Invalid investigation state"
        ),
        "agent_failures": [],
        "retry_counts": {},
    }

    result = failure_node(state)

    assert (
        result["recovery_action"]
        == "STOP"
    )

    assert (
        result["investigation_status"]
        == "FAILED"
    )


def test_failure_node_without_agent_stops():

    state = {
        "agent_failures": [],
        "retry_counts": {},
    }

    result = failure_node(state)

    assert (
        result["recovery_action"]
        == "STOP"
    )

    assert (
        result["investigation_status"]
        == "FAILED"
    )
