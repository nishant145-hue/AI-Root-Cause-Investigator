from __future__ import annotations

from dataclasses import dataclass
from threading import Lock
from time import monotonic
from typing import Any


@dataclass(frozen=True)
class ExecutionMetric:
    """
    Runtime metrics for one distributed agent execution.
    """

    execution_id: str
    investigation_id: int | None
    agent_name: str

    trace_id: str
    span_id: str
    parent_span_id: str | None

    started_at: float
    completed_at: float

    duration_ms: float

    status: str
    error: str | None = None


class AgentExecutionMetrics:
    """
    Thread-safe runtime metrics collector for the
    AgentExecutionManager.

    This collector is intentionally separate from the
    investigation execution analytics layer.

    Responsibilities:
    - record individual execution outcomes
    - track execution duration
    - track success/failure/cancellation
    - maintain aggregate per-agent statistics
    - expose thread-safe snapshots
    """

    def __init__(self) -> None:
        self._lock = Lock()

        self._executions: list[
            ExecutionMetric
        ] = []

        self._total_executions = 0
        self._successful_executions = 0
        self._failed_executions = 0
        self._cancelled_executions = 0

        self._total_duration_ms = 0.0

        self._agent_statistics: dict[
            str,
            dict[str, Any],
        ] = {}

    # =========================================================
    # Recording
    # =========================================================

    def record(
        self,
        *,
        execution_id: str,
        investigation_id: int | None,
        agent_name: str,
        trace_id: str,
        span_id: str,
        parent_span_id: str | None,
        started_at: float,
        status: str,
        error: str | None = None,
    ) -> ExecutionMetric:
        """
        Record one completed execution.

        `started_at` is expected to come from the execution
        manager's monotonic clock.
        """

        completed_at = monotonic()

        duration_ms = max(
            0.0,
            (completed_at - started_at) * 1000,
        )

        metric = ExecutionMetric(
            execution_id=execution_id,
            investigation_id=investigation_id,
            agent_name=agent_name,
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            started_at=started_at,
            completed_at=completed_at,
            duration_ms=duration_ms,
            status=status,
            error=error,
        )

        with self._lock:

            self._executions.append(metric)

            self._total_executions += 1

            self._total_duration_ms += duration_ms

            if status == "COMPLETED":
                self._successful_executions += 1

            elif status == "CANCELLED":
                self._cancelled_executions += 1

            else:
                self._failed_executions += 1

            statistics = self._agent_statistics.setdefault(
                agent_name,
                {
                    "execution_count": 0,
                    "success_count": 0,
                    "failure_count": 0,
                    "cancelled_count": 0,
                    "total_duration_ms": 0.0,
                    "average_duration_ms": 0.0,
                },
            )

            statistics["execution_count"] += 1

            if status == "COMPLETED":
                statistics["success_count"] += 1

            elif status == "CANCELLED":
                statistics["cancelled_count"] += 1

            else:
                statistics["failure_count"] += 1

            statistics["total_duration_ms"] += (
                duration_ms
            )

            execution_count = int(
                statistics["execution_count"]
            )

            statistics["average_duration_ms"] = (
                statistics["total_duration_ms"]
                / execution_count
            )

        return metric

    # =========================================================
    # Individual execution metrics
    # =========================================================

    def executions(
        self,
    ) -> list[ExecutionMetric]:

        with self._lock:
            return list(self._executions)

    # =========================================================
    # Aggregate metrics
    # =========================================================

    def snapshot(
        self,
    ) -> dict[str, Any]:

        with self._lock:

            average_duration_ms = (
                self._total_duration_ms
                / self._total_executions
                if self._total_executions
                else 0.0
            )

            return {
                "total_executions": (
                    self._total_executions
                ),
                "successful_executions": (
                    self._successful_executions
                ),
                "failed_executions": (
                    self._failed_executions
                ),
                "cancelled_executions": (
                    self._cancelled_executions
                ),
                "total_duration_ms": round(
                    self._total_duration_ms,
                    2,
                ),
                "average_duration_ms": round(
                    average_duration_ms,
                    2,
                ),
                "agent_statistics": {
                    agent: {
                        **statistics,
                        "total_duration_ms": round(
                            float(
                                statistics[
                                    "total_duration_ms"
                                ]
                            ),
                            2,
                        ),
                        "average_duration_ms": round(
                            float(
                                statistics[
                                    "average_duration_ms"
                                ]
                            ),
                            2,
                        ),
                    }
                    for agent, statistics
                    in self._agent_statistics.items()
                },
            }

    # =========================================================
    # Reset
    # =========================================================

    def reset(self) -> None:

        with self._lock:

            self._executions.clear()

            self._total_executions = 0
            self._successful_executions = 0
            self._failed_executions = 0
            self._cancelled_executions = 0

            self._total_duration_ms = 0.0

            self._agent_statistics.clear()
