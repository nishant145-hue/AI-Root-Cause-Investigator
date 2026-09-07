from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator

from app.core.logging import logger


AGENT_LOG_EVENTS = {
    "agent_execution_started",
    "agent_execution_completed",
    "agent_execution_failed",
    "agent_execution_cancelled",
    "agent_execution_timeout",
    "agent_execution_retry",
    "agent_execution_rerouted",
}


def _clean_context(
    context: dict[str, Any],
) -> dict[str, Any]:
    """
    Remove None values so structured logs remain compact
    and machine-friendly.
    """

    return {
        key: value
        for key, value in context.items()
        if value is not None
    }


def log_agent_event(
    event: str,
    *,
    level: str = "INFO",
    **context: Any,
) -> None:
    """
    Emit a structured agent observability event.

    All agent-specific identifiers are stored in Loguru's
    structured extra/context fields.
    """

    if not event:
        raise ValueError("event must not be empty")

    if event not in AGENT_LOG_EVENTS:
        raise ValueError(
            f"Unsupported agent log event: {event}"
        )

    payload = _clean_context(context)

    message = f"agent_event={event}"

    log_method = getattr(
        logger,
        level.lower(),
        None,
    )

    if log_method is None:
        raise ValueError(
            f"Unsupported log level: {level}"
        )

    log_method(
        message,
        event=event,
        **payload,
    )


@contextmanager
def agent_log_context(
    *,
    investigation_id: int | None = None,
    execution_id: str | None = None,
    agent_name: str | None = None,
    trace_id: str | None = None,
    span_id: str | None = None,
    parent_span_id: str | None = None,
    **extra: Any,
) -> Iterator[None]:
    """
    Attach agent execution identifiers to all logs emitted
    inside the context.
    """

    context = _clean_context(
        {
            "investigation_id": investigation_id,
            "execution_id": execution_id,
            "agent_name": agent_name,
            "trace_id": trace_id,
            "span_id": span_id,
            "parent_span_id": parent_span_id,
            **extra,
        }
    )

    with logger.contextualize(**context):
        yield
