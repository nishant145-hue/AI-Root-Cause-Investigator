from app.agent.graph import build_investigation_graph


def test_investigator_failure_is_routed_to_recovery(
    monkeypatch,
    db_session,
):
    """
    Inject a transient investigator failure and verify
    that the graph enters the failure-recovery path.
    """

    import app.agent.graph as graph_module

    def failing_investigator(
        state,
        session,
    ):
        raise TimeoutError(
            "Injected investigator timeout"
        )

    # Patch the exact reference used by graph.py.
    monkeypatch.setattr(
        graph_module,
        "investigator_node",
        failing_investigator,
    )

    graph = build_investigation_graph(
        db_session
    )

    initial_state = {
        "investigation_id": 1,
        "user_id": 1,
        "log_file_id": 1,

        "incident_summary": (
            "Injected investigator timeout"
        ),

        "plan": [
            "Search error logs for initial evidence."
        ],

        "current_step": (
            "Search logs for evidence"
        ),

        "next_action": {
            "tool": "search_logs",
            "reason": (
                "Initial log investigation."
            ),
            "parameters": {
                "severity": "ERROR",
                "limit": 50,
            },
        },

        "observations": [],
        "evidence": [],
        "historical_incidents": [],
        "hypotheses": [],
        "tool_calls": [],
        "tool_results": [],
        "remaining_questions": [],

        "investigation_attempts": 0,
        "investigation_status": "IN_PROGRESS",

        "agent_failures": [],
        "retry_counts": {},

        "last_failed_agent": None,
        "last_failure_type": None,
        "last_failure_message": None,

        "recovery_action": None,

        "execution_timeline": [],
        "execution_analytics": {},
    }

    # The current graph needs to receive failure state
    # rather than allowing the exception to escape.
    result = graph.invoke(
        initial_state
    )

    assert result is not None

    assert (
        result.get(
            "last_failed_agent"
        )
        == "investigator"
    )

    assert (
        result.get(
            "last_failure_message"
        )
        == "Injected investigator timeout"
    )

    assert (
        result.get(
            "recovery_action"
        )
        in {
            "RETRY",
            "REROUTE",
            "STOP",
        }
    )


def test_critical_failure_reaches_terminal_recovery(
    monkeypatch,
    db_session,
):
    """
    Inject a critical investigator failure after the
    retry limit has already been reached.
    """

    import app.agent.graph as graph_module

    def failing_investigator(
        state,
        session,
    ):
        raise RuntimeError(
            "Injected critical investigator failure"
        )

    # Patch the exact reference used by graph.py.
    monkeypatch.setattr(
        graph_module,
        "investigator_node",
        failing_investigator,
    )

    graph = build_investigation_graph(
        db_session
    )

    initial_state = {
        "investigation_id": 1,
        "user_id": 1,
        "log_file_id": 1,

        "incident_summary": (
            "Injected critical investigator failure"
        ),

        "plan": [
            "Search error logs for initial evidence."
        ],

        "current_step": (
            "Search logs for evidence"
        ),

        "next_action": {
            "tool": "search_logs",
            "reason": (
                "Initial log investigation."
            ),
            "parameters": {
                "severity": "ERROR",
                "limit": 50,
            },
        },

        "observations": [],
        "evidence": [],
        "historical_incidents": [],
        "hypotheses": [],
        "tool_calls": [],
        "tool_results": [],
        "remaining_questions": [],

        "investigation_attempts": 0,
        "investigation_status": "IN_PROGRESS",

        "agent_failures": [],

        "retry_counts": {
            "investigator": 2,
        },

        "last_failed_agent": None,
        "last_failure_type": None,
        "last_failure_message": None,

        "recovery_action": None,

        "execution_timeline": [],
        "execution_analytics": {},
    }

    result = graph.invoke(
        initial_state
    )

    assert result is not None

    assert (
        result.get(
            "last_failed_agent"
        )
        == "investigator"
    )

    assert (
        result.get(
            "last_failure_message"
        )
        == "Injected critical investigator failure"
    )

    assert (
        result.get(
            "recovery_action"
        )
        == "STOP"
    )

    assert (
        result.get(
            "investigation_status"
        )
        == "FAILED"
    )

def test_langgraph_failure_persists_circuit_breaker_state(
    monkeypatch,
    db_session,
):
    """
    Verify that a failure captured by the centralized
    recovery layer persists circuit-breaker state into
    the final LangGraph state.
    """

    import app.agent.graph as graph_module

    def failing_investigator(
        state,
        session,
    ):
        raise RuntimeError(
            "Injected circuit breaker failure"
        )

    monkeypatch.setattr(
        graph_module,
        "investigator_node",
        failing_investigator,
    )

    graph = build_investigation_graph(
        db_session
    )

    initial_state = {
        "investigation_id": 1,
        "user_id": 1,
        "log_file_id": 1,
        "incident_summary": (
            "Circuit breaker integration test"
        ),

        "plan": [
            "Search error logs."
        ],
        "current_step": (
            "Search logs for evidence"
        ),
        "next_action": {
            "tool": "search_logs",
            "reason": "Initial investigation.",
            "parameters": {
                "severity": "ERROR",
                "limit": 50,
            },
        },

        "observations": [],
        "evidence": [],
        "historical_incidents": [],
        "hypotheses": [],
        "tool_calls": [],
        "tool_results": [],
        "remaining_questions": [],

        "confidence": None,
        "root_cause": None,
        "failed_component": None,

        "investigation_attempts": 0,
        "investigation_status": "IN_PROGRESS",

        "agent_failures": [],
        "retry_counts": {},

        "last_failed_agent": None,
        "last_failure_type": None,
        "last_failure_message": None,
        "recovery_action": None,

        "execution_timeline": [],
        "execution_analytics": {},
    }

    result = graph.invoke(
        initial_state
    )

    assert result is not None

    assert (
        result["last_failed_agent"]
        == "investigator"
    )

    assert (
        result["last_failure_type"]
        == "CRITICAL"
    )

    assert (
        result["last_failure_message"]
        == "Injected circuit breaker failure"
    )

    assert (
        "circuit_breaker_states"
        in result
    )

    assert (
        "investigator"
        in result[
            "circuit_breaker_states"
        ]
    )

    assert (
        result[
            "circuit_breaker_states"
        ]["investigator"]
        in {
            "CLOSED",
            "OPEN",
            "HALF_OPEN",
        }
    )

    assert (
        "circuit_breaker_failures"
        in result
    )

    assert (
        result[
            "circuit_breaker_failures"
        ]["investigator"]
        >= 1
    )

def test_successful_retry_clears_stale_failure_state(
    monkeypatch,
):
    """
    Verify that a failed investigator followed by a successful retry
    clears stale failure-routing state.
    """

    from app.agent import graph as graph_module

    call_count = {"investigator": 0}

    def flaky_investigator(
        state,
        session,
    ):
        call_count["investigator"] += 1

        # First execution fails.
        if call_count["investigator"] == 1:
            raise TimeoutError(
                "simulated transient investigator failure"
            )

        # Retry succeeds.
        return {
            "observations": [
                "Investigator succeeded after retry."
            ],
            "evidence": [],
            "failed_component": "database",
            "severity": "HIGH",
            "investigation_status": "INVESTIGATING",
        }

    monkeypatch.setattr(
        graph_module,
        "investigator_node",
        flaky_investigator,
    )

    initial_state = {
        "investigation_id": 999,
        "user_id": 1,
        "log_file_id": 1,
        "incident_summary": "Database connection failure",
        "investigation_status": "INVESTIGATING",
        "agent_failures": [],
        "retry_counts": {},
        "last_failed_agent": None,
        "last_failure_type": None,
        "last_failure_message": None,
        "recovery_action": None,
        "failure_metadata": {},
        "circuit_breaker_states": {},
        "circuit_breaker_failures": {},
        "circuit_breaker_opened_at": {},
        "isolated_agents": [],
        "reroute_count": 0,
        "last_rerouted_agent": None,
    }

    # ---------------------------------------------------------
    # First execution -> failure
    # ---------------------------------------------------------

    first_result = graph_module.safe_investigator_node(
        initial_state,
        None,
    )

    assert call_count["investigator"] == 1

    assert first_result.get(
        "last_failed_agent"
    ) == "investigator"

    assert first_result.get("recovery_action") is None

    # ---------------------------------------------------------
    # Prepare state for retry
    # ---------------------------------------------------------

    retry_state = {
        **initial_state,
        **first_result,
    }

    retry_state["recovery_action"] = "RETRY"
    retry_state["next_agent"] = "investigator"

    # ---------------------------------------------------------
    # Second execution -> success
    # ---------------------------------------------------------

    second_result = graph_module.safe_investigator_node(
        retry_state,
        None,
    )

    assert call_count["investigator"] == 2

    # ---------------------------------------------------------
    # Critical assertions
    # ---------------------------------------------------------

    assert second_result.get(
        "last_failed_agent"
    ) is None

    assert second_result.get(
        "last_failure_type"
    ) is None

    assert second_result.get(
        "last_failure_message"
    ) is None

    assert second_result.get(
        "recovery_action"
    ) is None

    assert second_result.get(
        "failed_component"
    ) == "database"

    assert second_result.get(
        "severity"
    ) == "HIGH"
