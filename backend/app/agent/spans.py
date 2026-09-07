from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterator

from app.agent.trace_context import (
    TraceContext,
    create_child_trace_context,
    get_or_create_trace_context,
    reset_trace_context,
    set_trace_context,
)

VALID_SPAN_STATUSES = {
    "STARTED",
    "RUNNING",
    "COMPLETED",
    "FAILED",
    "CANCELLED",
}


@dataclass
class AgentSpan:
    """
    Represents the lifecycle of one agent operation.

    A span belongs to a distributed trace and may have
    a parent span.
    """

    trace_id: str
    span_id: str
    agent: str
    action: str

    parent_span_id: str | None = None

    status: str = "STARTED"

    started_at: datetime = field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )

    ended_at: datetime | None = None

    duration_ms: float | None = None

    attributes: dict[str, Any] = field(
        default_factory=dict
    )

    error: str | None = None

    def __post_init__(self) -> None:
        if self.status not in VALID_SPAN_STATUSES:
            raise ValueError(
                f"Invalid span status: {self.status}"
            )

    def start(self) -> None:
        """
        Move the span into RUNNING state.
        """

        if self.ended_at is not None:
            raise RuntimeError(
                "Cannot start an ended span"
            )

        self.status = "RUNNING"

    def finish(
        self,
        status: str = "COMPLETED",
        error: str | None = None,
    ) -> None:
        """
        Finish the span and calculate its duration.
        """

        if status not in {
            "COMPLETED",
            "FAILED",
            "CANCELLED",
        }:
            raise ValueError(
                f"Invalid terminal span status: {status}"
            )

        if self.ended_at is not None:
            raise RuntimeError(
                "Span has already ended"
            )

        self.ended_at = datetime.now(
            timezone.utc
        )

        self.status = status
        self.error = error

        self.duration_ms = (
            self.ended_at - self.started_at
        ).total_seconds() * 1000

        if self.duration_ms < 0:
            self.duration_ms = 0.0

    def fail(
        self,
        error: str,
    ) -> None:
        """
        Mark the span as failed.
        """

        self.finish(
            status="FAILED",
            error=error,
        )

    def cancel(
        self,
        reason: str | None = None,
    ) -> None:
        """
        Mark the span as cancelled.
        """

        self.finish(
            status="CANCELLED",
            error=reason,
        )

    def set_attribute(
        self,
        key: str,
        value: Any,
    ) -> None:
        """
        Add or update a span attribute.
        """

        self.attributes[key] = value

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize the span.
        """

        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "agent": self.agent,
            "action": self.action,
            "status": self.status,
            "started_at": self.started_at.isoformat(),
            "ended_at": (
                self.ended_at.isoformat()
                if self.ended_at
                else None
            ),
            "duration_ms": self.duration_ms,
            "attributes": dict(self.attributes),
            "error": self.error,
        }

class AgentSpanCollector:
    """
    Thread-safe collector for agent spans.
    """

    def __init__(self) -> None:
        from threading import Lock

        self._lock = Lock()

        self._spans: list[AgentSpan] = []

    def start(
        self,
        *,
        trace_id: str,
        span_id: str,
        agent: str,
        action: str,
        parent_span_id: str | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> AgentSpan:
        """
        Create and register a new span.
        """

        span = AgentSpan(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            agent=agent,
            action=action,
            attributes=dict(
                attributes or {}
            ),
        )

        span.start()

        with self._lock:
            self._spans.append(span)

        return span

    def spans(self) -> list[AgentSpan]:
        """
        Return a snapshot of all spans.
        """

        with self._lock:
            return list(self._spans)

    def completed_spans(self) -> list[AgentSpan]:
        """
        Return spans that have completed.
        """

        with self._lock:
            return [
                span
                for span in self._spans
                if span.ended_at is not None
            ]

    def find(
        self,
        span_id: str,
    ) -> AgentSpan | None:
        """
        Find a span by ID.
        """

        with self._lock:
            for span in self._spans:
                if span.span_id == span_id:
                    return span

        return None

    def to_dict(
        self,
    ) -> list[dict[str, Any]]:
        """
        Serialize all spans.
        """

        with self._lock:
            return [
                span.to_dict()
                for span in self._spans
            ]

    def clear(self) -> None:
        """
        Remove all spans.
        """

        with self._lock:
            self._spans.clear()


@contextmanager
def agent_span(
    collector: AgentSpanCollector,
    *,
    agent: str,
    action: str,
    attributes: dict[str, Any] | None = None,
) -> Iterator[AgentSpan]:
    """
    Create a child span for one agent operation.

    The previous trace context is restored when the
    operation exits.
    """

    parent_context = (
        get_or_create_trace_context()
    )

    child_context = (
        parent_context.child()
    )

    token = set_trace_context(
        child_context
    )

    span = collector.start(
        trace_id=child_context.trace_id,
        span_id=child_context.span_id,
        parent_span_id=(
            child_context.parent_span_id
        ),
        agent=agent,
        action=action,
        attributes=attributes,
    )

    try:

        yield span

    except Exception as exc:

        span.fail(str(exc))

        raise

    else:

        if span.ended_at is None:
            span.finish()

    finally:

        reset_trace_context(token)
