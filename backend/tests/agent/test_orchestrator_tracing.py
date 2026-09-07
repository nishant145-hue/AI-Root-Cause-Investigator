from app.agent.agents.orchestrator import (
    MultiAgentOrchestrator,
)


def test_orchestrator_records_routing_trace():

    orchestrator = (
        MultiAgentOrchestrator()
    )

    state = {
        "investigation_status":
            "STARTING",
    }

    result = orchestrator.run(state)

    assert result["next_agent"] == (
        "investigator"
    )

    traces = (
        orchestrator.execution_traces()
    )

    assert len(traces) == 1

    trace = traces[0]

    assert trace["agent"] == (
        "orchestrator"
    )

    assert trace["action"] == (
        "route_investigation"
    )

    assert trace["status"] == (
        "COMPLETED"
    )

    assert trace["metadata"][
        "investigation_status"
    ] == "STARTING"

    assert trace["metadata"][
        "next_agent"
    ] == "investigator"


def test_orchestrator_trace_records_memory_writer():

    orchestrator = (
        MultiAgentOrchestrator()
    )

    state = {
        "investigation_status":
            "ROOT_CAUSE_VALIDATED",
    }

    result = orchestrator.run(state)

    assert result["next_agent"] == (
        "memory_writer"
    )

    traces = (
        orchestrator.execution_traces()
    )

    assert len(traces) == 1

    assert traces[0]["metadata"][
        "next_agent"
    ] == "memory_writer"


def test_orchestrator_execution_summary():

    orchestrator = (
        MultiAgentOrchestrator()
    )

    orchestrator.route(
        {
            "investigation_status":
                "STARTING",
        }
    )

    orchestrator.route(
        {
            "investigation_status":
                "EVIDENCE_COLLECTED",
        }
    )

    summary = (
        orchestrator.execution_summary()
    )

    assert summary[
        "total_executions"
    ] == 2

    assert summary[
        "completed_executions"
    ] == 2

    assert summary[
        "failed_executions"
    ] == 0


def test_orchestrator_preserves_routing_behavior():

    orchestrator = (
        MultiAgentOrchestrator()
    )

    cases = [
        (
            "PLANNING",
            "investigator",
        ),
        (
            "EVIDENCE_COLLECTED",
            "memory",
        ),
        (
            "MEMORY_RETRIEVED",
            "reasoner",
        ),
        (
            "READY_FOR_VALIDATION",
            "validator",
        ),
        (
            "ROOT_CAUSE_VALIDATED",
            "memory_writer",
        ),
    ]

    for status, expected in cases:

        result = orchestrator.run(
            {
                "investigation_status":
                    status,
            }
        )

        assert result[
            "next_agent"
        ] == expected


def test_orchestrator_trace_duration():

    orchestrator = (
        MultiAgentOrchestrator()
    )

    orchestrator.route(
        {
            "investigation_status":
                "STARTING",
        }
    )

    trace = (
        orchestrator.execution_traces()
    )[0]

    assert trace[
        "started_at"
    ] is not None

    assert trace[
        "completed_at"
    ] is not None

    assert trace[
        "duration_ms"
    ] is not None

    assert trace[
        "duration_ms"
    ] >= 0
