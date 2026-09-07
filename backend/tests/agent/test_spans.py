from __future__ import annotations

import pytest

from app.agent.spans import (
    AgentSpan,
    AgentSpanCollector,
    agent_span,
)
from app.agent.trace_context import (
    clear_trace_context,
    create_trace_context,
    get_trace_context,
    trace_context,
)


def test_span_starts_in_started_state():
    span = AgentSpan(
        trace_id="trace-1",
        span_id="span-1",
        agent="investigator",
        action="analyze",
    )

    assert span.status == "STARTED"
    assert span.started_at is not None
    assert span.ended_at is None
    assert span.duration_ms is None


def test_span_start_moves_to_running():
    span = AgentSpan(
        trace_id="trace-1",
        span_id="span-1",
        agent="investigator",
        action="analyze",
    )

    span.start()

    assert span.status == "RUNNING"


def test_span_finish_records_duration():
    span = AgentSpan(
        trace_id="trace-1",
        span_id="span-1",
        agent="investigator",
        action="analyze",
    )

    span.start()
    span.finish()

    assert span.status == "COMPLETED"
    assert span.ended_at is not None
    assert span.duration_ms is not None
    assert span.duration_ms >= 0


def test_span_failure_records_error():
    span = AgentSpan(
        trace_id="trace-1",
        span_id="span-1",
        agent="reasoner",
        action="reason",
    )

    span.start()
    span.fail("model failed")

    assert span.status == "FAILED"
    assert span.error == "model failed"
    assert span.ended_at is not None
    assert span.duration_ms is not None


def test_span_cancellation():
    span = AgentSpan(
        trace_id="trace-1",
        span_id="span-1",
        agent="validator",
        action="validate",
    )

    span.start()
    span.cancel("cancelled by user")

    assert span.status == "CANCELLED"
    assert span.error == "cancelled by user"
    assert span.ended_at is not None


def test_span_cannot_finish_twice():
    span = AgentSpan(
        trace_id="trace-1",
        span_id="span-1",
        agent="investigator",
        action="analyze",
    )

    span.start()
    span.finish()

    with pytest.raises(
        RuntimeError,
        match="already ended",
    ):
        span.finish()


def test_span_attributes():
    span = AgentSpan(
        trace_id="trace-1",
        span_id="span-1",
        agent="investigator",
        action="analyze",
    )

    span.set_attribute(
        "model",
        "reasoning-model",
    )

    span.set_attribute(
        "attempt",
        1,
    )

    assert span.attributes[
        "model"
    ] == "reasoning-model"

    assert span.attributes[
        "attempt"
    ] == 1


def test_span_serialization():
    span = AgentSpan(
        trace_id="trace-1",
        span_id="span-2",
        parent_span_id="span-1",
        agent="reasoner",
        action="reason",
    )

    span.start()
    span.finish()

    data = span.to_dict()

    assert data["trace_id"] == "trace-1"
    assert data["span_id"] == "span-2"
    assert data["parent_span_id"] == "span-1"
    assert data["agent"] == "reasoner"
    assert data["action"] == "reason"
    assert data["status"] == "COMPLETED"
    assert data["duration_ms"] >= 0


def test_span_collector():
    collector = AgentSpanCollector()

    span = collector.start(
        trace_id="trace-1",
        span_id="span-1",
        agent="investigator",
        action="analyze",
    )

    assert span.status == "RUNNING"
    assert len(
        collector.spans()
    ) == 1

    assert (
        collector.find("span-1")
        is span
    )

    span.finish()

    assert len(
        collector.completed_spans()
    ) == 1


def test_agent_span_context_manager():
    clear_trace_context()

    parent = create_trace_context()

    collector = AgentSpanCollector()

    with trace_context(parent):

        with agent_span(
            collector,
            agent="investigator",
            action="analyze",
        ) as span:

            current = (
                get_trace_context()
            )

            assert (
                current.trace_id
                == parent.trace_id
            )

            assert (
                current.span_id
                == span.span_id
            )

            assert (
                current.parent_span_id
                == parent.span_id
            )

            assert (
                span.status
                == "RUNNING"
            )

        assert (
            span.status
            == "COMPLETED"
        )

        assert (
            get_trace_context()
            == parent
        )

    clear_trace_context()


def test_agent_span_context_manager_failure():
    clear_trace_context()

    collector = AgentSpanCollector()

    with pytest.raises(
        RuntimeError,
        match="boom",
    ):

        with agent_span(
            collector,
            agent="reasoner",
            action="reason",
        ) as span:

            raise RuntimeError("boom")

    assert span.status == "FAILED"
    assert span.error == "boom"
    assert span.ended_at is not None

    clear_trace_context()
