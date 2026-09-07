from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock
from typing import Any


@dataclass
class InvestigationTrace:
    """
    Aggregated observability record for one investigation.

    This object combines:
    - execution metrics
    - agent spans
    - queue/resource metrics
    - failures
    """

    investigation_id: int

    trace_id: str | None = None

    started_at: float | None = None
    completed_at: float | None = None

    status: str = "RUNNING"

    executions: list[dict[str, Any]] = field(
        default_factory=list
    )

    queue_metrics: list[dict[str, Any]] = field(
        default_factory=list
    )

    spans: list[dict[str, Any]] = field(
        default_factory=list
    )

    failures: list[dict[str, Any]] = field(
        default_factory=list
    )


class InvestigationTraceAggregator:
    """
    Thread-safe investigation-level trace aggregator.

    The aggregator does not execute agents and does not
    modify scheduling behavior.

    It combines telemetry produced by the existing:
    - AgentExecutionMetrics
    - AgentSpanCollector
    - AgentResourceMetrics
    - FailureTelemetryCollector
    """

    def __init__(self) -> None:
        self._lock = Lock()

        self._traces: dict[
            int,
            InvestigationTrace,
        ] = {}

    # =========================================================
    # Investigation lifecycle
    # =========================================================

    def start_investigation(
        self,
        investigation_id: int,
        *,
        trace_id: str | None = None,
        started_at: float | None = None,
    ) -> InvestigationTrace:
        """
        Create or update an investigation trace.
        """

        with self._lock:

            trace = self._traces.get(
                investigation_id
            )

            if trace is None:

                trace = InvestigationTrace(
                    investigation_id=(
                        investigation_id
                    ),
                    trace_id=trace_id,
                    started_at=started_at,
                    status="RUNNING",
                )

                self._traces[
                    investigation_id
                ] = trace

            else:

                if trace_id is not None:
                    trace.trace_id = trace_id

                if (
                    trace.started_at is None
                    and started_at is not None
                ):
                    trace.started_at = started_at

                trace.status = "RUNNING"

            return trace

    def finish_investigation(
        self,
        investigation_id: int,
        *,
        completed_at: float | None = None,
        status: str = "COMPLETED",
    ) -> InvestigationTrace | None:
        """
        Finish an investigation trace.
        """

        with self._lock:

            trace = self._traces.get(
                investigation_id
            )

            if trace is None:
                return None

            trace.completed_at = completed_at
            trace.status = status

            return trace

    # =========================================================
    # Recording
    # =========================================================

    def record_execution(
    self,
    execution: dict[str, Any],
) -> None:
        """
        Add one execution metric to the investigation.
        """

        investigation_id = execution.get(
            "investigation_id"
        )

        if investigation_id is None:
            return

        with self._lock:

            trace = self._traces.setdefault(
            investigation_id,
            InvestigationTrace(
                investigation_id=(
                    investigation_id
                )
            ),
        )

            trace.executions.append(
                dict(execution)
            )

            trace_id = execution.get(
            "trace_id"
        )

            if (
            trace.trace_id is None
            and trace_id is not None
        ):
                trace.trace_id = trace_id

            started_at = execution.get(
                "started_at"
            )

            if (
                trace.started_at is None
                and started_at is not None
            ):
                trace.started_at = started_at

    def record_queue_metric(
        self,
        queue_metric: dict[str, Any],
    ) -> None:
        """
        Add queue/resource telemetry.
        """

        investigation_id = (
            queue_metric.get(
                "investigation_id"
            )
        )

        if investigation_id is None:
            return

        with self._lock:

            trace = self._traces.setdefault(
                investigation_id,
                InvestigationTrace(
                    investigation_id=(
                        investigation_id
                    )
                ),
            )

            trace.queue_metrics.append(
                dict(queue_metric)
            )

    def record_span(
        self,
        span: dict[str, Any],
    ) -> None:
        """
        Add an agent span to the investigation trace.

        Investigation ID is normally stored in the
        span attributes by AgentExecutionManager.
        """

        attributes = span.get(
            "attributes"
        ) or {}

        investigation_id = attributes.get(
            "investigation_id"
        )

        if investigation_id is None:
            return

        with self._lock:

            trace = self._traces.setdefault(
                int(investigation_id),
                InvestigationTrace(
                    investigation_id=(
                        int(investigation_id)
                    )
                ),
            )

            trace.spans.append(
                dict(span)
            )

            trace_id = span.get(
                "trace_id"
            )

            if (
                trace.trace_id is None
                and trace_id is not None
            ):
                trace.trace_id = trace_id

    def record_failure(
        self,
        failure: dict[str, Any],
    ) -> None:
        """
        Add failure/retry/timeout telemetry.
        """

        investigation_id = (
            failure.get(
                "investigation_id"
            )
        )

        if investigation_id is None:
            return

        with self._lock:

            trace = self._traces.setdefault(
                investigation_id,
                InvestigationTrace(
                    investigation_id=(
                        investigation_id
                    )
                ),
            )

            trace.failures.append(
                dict(failure)
            )

    # =========================================================
    # Retrieval
    # =========================================================

    def get(
        self,
        investigation_id: int,
    ) -> InvestigationTrace | None:

        with self._lock:

            return self._traces.get(
                investigation_id
            )

    def all(
        self,
    ) -> list[InvestigationTrace]:

        with self._lock:

            return list(
                self._traces.values()
            )

    # =========================================================
    # Timeline
    # =========================================================

    def timeline(
        self,
        investigation_id: int,
    ) -> list[dict[str, Any]]:

        with self._lock:

            trace = self._traces.get(
                investigation_id
            )

            if trace is None:
                return []

            timeline: list[
                dict[str, Any]
            ] = []

            for execution in trace.executions:

                started_at = execution.get(
                    "started_at"
                )

                completed_at = execution.get(
                    "completed_at"
                )

                queue_metric = (
                    self._queue_metric_for_execution(
                        trace.queue_metrics,
                        execution.get(
                            "execution_id"
                        ),
                    )
                )

                timeline.append(
                    {
                        "execution_id": (
                            execution.get(
                                "execution_id"
                            )
                        ),
                        "agent_name": (
                            execution.get(
                                "agent_name"
                            )
                        ),
                        "trace_id": (
                            execution.get(
                                "trace_id"
                            )
                        ),
                        "span_id": (
                            execution.get(
                                "span_id"
                            )
                        ),
                        "parent_span_id": (
                            execution.get(
                                "parent_span_id"
                            )
                        ),
                        "started_at": started_at,
                        "completed_at": completed_at,
                        "duration_ms": (
                            execution.get(
                                "duration_ms"
                            )
                        ),
                        "queue_wait_ms": (
                            queue_metric.get(
                                "queue_wait_ms"
                            )
                            if queue_metric
                            else 0.0
                        ),
                        "status": (
                            execution.get(
                                "status"
                            )
                        ),
                        "error": (
                            execution.get(
                                "error"
                            )
                        ),
                    }
                )

            timeline.sort(
                key=lambda item: (
                    item.get(
                        "started_at"
                    )
                    is None,
                    item.get(
                        "started_at"
                    )
                    or 0.0,
                )
            )

            return timeline

    @staticmethod
    def _queue_metric_for_execution(
        queue_metrics: list[
            dict[str, Any]
        ],
        execution_id: str | None,
    ) -> dict[str, Any] | None:

        if execution_id is None:
            return None

        for metric in queue_metrics:

            if (
                metric.get(
                    "execution_id"
                )
                == execution_id
            ):
                return metric

        return None

    # =========================================================
    # Aggregate statistics
    # =========================================================

    def summary(
        self,
        investigation_id: int,
    ) -> dict[str, Any]:

        with self._lock:

            trace = self._traces.get(
                investigation_id
            )

            if trace is None:

                return {
                    "investigation_id": (
                        investigation_id
                    ),
                    "trace_id": None,
                    "status": "NOT_FOUND",
                    "agent_count": 0,
                    "completed_count": 0,
                    "failed_count": 0,
                    "cancelled_count": 0,
                    "total_duration_ms": 0.0,
                    "total_queue_wait_ms": 0.0,
                    "average_queue_wait_ms": 0.0,
                    "retry_count": 0,
                    "timeout_count": 0,
                    "critical_path_ms": 0.0,
                }

            executions = trace.executions

            completed_count = sum(
                1
                for execution in executions
                if execution.get("status")
                == "COMPLETED"
            )

            failed_count = sum(
                1
                for execution in executions
                if execution.get("status")
                == "FAILED"
            )

            cancelled_count = sum(
                1
                for execution in executions
                if execution.get("status")
                == "CANCELLED"
            )

            total_queue_wait_ms = sum(
                float(
                    metric.get(
                        "queue_wait_ms",
                        0.0,
                    )
                )
                for metric in trace.queue_metrics
            )

            queue_count = len(
                trace.queue_metrics
            )

            average_queue_wait_ms = (
                total_queue_wait_ms
                / queue_count
                if queue_count
                else 0.0
            )

            total_duration_ms = self._total_duration(
                trace
            )

            retry_count = self._count_failures_by_type(
                trace.failures,
                "retry",
            )

            timeout_count = self._count_failures_by_type(
                trace.failures,
                "timeout",
            )

            return {
                "investigation_id": (
                    investigation_id
                ),
                "trace_id": trace.trace_id,
                "status": trace.status,
                "agent_count": len(
                    executions
                ),
                "completed_count": (
                    completed_count
                ),
                "failed_count": failed_count,
                "cancelled_count": (
                    cancelled_count
                ),
                "total_duration_ms": round(
                    total_duration_ms,
                    2,
                ),
                "total_queue_wait_ms": round(
                    total_queue_wait_ms,
                    2,
                ),
                "average_queue_wait_ms": round(
                    average_queue_wait_ms,
                    2,
                ),
                "retry_count": retry_count,
                "timeout_count": timeout_count,
                "critical_path_ms": round(
                    self._critical_path(
                        trace
                    ),
                    2,
                ),
            }

    @staticmethod
    def _total_duration(
        trace: InvestigationTrace,
    ) -> float:

        if (
            trace.started_at is not None
            and trace.completed_at is not None
        ):
            return max(
                0.0,
                (
                    trace.completed_at
                    - trace.started_at
                )
                * 1000,
            )

        durations = [
            float(
                execution.get(
                    "duration_ms",
                    0.0,
                )
            )
            for execution in trace.executions
        ]

        return sum(durations)



    @staticmethod
    def _count_failures_by_type(
        failures: list[dict[str, Any]],
        event_type: str,
    ) -> int:
        """
        Count failure telemetry events by event type.

        Retry and timeout telemetry are stored together with
        investigation failures, so this helper normalizes
        both the explicit event_type field and common
        telemetry naming conventions.
        """

        normalized_type = event_type.upper()

        count = 0

        for failure in failures:

            failure_event_type = str(
                failure.get(
                    "event_type",
                    ""
                )
            ).upper()

            failure_type = str(
                failure.get(
                    "failure_type",
                    ""
                )
            ).upper()

            if normalized_type == "RETRY":

                if (
                    failure_event_type
                    in {
                        "AGENT_RETRY",
                        "RETRY",
                    }
                    or failure_type == "RETRY"
                ):
                    count += 1

            elif normalized_type == "TIMEOUT":

                if (
                    failure_event_type
                    in {
                        "AGENT_TIMEOUT",
                        "TIMEOUT",
                    }
                    or failure_type == "TIMEOUT"
                ):
                    count += 1

        return count
    # =========================================================
    # Critical path
    # =========================================================

    def critical_path(
        self,
        investigation_id: int,
    ) -> dict[str, Any]:

        with self._lock:

            trace = self._traces.get(
                investigation_id
            )

            if trace is None:
                return {
                    "investigation_id": (
                        investigation_id
                    ),
                    "critical_path_ms": 0.0,
                    "executions": [],
                }

            executions = list(
                trace.executions
            )

            if not executions:
                return {
                    "investigation_id": (
                        investigation_id
                    ),
                    "critical_path_ms": 0.0,
                    "executions": [],
                }

            execution_by_span = {
                execution.get(
                    "span_id"
                ): execution
                for execution in executions
            }

            memo: dict[str, float] = {}
            path_memo: dict[
                str,
                list[str],
            ] = {}

            def longest_path(
                span_id: str,
                visiting: set[str] | None = None,
            ) -> tuple[
                float,
                list[str],
            ]:

                if span_id in memo:
                    return (
                        memo[span_id],
                        path_memo[span_id],
                    )

                if visiting is None:
                    visiting = set()

                if span_id in visiting:
                    return (
                        0.0,
                        [],
                    )

                execution = execution_by_span.get(
                    span_id
                )

                if execution is None:
                    return (
                        0.0,
                        [],
                    )

                visiting = set(visiting)
                visiting.add(span_id)

                duration = float(
                    execution.get(
                        "duration_ms",
                        0.0,
                    )
                )

                children = [
                    child
                    for child in executions
                    if child.get(
                        "parent_span_id"
                    )
                    == span_id
                ]

                best_child_duration = 0.0
                best_child_path: list[str] = []

                for child in children:

                    child_span_id = child.get(
                        "span_id"
                    )

                    if child_span_id is None:
                        continue

                    child_duration, child_path = (
                        longest_path(
                            child_span_id,
                            visiting,
                        )
                    )

                    if (
                        child_duration
                        > best_child_duration
                    ):
                        best_child_duration = (
                            child_duration
                        )
                        best_child_path = (
                            child_path
                        )

                total = (
                    duration
                    + best_child_duration
                )

                path = [
                    execution.get(
                        "execution_id"
                    )
                ] + best_child_path

                memo[span_id] = total
                path_memo[span_id] = path

                return total, path

            roots = [
                execution
                for execution in executions
                if execution.get(
                    "parent_span_id"
                )
                not in execution_by_span
            ]

            best_duration = 0.0
            best_path: list[str] = []

            for root in roots:

                span_id = root.get(
                    "span_id"
                )

                if span_id is None:
                    continue

                duration, path = longest_path(
                    span_id
                )

                if duration > best_duration:

                    best_duration = duration
                    best_path = path

            return {
                "investigation_id": (
                    investigation_id
                ),
                "critical_path_ms": round(
                    best_duration,
                    2,
                ),
                "executions": best_path,
            }


    def _critical_path(
        self,
        trace: InvestigationTrace,
    ) -> float:
        """
        Calculate the critical-path duration for an already
        loaded investigation trace.

        This internal helper is used by summary() so that
        summary generation does not need to perform another
        investigation lookup.
        """

        executions = trace.executions

        if not executions:
            return 0.0

        execution_by_id = {
            execution["execution_id"]: execution
            for execution in executions
            if execution.get("execution_id")
        }

        memo: dict[str, float] = {}

        def duration(execution: dict[str, Any]) -> float:
            return float(
                execution.get(
                    "duration_ms",
                    0.0,
                )
            )

        def longest_path(
            execution_id: str,
            visiting: set[str] | None = None,
        ) -> float:

            if execution_id in memo:
                return memo[execution_id]

            if visiting is None:
                visiting = set()

            # Protect against malformed/cyclic parent relationships.
            if execution_id in visiting:
                return duration(
                    execution_by_id[execution_id]
                )

            execution = execution_by_id.get(
                execution_id
            )

            if execution is None:
                return 0.0

            visiting = set(visiting)
            visiting.add(execution_id)

            parent_span_id = execution.get(
                "parent_span_id"
            )

            parent = None

            if parent_span_id:
                for candidate in executions:
                    if (
                        candidate.get("span_id")
                        == parent_span_id
                    ):
                        parent = candidate
                        break

            current_duration = duration(
                execution
            )

            if parent is None:
                result = current_duration
            else:
                result = (
                    current_duration
                    + longest_path(
                        parent["execution_id"],
                        visiting,
                    )
                )

            memo[execution_id] = result

            return result

        return max(
            (
                longest_path(
                    execution["execution_id"]
                )
                for execution in executions
                if execution.get("execution_id")
            ),
            default=0.0,
        )
    # =========================================================
    # Snapshot
    # =========================================================

    def snapshot(
        self,
        investigation_id: int,
    ) -> dict[str, Any]:

        with self._lock:

            trace = self._traces.get(
                investigation_id
            )

            if trace is None:
                return {
                    "investigation_id": (
                        investigation_id
                    ),
                    "trace_id": None,
                    "started_at": None,
                    "completed_at": None,
                    "status": "NOT_FOUND",
                    "executions": [],
                    "queue_metrics": [],
                    "spans": [],
                    "failures": [],
                }

            return {
                "investigation_id": (
                    investigation_id
                ),
                "trace_id": trace.trace_id,
                "started_at": trace.started_at,
                "completed_at": trace.completed_at,
                "status": trace.status,
                "executions": [
                    dict(item)
                    for item in trace.executions
                ],
                "queue_metrics": [
                    dict(item)
                    for item in trace.queue_metrics
                ],
                "spans": [
                    dict(item)
                    for item in trace.spans
                ],
                "failures": [
                    dict(item)
                    for item in trace.failures
                ],
            }

    # =========================================================
    # Reset
    # =========================================================

    def reset(
        self,
        investigation_id: int | None = None,
    ) -> None:

        with self._lock:

            if investigation_id is None:

                self._traces.clear()

            else:

                self._traces.pop(
                    investigation_id,
                    None,
                )
