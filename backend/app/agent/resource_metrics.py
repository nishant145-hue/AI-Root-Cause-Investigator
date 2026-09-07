from __future__ import annotations

from dataclasses import dataclass
from threading import Lock
from time import monotonic
from typing import Any


@dataclass(frozen=True)
class QueueMetric:
    execution_id: str
    investigation_id: int | None
    agent_name: str

    queued_at: float
    started_at: float
    queue_wait_ms: float

    queue_depth_at_submit: int
    queue_depth_at_start: int


class AgentResourceMetrics:
    """
    Thread-safe queue and worker resource telemetry.

    This collector observes execution resources without
    changing scheduling or admission-control behavior.
    """

    def __init__(self) -> None:
        self._lock = Lock()

        self._queue_metrics: list[QueueMetric] = []

        self._queued_count = 0
        self._rejected_count = 0

        self._max_queue_depth = 0
        self._total_queue_wait_ms = 0.0

        self._active_workers = 0
        self._max_active_workers = 0

    # =========================================================
    # Queue lifecycle
    # =========================================================

    def record_queued(
        self,
        *,
        queue_depth: int,
    ) -> None:
        with self._lock:
            self._queued_count += 1
            self._max_queue_depth = max(
                self._max_queue_depth,
                queue_depth,
            )

    def record_started(
        self,
        *,
        execution_id: str,
        investigation_id: int | None,
        agent_name: str,
        queued_at: float,
        started_at: float,
        queue_depth_at_submit: int,
        queue_depth_at_start: int,
    ) -> QueueMetric:

        queue_wait_ms = max(
            0.0,
            (started_at - queued_at) * 1000,
        )

        metric = QueueMetric(
            execution_id=execution_id,
            investigation_id=investigation_id,
            agent_name=agent_name,
            queued_at=queued_at,
            started_at=started_at,
            queue_wait_ms=queue_wait_ms,
            queue_depth_at_submit=queue_depth_at_submit,
            queue_depth_at_start=queue_depth_at_start,
        )

        with self._lock:
            self._queue_metrics.append(metric)

            self._queued_count = max(
                0,
                self._queued_count - 1,
            )

            self._total_queue_wait_ms += (
                queue_wait_ms
            )

        return metric

    def record_worker_acquired(self) -> None:
        with self._lock:
            self._active_workers += 1
            self._max_active_workers = max(
                self._max_active_workers,
                self._active_workers,
            )

    def record_worker_released(self) -> None:
        with self._lock:
            self._active_workers = max(
                0,
                self._active_workers - 1,
            )

    def record_rejection(self) -> None:
        with self._lock:
            self._rejected_count += 1

    # =========================================================
    # Snapshot
    # =========================================================

    def snapshot(
        self,
        *,
        max_workers: int,
        max_queue_size: int,
    ) -> dict[str, Any]:

        with self._lock:
            average_queue_wait_ms = (
                self._total_queue_wait_ms
                / len(self._queue_metrics)
                if self._queue_metrics
                else 0.0
            )

            worker_utilization = (
                self._active_workers
                / max_workers
                if max_workers > 0
                else 0.0
            )

            queue_utilization = (
                self._queued_count
                / max_queue_size
                if max_queue_size > 0
                else 0.0
            )

            return {
                "queued_count": self._queued_count,
                "rejected_count": self._rejected_count,
                "max_queue_depth": self._max_queue_depth,
                "max_queue_size": max_queue_size,
                "queue_available": max(
                    0,
                    max_queue_size
                    - self._queued_count,
                ),
                "queue_utilization": round(
                    queue_utilization,
                    4,
                ),
                "average_queue_wait_ms": round(
                    average_queue_wait_ms,
                    2,
                ),
                "active_workers": self._active_workers,
                "max_active_workers": (
                    self._max_active_workers
                ),
                "max_workers": max_workers,
                "available_workers": max(
                    0,
                    max_workers
                    - self._active_workers,
                ),
                "worker_utilization": round(
                    worker_utilization,
                    4,
                ),
            }

    def history(self) -> list[dict[str, Any]]:
        with self._lock:
            return [
                {
                    "execution_id": metric.execution_id,
                    "investigation_id": (
                        metric.investigation_id
                    ),
                    "agent_name": metric.agent_name,
                    "queued_at": metric.queued_at,
                    "started_at": metric.started_at,
                    "queue_wait_ms": round(
                        metric.queue_wait_ms,
                        2,
                    ),
                    "queue_depth_at_submit": (
                        metric.queue_depth_at_submit
                    ),
                    "queue_depth_at_start": (
                        metric.queue_depth_at_start
                    ),
                }
                for metric in self._queue_metrics
            ]

    def reset(self) -> None:
        with self._lock:
            self._queue_metrics.clear()
            self._queued_count = 0
            self._rejected_count = 0
            self._max_queue_depth = 0
            self._total_queue_wait_ms = 0.0
            self._active_workers = 0
            self._max_active_workers = 0
