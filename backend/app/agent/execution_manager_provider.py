from __future__ import annotations

from threading import Lock

from app.agent.execution_manager import (
    AgentExecutionManager,
)
from app.core.config import settings


_manager: AgentExecutionManager | None = None
_lock = Lock()


def get_execution_manager() -> AgentExecutionManager:
    """
    Return the application-wide AgentExecutionManager.

    The manager is lazily initialized and shared across all
    API requests so observability endpoints inspect the same
    telemetry collectors used by agent execution.
    """

    global _manager

    if _manager is not None:
        return _manager

    with _lock:

        if _manager is None:

            _manager = AgentExecutionManager(
                max_workers=10,
                max_per_investigation=3,
                max_queue_size=20,
            )

    return _manager


def shutdown_execution_manager() -> None:
    """
    Shutdown the application-wide execution manager.
    """

    global _manager

    with _lock:

        if _manager is not None:

            _manager.shutdown(
                wait=True,
                cancel_futures=True,
            )

            _manager = None
