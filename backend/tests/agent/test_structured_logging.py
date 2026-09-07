import json

import pytest
from app.agent.structured_logging import (
    AGENT_LOG_EVENTS,
    agent_log_context,
    log_agent_event,
)


def test_agent_log_events_are_defined():
    assert "agent_execution_started" in AGENT_LOG_EVENTS
    assert "agent_execution_completed" in AGENT_LOG_EVENTS
    assert "agent_execution_failed" in AGENT_LOG_EVENTS
    assert "agent_execution_cancelled" in AGENT_LOG_EVENTS
    assert "agent_execution_timeout" in AGENT_LOG_EVENTS
    assert "agent_execution_retry" in AGENT_LOG_EVENTS
    assert "agent_execution_rerouted" in AGENT_LOG_EVENTS


def test_log_agent_event_accepts_valid_event():
    log_agent_event(
        "agent_execution_started",
        investigation_id=100,
        execution_id="investigator-1",
        agent_name="investigator",
        trace_id="trace-1",
        span_id="span-1",
    )


def test_log_agent_event_rejects_empty_event():
    try:
        log_agent_event("")
        assert False
    except ValueError as exc:
        assert "event" in str(exc)


def test_log_agent_event_rejects_unknown_event():
    try:
        log_agent_event(
            "unknown_agent_event"
        )
        assert False
    except ValueError as exc:
        assert "Unsupported" in str(exc)


def test_log_agent_event_supports_context_fields():
    log_agent_event(
        "agent_execution_completed",
        investigation_id=123,
        execution_id="reasoner-1",
        agent_name="reasoner",
        trace_id="trace-123",
        span_id="span-456",
        parent_span_id="span-parent",
        duration_ms=125.5,
        retry_count=2,
        queue_wait_ms=14.2,
    )


def test_agent_log_context_can_be_entered():
    with agent_log_context(
        investigation_id=100,
        execution_id="investigator-1",
        agent_name="investigator",
        trace_id="trace-1",
        span_id="span-1",
    ):
        log_agent_event(
            "agent_execution_started"
        )


def test_agent_log_context_supports_extra_fields():
    with agent_log_context(
        investigation_id=100,
        trace_id="trace-1",
        custom_field="custom-value",
    ):
        log_agent_event(
            "agent_execution_completed",
            status="success",
        )


def test_agent_log_context_does_not_fail_with_none_values():
    with agent_log_context(
        investigation_id=100,
        execution_id=None,
        agent_name=None,
        trace_id="trace-1",
    ):
        log_agent_event(
            "agent_execution_started"
        )

def test_log_agent_event_emits_structured_payload(monkeypatch):
    captured = {}

    class FakeLogger:
        def info(self, message, **kwargs):
            captured["message"] = message
            captured["payload"] = kwargs

    monkeypatch.setattr(
        "app.agent.structured_logging.logger",
        FakeLogger(),
    )

    log_agent_event(
        "agent_execution_completed",
        investigation_id=100,
        execution_id="investigator-1",
        agent_name="investigator",
        trace_id="trace-1",
        span_id="span-1",
        parent_span_id="parent-1",
        status="success",
        duration_ms=25.5,
    )

    assert (
        captured["message"]
        == "agent_event=agent_execution_completed"
    )

    payload = captured["payload"]

    assert (
        payload["event"]
        == "agent_execution_completed"
    )

    assert payload["investigation_id"] == 100
    assert payload["execution_id"] == "investigator-1"
    assert payload["agent_name"] == "investigator"
    assert payload["trace_id"] == "trace-1"
    assert payload["span_id"] == "span-1"
    assert payload["parent_span_id"] == "parent-1"
    assert payload["status"] == "success"
    assert payload["duration_ms"] == 25.5

def test_log_agent_event_removes_none_context(monkeypatch):
    captured = {}

    class FakeLogger:
        def info(self, message, **kwargs):
            captured["payload"] = kwargs

    monkeypatch.setattr(
        "app.agent.structured_logging.logger",
        FakeLogger(),
    )

    log_agent_event(
        "agent_execution_started",
        investigation_id=100,
        execution_id=None,
        agent_name=None,
        trace_id="trace-1",
        span_id=None,
        parent_span_id=None,
    )

    payload = captured["payload"]

    assert payload["investigation_id"] == 100
    assert payload["trace_id"] == "trace-1"

    assert "execution_id" not in payload
    assert "agent_name" not in payload
    assert "span_id" not in payload
    assert "parent_span_id" not in payload

@pytest.mark.parametrize(
    "level,method_name",
    [
        ("INFO", "info"),
        ("WARNING", "warning"),
        ("ERROR", "error"),
        ("DEBUG", "debug"),
    ],
)
def test_log_agent_event_uses_requested_log_level(
    monkeypatch,
    level,
    method_name,
):
    called = {}

    class FakeLogger:
        def __getattr__(self, name):
            def log_method(message, **kwargs):
                called["method"] = name
                called["message"] = message
                called["payload"] = kwargs

            return log_method

    monkeypatch.setattr(
        "app.agent.structured_logging.logger",
        FakeLogger(),
    )

    log_agent_event(
        "agent_execution_started",
        level=level,
    )

    assert called["method"] == method_name

def test_log_agent_event_rejects_invalid_log_level(
    monkeypatch,
):
    class FakeLogger:
        pass

    monkeypatch.setattr(
        "app.agent.structured_logging.logger",
        FakeLogger(),
    )

    with pytest.raises(ValueError, match="Unsupported log level"):
        log_agent_event(
            "agent_execution_started",
            level="INVALID",
        )

def test_structured_agent_payload_is_json_serializable(
    monkeypatch,
):
    captured = {}

    class FakeLogger:
        def info(self, message, **kwargs):
            captured["payload"] = kwargs

    monkeypatch.setattr(
        "app.agent.structured_logging.logger",
        FakeLogger(),
    )

    log_agent_event(
        "agent_execution_completed",
        investigation_id=100,
        execution_id="investigator-1",
        agent_name="investigator",
        trace_id="trace-1",
        span_id="span-1",
        status="success",
        duration_ms=15.2,
        retry_count=1,
        queue_wait_ms=4.5,
    )

    payload = captured["payload"]

    serialized = json.dumps(payload)

    assert serialized

def test_structured_logging_does_not_automatically_log_sensitive_fields(
    monkeypatch,
):
    captured = {}

    class FakeLogger:
        def info(self, message, **kwargs):
            captured["payload"] = kwargs

    monkeypatch.setattr(
        "app.agent.structured_logging.logger",
        FakeLogger(),
    )

    log_agent_event(
        "agent_execution_started",
        investigation_id=100,
        execution_id="investigator-1",
        agent_name="investigator",
    )

    payload = captured["payload"]

    assert "password" not in payload
    assert "token" not in payload
    assert "api_key" not in payload
    assert "authorization" not in payload
    assert "secret" not in payload
