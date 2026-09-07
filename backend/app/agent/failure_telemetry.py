from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from threading import Lock
from typing import Any


@dataclass(frozen=True)
class FailureTelemetryEvent:
    """
    Telemetry describing one agent failure.
    """

    event_type: str
    agent_name: str

    timestamp: datetime

    execution_id: str | None = None
    investigation_id: int | None = None

    trace_id: str | None = None
    span_id: str | None = None
    parent_span_id: str | None = None

    failure_type: str | None = None
    message: str | None = None

    attempt: int = 1

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)

        data["timestamp"] = (
            self.timestamp.isoformat()
        )

        return data


@dataclass(frozen=True)
class RetryTelemetryEvent:
    """
    Telemetry describing one retry decision.
    """

    event_type: str
    agent_name: str

    timestamp: datetime

    attempt: int

    recovery_action: str

    reason: str

    execution_id: str | None = None
    investigation_id: int | None = None

    trace_id: str | None = None
    span_id: str | None = None
    parent_span_id: str | None = None

    failure_type: str | None = None

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)

        data["timestamp"] = (
            self.timestamp.isoformat()
        )

        return data


@dataclass(frozen=True)
class TimeoutTelemetryEvent:
    """
    Telemetry describing one timeout.
    """

    event_type: str
    agent_name: str

    timestamp: datetime

    timeout_seconds: float

    execution_id: str | None = None
    investigation_id: int | None = None

    trace_id: str | None = None
    span_id: str | None = None
    parent_span_id: str | None = None

    attempt: int = 1

    message: str | None = None

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)

        data["timestamp"] = (
            self.timestamp.isoformat()
        )

        return data


class FailureTelemetryCollector:
    """
    Thread-safe collector for failure, retry,
    and timeout telemetry.

    This collector does not perform recovery.

    It only records what happened.
    """

    def __init__(self) -> None:

        self._lock = Lock()

        self._failures: list[
            FailureTelemetryEvent
        ] = []

        self._retries: list[
            RetryTelemetryEvent
        ] = []

        self._timeouts: list[
            TimeoutTelemetryEvent
        ] = []

    # =========================================================
    # Failure
    # =========================================================

    def record_failure(
        self,
        *,
        agent_name: str,
        failure_type: str | None,
        message: str | None,
        attempt: int = 1,
        execution_id: str | None = None,
        investigation_id: int | None = None,
        trace_id: str | None = None,
        span_id: str | None = None,
        parent_span_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> FailureTelemetryEvent:

        event = FailureTelemetryEvent(
            event_type="AGENT_FAILURE",
            agent_name=agent_name,
            timestamp=datetime.now(timezone.utc),
            execution_id=execution_id,
            investigation_id=investigation_id,
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            failure_type=failure_type,
            message=message,
            attempt=attempt,
            metadata=dict(metadata or {}),
        )

        with self._lock:
            self._failures.append(event)

        return event

    # =========================================================
    # Retry
    # =========================================================

    def record_retry(
        self,
        *,
        agent_name: str,
        attempt: int,
        recovery_action: str,
        reason: str,
        execution_id: str | None = None,
        investigation_id: int | None = None,
        trace_id: str | None = None,
        span_id: str | None = None,
        parent_span_id: str | None = None,
        failure_type: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> RetryTelemetryEvent:

        event = RetryTelemetryEvent(
            event_type="AGENT_RETRY",
            agent_name=agent_name,
            timestamp=datetime.now(timezone.utc),
            attempt=attempt,
            recovery_action=recovery_action,
            reason=reason,
            execution_id=execution_id,
            investigation_id=investigation_id,
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            failure_type=failure_type,
            metadata=dict(metadata or {}),
        )

        with self._lock:
            self._retries.append(event)

        return event

    # =========================================================
    # Timeout
    # =========================================================

    def record_timeout(
        self,
        *,
        agent_name: str,
        timeout_seconds: float,
        attempt: int = 1,
        message: str | None = None,
        execution_id: str | None = None,
        investigation_id: int | None = None,
        trace_id: str | None = None,
        span_id: str | None = None,
        parent_span_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> TimeoutTelemetryEvent:

        event = TimeoutTelemetryEvent(
            event_type="AGENT_TIMEOUT",
            agent_name=agent_name,
            timestamp=datetime.now(timezone.utc),
            timeout_seconds=timeout_seconds,
            execution_id=execution_id,
            investigation_id=investigation_id,
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            attempt=attempt,
            message=message,
            metadata=dict(metadata or {}),
        )

        with self._lock:
            self._timeouts.append(event)

        return event

    # =========================================================
    # Accessors
    # =========================================================

    def failures(
        self,
    ) -> list[FailureTelemetryEvent]:

        with self._lock:
            return list(self._failures)

    def retries(
        self,
    ) -> list[RetryTelemetryEvent]:

        with self._lock:
            return list(self._retries)

    def timeouts(
        self,
    ) -> list[TimeoutTelemetryEvent]:

        with self._lock:
            return list(self._timeouts)

    # =========================================================
    # Snapshot
    # =========================================================

    def snapshot(self) -> dict[str, Any]:

        with self._lock:

            failures = list(self._failures)
            retries = list(self._retries)
            timeouts = list(self._timeouts)

        return {
            "failure_count": len(failures),
            "retry_count": len(retries),
            "timeout_count": len(timeouts),
            "failures": [
                event.to_dict()
                for event in failures
            ],
            "retries": [
                event.to_dict()
                for event in retries
            ],
            "timeouts": [
                event.to_dict()
                for event in timeouts
            ],
        }

    # =========================================================
    # Aggregate
    # =========================================================

    def aggregate(self) -> dict[str, Any]:

        with self._lock:

            failures = list(self._failures)
            retries = list(self._retries)
            timeouts = list(self._timeouts)

        failures_by_agent: dict[str, int] = {}
        retries_by_agent: dict[str, int] = {}
        timeouts_by_agent: dict[str, int] = {}

        for event in failures:

            failures_by_agent[event.agent_name] = (
                failures_by_agent.get(
                    event.agent_name,
                    0,
                )
                + 1
            )

        for event in retries:

            retries_by_agent[event.agent_name] = (
                retries_by_agent.get(
                    event.agent_name,
                    0,
                )
                + 1
            )

        for event in timeouts:

            timeouts_by_agent[event.agent_name] = (
                timeouts_by_agent.get(
                    event.agent_name,
                    0,
                )
                + 1
            )

        return {
            "failure_count": len(failures),
            "retry_count": len(retries),
            "timeout_count": len(timeouts),
            "failures_by_agent": failures_by_agent,
            "retries_by_agent": retries_by_agent,
            "timeouts_by_agent": timeouts_by_agent,
        }

    # =========================================================
    # Reset
    # =========================================================

    def reset(self) -> None:

        with self._lock:

            self._failures.clear()
            self._retries.clear()
            self._timeouts.clear()
