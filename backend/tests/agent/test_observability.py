from time import sleep

from app.agent.observability import (
    AgentExecutionTrace,
    ExecutionTraceCollector,
)


def test_execution_trace_starts_running():

    collector = ExecutionTraceCollector()

    trace = collector.start(
        agent="investigator",
        action="search_logs",
    )

    assert trace.agent == "investigator"
    assert trace.action == "search_logs"
    assert trace.status == "RUNNING"
    assert trace.attempt == 1
    assert trace.started_at is not None


def test_execution_trace_completion_records_duration():

    collector = ExecutionTraceCollector()

    trace = collector.start(
        agent="memory",
        action="semantic_search",
    )

    sleep(0.01)

    trace.complete()

    assert trace.status == "COMPLETED"
    assert trace.completed_at is not None
    assert trace.duration_ms is not None
    assert trace.duration_ms >= 0


def test_execution_trace_records_failure():

    collector = ExecutionTraceCollector()

    trace = collector.start(
        agent="reasoner",
        action="generate_hypotheses",
        attempt=2,
    )

    trace.complete(
        status="FAILED",
        error="LLM timeout",
    )

    assert trace.status == "FAILED"
    assert trace.error == "LLM timeout"
    assert trace.attempt == 2


def test_collector_tracks_multiple_agents():

    collector = ExecutionTraceCollector()

    first = collector.start(
        agent="investigator",
        action="search_logs",
    )

    second = collector.start(
        agent="memory",
        action="semantic_search",
    )

    first.complete()
    second.complete()

    traces = collector.traces()

    assert len(traces) == 2
    assert traces[0].agent == "investigator"
    assert traces[1].agent == "memory"


def test_collector_summary():

    collector = ExecutionTraceCollector()

    first = collector.start(
        agent="memory",
        action="semantic_search",
        attempt=2,
    )

    second = collector.start(
        agent="validator",
        action="validate_root_cause",
    )

    first.complete()
    second.complete()

    summary = collector.summary()

    assert summary[
        "total_executions"
    ] == 2

    assert summary[
        "completed_executions"
    ] == 2

    assert summary[
        "failed_executions"
    ] == 0

    assert summary[
        "retries"
    ] == 1


def test_trace_serialization():

    collector = ExecutionTraceCollector()

    trace = collector.start(
        agent="reasoner",
        action="generate_hypotheses",
        metadata={
            "model": "llm",
        },
    )

    trace.complete()

    data = trace.to_dict()

    assert data["agent"] == "reasoner"
    assert data["action"] == (
        "generate_hypotheses"
    )

    assert data["status"] == "COMPLETED"

    assert data["metadata"]["model"] == "llm"


def test_collector_serialization():

    collector = ExecutionTraceCollector()

    trace = collector.start(
        agent="planner",
        action="create_plan",
    )

    trace.complete()

    data = collector.to_dict()

    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["agent"] == "planner"


def test_collector_clear():

    collector = ExecutionTraceCollector()

    trace = collector.start(
        agent="investigator",
        action="search_logs",
    )

    trace.complete()

    assert len(
        collector.traces()
    ) == 1

    collector.clear()

    assert len(
        collector.traces()
    ) == 0
