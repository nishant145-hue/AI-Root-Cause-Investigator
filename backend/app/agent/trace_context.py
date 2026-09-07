from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar, Token
from dataclasses import dataclass
from typing import Iterator
from uuid import uuid4


@dataclass(frozen=True)
class TraceContext:
    """
    Distributed execution trace context.

    A trace_id identifies the complete investigation flow.

    A span_id identifies the current execution scope.

    parent_span_id identifies the immediate parent scope.
    """

    trace_id: str
    span_id: str
    parent_span_id: str | None = None

    def child(self) -> "TraceContext":
        """
        Create a child context.

        The child belongs to the same distributed trace,
        receives a new span ID, and points to the current
        span as its parent.
        """

        return TraceContext(
            trace_id=self.trace_id,
            span_id=generate_id(),
            parent_span_id=self.span_id,
        )

    def to_dict(self) -> dict[str, str | None]:
        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
        }


_current_trace_context: ContextVar[
    TraceContext | None
] = ContextVar(
    "agent_trace_context",
    default=None,
)


def generate_id() -> str:
    """
    Generate a unique trace/span identifier.
    """

    return uuid4().hex


def create_trace_context() -> TraceContext:
    """
    Create a new root distributed trace context.
    """

    return TraceContext(
        trace_id=generate_id(),
        span_id=generate_id(),
        parent_span_id=None,
    )


def get_trace_context() -> TraceContext | None:
    """
    Return the current trace context.
    """

    return _current_trace_context.get()


def set_trace_context(
    context: TraceContext,
) -> Token[TraceContext | None]:
    """
    Set the current trace context.

    Returns the ContextVar token so callers can restore
    the previous context safely.
    """

    return _current_trace_context.set(
        context
    )


def reset_trace_context(
    token: Token[TraceContext | None],
) -> None:
    """
    Restore the context that existed before a set operation.
    """

    _current_trace_context.reset(token)


def clear_trace_context() -> None:
    """
    Remove the current trace context.
    """

    _current_trace_context.set(None)


def get_or_create_trace_context() -> TraceContext:
    """
    Return the current context or create a root context
    when no context currently exists.
    """

    context = get_trace_context()

    if context is not None:
        return context

    context = create_trace_context()

    set_trace_context(context)

    return context


def create_child_trace_context() -> TraceContext:
    """
    Create and install a child context.

    If no context exists, a root context is created first.
    """

    parent = get_or_create_trace_context()

    child = parent.child()

    set_trace_context(child)

    return child


@contextmanager
def trace_context(
    context: TraceContext | None = None,
) -> Iterator[TraceContext]:
    """
    Temporarily install a trace context.

    The previous context is always restored when leaving
    the context manager.
    """

    if context is None:
        context = create_trace_context()

    token = set_trace_context(context)

    try:
        yield context

    finally:
        reset_trace_context(token)


@contextmanager
def child_trace_context() -> Iterator[TraceContext]:
    """
    Temporarily install a child trace context.

    The parent context is automatically restored when
    the context manager exits.
    """

    parent = get_or_create_trace_context()

    child = parent.child()

    token = set_trace_context(child)

    try:
        yield child

    finally:
        reset_trace_context(token)
