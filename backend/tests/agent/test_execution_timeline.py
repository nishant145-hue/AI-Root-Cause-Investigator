from datetime import datetime, timedelta, timezone

from app.agent.observability import (
    AgentExecutionTrace,
    UnifiedExecutionTimeline,
)


def make_trace(
    agent: str,
    action: str,
    started_at: datetime,
    status: str = "COMPLETED",
    attempt: int = 1,
    duration_ms: float = 10.0,
    error: str | None = None,
) -> AgentExecutionTrace:

    trace = AgentExecutionTrace(
        agent=agent,
        action=action,
        status="RUNNING",
        started_at=started_at,
        attempt=attempt,
    )

    trace.complete(
        status=status,
        error=error,
    )

    trace.duration_ms = duration_ms

    return trace


def test_timeline_orders_traces_chronologically():

    now = datetime.now(
        timezone.utc
    )

    validator = make_trace(
        agent="validator",
        action="validate_root_cause",
        started_at=now + timedelta(seconds=3),
    )

    investigator = make_trace(
        agent="investigator",
        action="search_logs",
        started_at=now + timedelta(seconds=1),
    )

    orchestrator = make_trace(
        agent="orchestrator",
        action="route_investigation",
        started_at=now,
    )

    timeline = UnifiedExecutionTimeline()

    timeline.add_trace(validator)
    timeline.add_trace(investigator)
    timeline.add_trace(orchestrator)

    traces = timeline.traces()

    assert [
        trace.agent
        for trace in traces
    ] == [
        "orchestrator",
        "investigator",
        "validator",
    ]


def test_timeline_combines_multiple_agents():

    now = datetime.now(
        timezone.utc
    )

    timeline = UnifiedExecutionTimeline()

    timeline.add_traces(
        [
            make_trace(
                "orchestrator",
                "route_investigation",
                now,
            ),
            make_trace(
                "investigator",
                "search_logs",
                now + timedelta(seconds=1),
            ),
            make_trace(
                "memory",
                "semantic_memory_search",
                now + timedelta(seconds=2),
            ),
            make_trace(
                "reasoner",
                "generate_hypotheses",
                now + timedelta(seconds=3),
            ),
            make_trace(
                "validator",
                "validate_root_cause",
                now + timedelta(seconds=4),
            ),
        ]
    )

    traces = timeline.traces()

    assert len(traces) == 5

    assert {
        trace.agent
        for trace in traces
    } == {
        "orchestrator",
        "investigator",
        "memory",
        "reasoner",
        "validator",
    }


def test_timeline_summary():

    now = datetime.now(
        timezone.utc
    )

    timeline = UnifiedExecutionTimeline()

    timeline.add_traces(
        [
            make_trace(
                "investigator",
                "search_logs",
                now,
                status="FAILED",
                attempt=1,
                error="timeout",
            ),
            make_trace(
                "investigator",
                "search_logs",
                now + timedelta(seconds=1),
                status="COMPLETED",
                attempt=2,
                duration_ms=20.0,
            ),
            make_trace(
                "reasoner",
                "generate_hypotheses",
                now + timedelta(seconds=2),
                status="COMPLETED",
                attempt=1,
                duration_ms=30.0,
            ),
        ]
    )

    summary = timeline.summary()

    assert summary[
        "total_executions"
    ] == 3

    assert summary[
        "completed_executions"
    ] == 2

    assert summary[
        "failed_executions"
    ] == 1

    assert summary[
        "retries"
    ] == 1

    assert summary[
    "total_duration_ms"
] == 60.0

def test_timeline_serialization():

    now = datetime.now(
        timezone.utc
    )

    timeline = UnifiedExecutionTimeline()

    timeline.add_trace(
        make_trace(
            "investigator",
            "search_logs",
            now,
        )
    )

    data = timeline.to_dict()

    assert len(data) == 1

    assert data[0]["agent"] == (
        "investigator"
    )

    assert data[0]["action"] == (
        "search_logs"
    )

    assert data[0]["status"] == (
        "COMPLETED"
    )

    assert data[0]["attempt"] == 1

from unittest.mock import Mock, patch

from app.agent.agents.orchestrator import (
    MultiAgentOrchestrator,
)


def test_orchestrator_builds_unified_timeline():

    orchestrator = (
        MultiAgentOrchestrator()
    )

    # Generate an orchestrator trace.
    orchestrator.route(
        {
            "investigation_status":
                "STARTING",
        }
    )

    # Generate investigator trace.
    with patch(
        "app.agent.agents.investigator.search_logs",
        return_value=[
            {"id": 1},
        ],
    ):

        orchestrator.investigator.search_logs(
            session=Mock(),
            log_file_id=1,
        )

    timeline = (
        orchestrator.build_execution_timeline()
    )

    traces = timeline.traces()

    assert len(traces) == 2

    assert {
        trace.agent
        for trace in traces
    } == {
        "orchestrator",
        "investigator",
    }


def test_orchestrator_timeline_summary():

    orchestrator = (
        MultiAgentOrchestrator()
    )

    orchestrator.route(
        {
            "investigation_status":
                "STARTING",
        }
    )

    summary = (
        orchestrator.execution_timeline_summary()
    )

    assert summary[
        "total_executions"
    ] == 1

    assert summary[
        "completed_executions"
    ] == 1

    assert summary[
        "failed_executions"
    ] == 0

    assert "orchestrator" in (
        summary["agents"]
    )
