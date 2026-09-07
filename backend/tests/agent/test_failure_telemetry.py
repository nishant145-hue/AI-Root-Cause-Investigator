from app.agent.failure_telemetry import (
    FailureTelemetryCollector,
)


def test_failure_telemetry_records_failure():

    collector = FailureTelemetryCollector()

    event = collector.record_failure(
        agent_name="memory",
        failure_type="TRANSIENT",
        message="Qdrant timeout",
        attempt=1,
        execution_id="memory-1",
        investigation_id=100,
        trace_id="trace-1",
        span_id="span-1",
    )

    assert event.event_type == (
        "AGENT_FAILURE"
    )

    assert event.agent_name == "memory"

    assert event.failure_type == (
        "TRANSIENT"
    )

    assert event.attempt == 1

    assert event.execution_id == (
        "memory-1"
    )


def test_retry_telemetry_records_retry():

    collector = FailureTelemetryCollector()

    event = collector.record_retry(
        agent_name="memory",
        attempt=2,
        recovery_action="RETRY",
        reason="Transient failure",
        execution_id="memory-2",
        investigation_id=100,
        trace_id="trace-1",
        span_id="span-2",
        failure_type="TRANSIENT",
    )

    assert event.event_type == (
        "AGENT_RETRY"
    )

    assert event.attempt == 2

    assert event.recovery_action == (
        "RETRY"
    )

    assert event.failure_type == (
        "TRANSIENT"
    )


def test_timeout_telemetry_records_timeout():

    collector = FailureTelemetryCollector()

    event = collector.record_timeout(
        agent_name="investigator",
        timeout_seconds=60.0,
        attempt=2,
        message="Agent timed out",
        execution_id="investigator-2",
        investigation_id=101,
        trace_id="trace-2",
        span_id="span-2",
    )

    assert event.event_type == (
        "AGENT_TIMEOUT"
    )

    assert event.timeout_seconds == 60.0

    assert event.attempt == 2


def test_aggregate_tracks_all_event_types():

    collector = FailureTelemetryCollector()

    collector.record_failure(
        agent_name="memory",
        failure_type="TRANSIENT",
        message="timeout",
    )

    collector.record_failure(
        agent_name="reasoner",
        failure_type="CRITICAL",
        message="invalid state",
    )

    collector.record_retry(
        agent_name="memory",
        attempt=1,
        recovery_action="RETRY",
        reason="transient",
    )

    collector.record_timeout(
        agent_name="memory",
        timeout_seconds=60.0,
    )

    aggregate = collector.aggregate()

    assert aggregate["failure_count"] == 2

    assert aggregate["retry_count"] == 1

    assert aggregate["timeout_count"] == 1

    assert (
        aggregate["failures_by_agent"]["memory"]
        == 1
    )

    assert (
        aggregate["retries_by_agent"]["memory"]
        == 1
    )

    assert (
        aggregate["timeouts_by_agent"]["memory"]
        == 1
    )


def test_reset_clears_telemetry():

    collector = FailureTelemetryCollector()

    collector.record_failure(
        agent_name="memory",
        failure_type="TRANSIENT",
        message="failure",
    )

    collector.record_retry(
        agent_name="memory",
        attempt=1,
        recovery_action="RETRY",
        reason="retry",
    )

    collector.record_timeout(
        agent_name="memory",
        timeout_seconds=10.0,
    )

    collector.reset()

    aggregate = collector.aggregate()

    assert aggregate["failure_count"] == 0
    assert aggregate["retry_count"] == 0
    assert aggregate["timeout_count"] == 0
