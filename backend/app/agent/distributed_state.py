from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock
from time import monotonic
from typing import Any


@dataclass
class InvestigationExecutionState:
    """
    Runtime scheduling state for one investigation.
    """

    investigation_id: int

    active_tasks: int = 0
    queued_tasks: int = 0

    completed_tasks: int = 0
    failed_tasks: int = 0

    last_agent: str | None = None

    created_at: float = field(
        default_factory=monotonic
    )

    updated_at: float = field(
        default_factory=monotonic
    )

    metadata: dict[str, Any] = field(
        default_factory=dict
    )


class DistributedExecutionState:
    """
    Thread-safe registry containing execution state
    for multiple investigations.

    This is intentionally process-local for now.

    A later production phase can replace the backing
    store with Redis/PostgreSQL without changing the
    scheduling interface.
    """

    def __init__(self) -> None:

        self._lock = Lock()

        self._investigations: dict[
            int,
            InvestigationExecutionState,
        ] = {}

    # =========================================================
    # Investigation registration
    # =========================================================

    def _get_or_create_locked(
        self,
        investigation_id: int,
    ) -> InvestigationExecutionState:

        state = self._investigations.get(
            investigation_id
        )

        if state is None:

            state = InvestigationExecutionState(
                investigation_id=investigation_id
            )

            self._investigations[
                investigation_id
            ] = state

        return state

    # =========================================================
    # State updates
    # =========================================================

    def mark_queued(
        self,
        investigation_id: int,
        *,
        agent_name: str | None = None,
    ) -> None:

        with self._lock:

            state = self._get_or_create_locked(
                investigation_id
            )

            state.queued_tasks += 1

            if agent_name:
                state.last_agent = agent_name

            state.updated_at = monotonic()

    def mark_started(
        self,
        investigation_id: int,
        *,
        agent_name: str | None = None,
    ) -> None:

        with self._lock:

            state = self._get_or_create_locked(
                investigation_id
            )

            if state.queued_tasks > 0:
                state.queued_tasks -= 1

            state.active_tasks += 1

            if agent_name:
                state.last_agent = agent_name

            state.updated_at = monotonic()

    def mark_completed(
        self,
        investigation_id: int,
    ) -> None:

        with self._lock:

            state = self._get_or_create_locked(
                investigation_id
            )

            if state.active_tasks > 0:
                state.active_tasks -= 1

            state.completed_tasks += 1

            state.updated_at = monotonic()

    def mark_failed(
        self,
        investigation_id: int,
    ) -> None:

        with self._lock:

            state = self._get_or_create_locked(
                investigation_id
            )

            if state.active_tasks > 0:
                state.active_tasks -= 1

            state.failed_tasks += 1

            state.updated_at = monotonic()

    # =========================================================
    # Read state
    # =========================================================

    def snapshot(
        self,
        investigation_id: int,
    ) -> dict[str, Any]:

        with self._lock:

            state = self._investigations.get(
                investigation_id
            )

            if state is None:

                return {
                    "investigation_id": investigation_id,
                    "active_tasks": 0,
                    "queued_tasks": 0,
                    "completed_tasks": 0,
                    "failed_tasks": 0,
                    "last_agent": None,
                }

            return {
                "investigation_id": (
                    state.investigation_id
                ),
                "active_tasks": (
                    state.active_tasks
                ),
                "queued_tasks": (
                    state.queued_tasks
                ),
                "completed_tasks": (
                    state.completed_tasks
                ),
                "failed_tasks": (
                    state.failed_tasks
                ),
                "last_agent": state.last_agent,
                "created_at": state.created_at,
                "updated_at": state.updated_at,
                "metadata": dict(
                    state.metadata
                ),
            }

    def all_snapshots(
        self,
    ) -> list[dict[str, Any]]:

        with self._lock:

            ids = list(
                self._investigations.keys()
            )

        return [
            self.snapshot(investigation_id)
            for investigation_id in ids
        ]

    # =========================================================
    # Cleanup
    # =========================================================

    def remove(
        self,
        investigation_id: int,
    ) -> None:

        with self._lock:

            self._investigations.pop(
                investigation_id,
                None,
            )

    def clear(self) -> None:

        with self._lock:

            self._investigations.clear()
