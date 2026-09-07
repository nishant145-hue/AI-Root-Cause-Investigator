from __future__ import annotations

from concurrent.futures import (
    Future,
    ThreadPoolExecutor,
)
from dataclasses import dataclass, replace
from threading import Condition, Lock
from time import monotonic
from typing import Any, Callable

from app.agent.distributed_state import (
    DistributedExecutionState,
)
from app.agent.execution_metrics import (
    AgentExecutionMetrics,
)
from app.agent.failure_telemetry import (
    FailureTelemetryCollector,
)
from app.agent.investigation_trace import (
    InvestigationTraceAggregator,
)
from app.agent.observability_export import (
    ObservabilityExporter,
)
from app.agent.resource_metrics import (
    AgentResourceMetrics,
)
from app.agent.spans import (
    AgentSpan,
    AgentSpanCollector,
)
from app.agent.structured_logging import (
    agent_log_context,
    log_agent_event,
)
from app.agent.trace_context import (
    TraceContext,
    get_or_create_trace_context,
)


class AgentExecutionError(RuntimeError):
    """Base error for agent execution failures."""


class AgentResourceExhaustedError(
    AgentExecutionError
):
    """Raised when execution capacity is exhausted."""


class AgentQueueFullError(
    AgentResourceExhaustedError
):
    """Raised when the bounded execution queue is full."""


@dataclass(frozen=True)
class AgentExecution:
    execution_id: str
    investigation_id: int | None
    agent_name: str

    started_at: float
    queued_at: float

    queue_depth_at_submit: int

    trace_id: str
    span_id: str
    parent_span_id: str | None = None

    span: AgentSpan | None = None


class AgentExecutionManager:
    """
    Manages concurrent agent execution with:

    - global concurrency limits
    - per-investigation limits
    - bounded queue
    - queue timeout
    - resource isolation
    - automatic cleanup
    - distributed execution state
    - safe shutdown
    """

    def __init__(
        self,
        *,
        max_workers: int = 10,
        max_per_investigation: int = 3,
        max_queue_size: int = 20,
    ) -> None:

        if max_workers < 1:
            raise ValueError(
                "max_workers must be >= 1"
            )

        if max_per_investigation < 1:
            raise ValueError(
                "max_per_investigation must be >= 1"
            )

        if max_per_investigation > max_workers:
            raise ValueError(
                "max_per_investigation cannot "
                "exceed max_workers"
            )

        if max_queue_size < 0:
            raise ValueError(
                "max_queue_size must be >= 0"
            )

        self.max_workers = max_workers
        self.max_per_investigation = (
            max_per_investigation
        )
        self.max_queue_size = max_queue_size

        self._executor = ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="agent-worker",
        )

        self._lock = Lock()

        self._condition = Condition(
            self._lock
        )

        self._active: dict[
            str,
            AgentExecution,
        ] = {}

        self._active_by_investigation: dict[
            int,
            set[str],
        ] = {}

        self._queued = 0

        self._counter = 0

        self._closed = False

        self.distributed_state = (
            DistributedExecutionState()
        )

        self.execution_metrics = (
            AgentExecutionMetrics()
        )

        self.span_collector = (
            AgentSpanCollector()
        )

        self.failure_telemetry = (
            FailureTelemetryCollector()
        )

        self.resource_metrics = (
            AgentResourceMetrics()
        )

        self.investigation_traces = (
            InvestigationTraceAggregator()
        )

        self.observability_exporter = (
            ObservabilityExporter(
                investigation_traces=(
                    self.investigation_traces
                ),
                execution_metrics=(
                    self.execution_metrics
                ),
                resource_metrics=(
                    self.resource_metrics
                ),
                failure_telemetry=(
                    self.failure_telemetry
                ),
                max_workers=self.max_workers,
                max_queue_size=self.max_queue_size,
            )
        )

        self._terminalized: set[str] = set()
    # =========================================================
    # Execution IDs
    # =========================================================

    def _next_execution_id(
        self,
        agent_name: str,
    ) -> str:

        self._counter += 1

        return (
            f"{agent_name}-"
            f"{self._counter}"
        )

    # =========================================================
    # Capacity
    # =========================================================

    def _global_capacity_available(
        self,
    ) -> bool:

        return (
            len(self._active)
            < self.max_workers
        )

    def _investigation_capacity_available(
        self,
        investigation_id: int | None,
    ) -> bool:

        if investigation_id is None:
            return True

        active = (
            self._active_by_investigation.get(
                investigation_id,
                set(),
            )
        )

        return (
            len(active)
            < self.max_per_investigation
        )

    # =========================================================
    # Queue capacity
    # =========================================================

    def _queue_capacity_available(
        self,
    ) -> bool:

        return (
            self._queued
            < self.max_queue_size
        )

    # =========================================================
    # Registration
    # =========================================================

    def _register(
        self,
        *,
        investigation_id: int | None,
        agent_name: str,
    ) -> AgentExecution:

        with self._condition:

            if self._closed:
                raise AgentExecutionError(
                    "AgentExecutionManager is closed."
                )

            # -------------------------------------------------
            # Global capacity
            # -------------------------------------------------
            if not self._global_capacity_available():

                raise AgentResourceExhaustedError(
                    "Global agent execution capacity "
                    "has been exhausted."
                )

            # -------------------------------------------------
            # Per-investigation capacity
            # -------------------------------------------------
            if not self._investigation_capacity_available(
                investigation_id
            ):

                raise AgentResourceExhaustedError(
                    "Investigation agent execution "
                    "capacity has been exhausted."
                )

            trace_context = get_or_create_trace_context()

            span_context = trace_context.child()

            execution_id = self._next_execution_id(
                agent_name
            )

            execution = AgentExecution(
                execution_id=execution_id,
                investigation_id=investigation_id,
                agent_name=agent_name,
                started_at=monotonic(),
                trace_id=span_context.trace_id,
                span_id=span_context.span_id,
                parent_span_id=span_context.parent_span_id,
                queued_at=monotonic(),
                queue_depth_at_submit=self._queued,
            )

            span = self.span_collector.start(
                trace_id=execution.trace_id,
                span_id=execution.span_id,
                parent_span_id=execution.parent_span_id,
                agent=agent_name,
                action="agent_execution",
                attributes={
                    "execution_id": execution.execution_id,
                    "investigation_id": investigation_id,
                },
            )

            execution = AgentExecution(
                execution_id=execution.execution_id,
                investigation_id=execution.investigation_id,
                agent_name=execution.agent_name,
                started_at=execution.started_at,
                queued_at=execution.queued_at,
                queue_depth_at_submit=(
                    execution.queue_depth_at_submit
                ),
                trace_id=execution.trace_id,
                span_id=execution.span_id,
                parent_span_id=execution.parent_span_id,
                span=span,
            )

            # -------------------------------------------------
            # Distributed state
            # -------------------------------------------------

            if investigation_id is not None:

                self.distributed_state.mark_started(
                    investigation_id,
                    agent_name=agent_name,
                )

            # -------------------------------------------------
            # Register active execution
            # -------------------------------------------------
            self._active[
                execution_id
            ] = execution

            if investigation_id is not None:

                self._active_by_investigation.setdefault(
                    investigation_id,
                    set(),
                ).add(
                    execution_id
                )

            return execution

    # =========================================================
    # Release
    # =========================================================

    def _release(
        self,
        execution_id: str,
    ) -> None:
        """
        Release an active execution.

        This method is idempotent. If the execution has
        already been released, nothing happens.

        This is important because both:
        - the Future completion callback
        - synchronous run()

        may attempt cleanup.
        """

        with self._condition:

            execution = self._active.pop(
                execution_id,
                None,
            )

            if execution is None:
                return

            investigation_id = (
                execution.investigation_id
            )

            if investigation_id is not None:

                active = (
                    self._active_by_investigation.get(
                        investigation_id
                    )
                )

                if active is not None:

                    active.discard(
                        execution_id
                    )

                    if not active:
                        self._active_by_investigation.pop(
                            investigation_id,
                            None,
                        )

            self._condition.notify_all()


    def _finalize_execution(
        self,
        execution: AgentExecution,
        *,
        status: str,
        error: str | None = None,
    ) -> None:
        """
        Finalize an execution exactly once.

        This method performs all terminal telemetry before the
        Future becomes observable as completed.
        """

        with self._lock:

            if execution.execution_id in self._terminalized:
                return

            self._terminalized.add(
                execution.execution_id
            )

        # -------------------------------------------------
        # Span lifecycle
        # -------------------------------------------------

        if execution.span is not None:

            if status == "COMPLETED":

                execution.span.finish()

            elif status == "FAILED":

                execution.span.fail(
                    error
                    or "Agent execution failed"
                )

            elif status == "CANCELLED":

                execution.span.cancel(
                    error
                )

            self.investigation_traces.record_span(
                execution.span.to_dict()
            )

        # -------------------------------------------------
        # Failure telemetry
        # -------------------------------------------------

        if status == "FAILED":

            self.failure_telemetry.record_failure(
                execution_id=(
                    execution.execution_id
                ),
                investigation_id=(
                    execution.investigation_id
                ),
                agent_name=(
                    execution.agent_name
                ),
                trace_id=execution.trace_id,
                span_id=execution.span_id,
                parent_span_id=(
                    execution.parent_span_id
                ),
                failure_type=(
                    "AgentExecutionError"
                    if error is None
                    else type(error).__name__
                ),
                message=(
                    error
                    or "Agent execution failed"
                ),
                attempt=1,
                metadata={
                    "source": (
                        "execution_manager.finalize"
                    ),
                },
            )

        # -------------------------------------------------
        # Execution metrics
        # -------------------------------------------------

        metric = self.execution_metrics.record(
            execution_id=(
                execution.execution_id
            ),
            investigation_id=(
                execution.investigation_id
            ),
            agent_name=(
                execution.agent_name
            ),
            trace_id=execution.trace_id,
            span_id=execution.span_id,
            parent_span_id=(
                execution.parent_span_id
            ),
            started_at=execution.started_at,
            status=status,
            error=error,
        )

        # -------------------------------------------------
        # Structured terminal logging
        # -------------------------------------------------

        if status == "FAILED":

            log_agent_event(
                "agent_execution_failed",
                level="ERROR",
                investigation_id=(
                    execution.investigation_id
                ),
                execution_id=(
                    execution.execution_id
                ),
                agent_name=(
                    execution.agent_name
                ),
                trace_id=execution.trace_id,
                span_id=execution.span_id,
                parent_span_id=(
                    execution.parent_span_id
                ),
                status="failed",
                duration_ms=metric.duration_ms,
                error_type=(
                    type(error).__name__
                    if error
                    else "AgentExecutionError"
                ),
                error=error,
            )

        elif status == "CANCELLED":

            log_agent_event(
                "agent_execution_cancelled",
                level="WARNING",
                investigation_id=(
                    execution.investigation_id
                ),
                execution_id=(
                    execution.execution_id
                ),
                agent_name=(
                    execution.agent_name
                ),
                trace_id=execution.trace_id,
                span_id=execution.span_id,
                parent_span_id=(
                    execution.parent_span_id
                ),
                status="cancelled",
                duration_ms=metric.duration_ms,
            )

        elif status == "COMPLETED":

            log_agent_event(
                "agent_execution_completed",
                investigation_id=(
                    execution.investigation_id
                ),
                execution_id=(
                    execution.execution_id
                ),
                agent_name=(
                    execution.agent_name
                ),
                trace_id=execution.trace_id,
                span_id=execution.span_id,
                parent_span_id=(
                    execution.parent_span_id
                ),
                status="success",
                duration_ms=metric.duration_ms,
            )

        # -------------------------------------------------
        # Investigation-level execution aggregation
        # -------------------------------------------------

        self.investigation_traces.record_execution(
            {
                "execution_id": (
                    metric.execution_id
                ),
                "investigation_id": (
                    metric.investigation_id
                ),
                "agent_name": metric.agent_name,
                "started_at": metric.started_at,
                "completed_at": metric.completed_at,
                "duration_ms": metric.duration_ms,
                "trace_id": metric.trace_id,
                "span_id": metric.span_id,
                "parent_span_id": (
                    metric.parent_span_id
                ),
                "status": metric.status,
                "error": metric.error,
            }
        )

        # -------------------------------------------------
        # Distributed state
        # -------------------------------------------------

        if execution.investigation_id is not None:

            if status == "FAILED":

                self.distributed_state.mark_failed(
                    execution.investigation_id
                )

            elif status == "COMPLETED":

                self.distributed_state.mark_completed(
                execution.investigation_id
            )

        # -------------------------------------------------
        # Release active execution
        # -------------------------------------------------

        self._release(
            execution.execution_id
        )

    # =========================================================
    # Submit
    # =========================================================

    def submit(
        self,
        investigation_id: int | None,
        agent_name: str,
        fn: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> tuple[
        AgentExecution,
        Future[Any],
    ]:
        """
        Submit an agent for asynchronous execution.

        Responsibilities:
        - register execution
        - record queue telemetry
        - execute agent inside ThreadPoolExecutor
        - maintain trace/span context
        - record execution metrics
        - record failure telemetry
        - record investigation-level trace data
        - emit structured lifecycle logs
        - release worker resources
        """

        # =====================================================
        # Register execution
        # =====================================================

        execution = self._register(
            investigation_id=investigation_id,
            agent_name=agent_name,
        )

        # =====================================================
        # Queue telemetry
        # =====================================================

        queued_at = monotonic()

        with self._condition:

            queue_depth_at_submit = self._queued

            self._queued += 1

            execution = replace(
                execution,
                queued_at=queued_at,
                queue_depth_at_submit=(
                    queue_depth_at_submit
                ),
            )

            self._active[
                execution.execution_id
            ] = execution

        self.resource_metrics.record_queued(
            queue_depth=self._queued,
        )

        # =====================================================
        # Worker wrapper
        # =====================================================

        def run_with_resource_telemetry() -> Any:

            started_at = monotonic()

            # -------------------------------------------------
            # Queue -> RUNNING
            # -------------------------------------------------

            with self._condition:

                self._queued = max(
                    0,
                    self._queued - 1,
                )

                queue_depth_at_start = self._queued

                queue_metric = (
                    self.resource_metrics.record_started(
                        execution_id=(
                            execution.execution_id
                        ),
                        investigation_id=(
                            execution.investigation_id
                        ),
                        agent_name=(
                            execution.agent_name
                        ),
                        queued_at=execution.queued_at,
                        started_at=started_at,
                        queue_depth_at_submit=(
                            execution.queue_depth_at_submit
                        ),
                        queue_depth_at_start=(
                            queue_depth_at_start
                        ),
                    )
                )

            # -------------------------------------------------
            # Investigation queue aggregation
            # -------------------------------------------------

            self.investigation_traces.record_queue_metric(
                {
                    "execution_id": (
                        queue_metric.execution_id
                    ),
                    "investigation_id": (
                        queue_metric.investigation_id
                    ),
                    "agent_name": (
                        queue_metric.agent_name
                    ),
                    "queued_at": (
                        queue_metric.queued_at
                    ),
                    "started_at": (
                        queue_metric.started_at
                    ),
                    "queue_wait_ms": (
                        queue_metric.queue_wait_ms
                    ),
                    "queue_depth_at_submit": (
                        queue_metric.queue_depth_at_submit
                    ),
                    "queue_depth_at_start": (
                        queue_metric.queue_depth_at_start
                    ),
                }
            )

            self.resource_metrics.record_worker_acquired()

            # -------------------------------------------------
            # Structured STARTED log
            # -------------------------------------------------

            log_agent_event(
                "agent_execution_started",
                    investigation_id=(
                        execution.investigation_id
                ),
                execution_id=(
                    execution.execution_id
                ),
                agent_name=(
                    execution.agent_name
                ),
                trace_id=execution.trace_id,
                span_id=execution.span_id,
                parent_span_id=(
                    execution.parent_span_id
                ),
                status="running",
            )

            try:

                result = fn(
                *args,
                **kwargs,
                )

        # IMPORTANT:
        # Finalize before returning the result so that
        # future.result() cannot observe completion before
        # investigation telemetry has been recorded.

                self._finalize_execution(
                execution,
                status="COMPLETED",
                )

                return result

            except Exception as exc:

                self._finalize_execution(
                    execution,
                    status="FAILED",
                    error=str(exc),
                    )

                raise

            finally:

                self.resource_metrics.record_worker_released()

        # =====================================================
        # Submit to executor
        # =====================================================

        try:

            future = self._executor.submit(
                run_with_resource_telemetry
            )

        except Exception as exc:

            # -------------------------------------------------
            # Executor rejected task
            # -------------------------------------------------

            with self._condition:

                self._queued = max(
                    0,
                    self._queued - 1,
                )

            self.resource_metrics.record_rejection()

            self.failure_telemetry.record_failure(
                execution_id=(
                    execution.execution_id
                ),
                investigation_id=(
                    execution.investigation_id
                ),
                agent_name=(
                    execution.agent_name
                ),
                trace_id=execution.trace_id,
                span_id=execution.span_id,
                parent_span_id=(
                    execution.parent_span_id
                ),
                failure_type=type(exc).__name__,
                message=str(exc),
                attempt=1,
                metadata={
                    "source": (
                        "execution_manager.submit"
                    ),
                },
            )

            metric = self.execution_metrics.record(
                execution_id=(
                    execution.execution_id
                ),
                investigation_id=(
                    execution.investigation_id
                ),
                agent_name=(
                    execution.agent_name
                ),
                trace_id=execution.trace_id,
                span_id=execution.span_id,
                parent_span_id=(
                    execution.parent_span_id
                ),
                started_at=execution.started_at,
                status="FAILED",
                error=str(exc),
            )

            if execution.span is not None:

                execution.span.fail(
                    str(exc)
                )

                self.investigation_traces.record_span(
                    execution.span.to_dict()
                )

            self.investigation_traces.record_execution(
                {
                    "execution_id": (
                        metric.execution_id
                    ),
                    "investigation_id": (
                        metric.investigation_id
                    ),
                    "agent_name": metric.agent_name,
                    "started_at": metric.started_at,
                    "completed_at": metric.completed_at,
                    "duration_ms": metric.duration_ms,
                    "trace_id": metric.trace_id,
                    "span_id": metric.span_id,
                    "parent_span_id": (
                        metric.parent_span_id
                    ),
                    "status": metric.status,
                    "error": metric.error,
                }
            )

            if investigation_id is not None:

                self.distributed_state.mark_failed(
                    investigation_id
                )

            self._release(
                execution.execution_id
            )

            raise

        # =====================================================
        # Completion callback
        # =====================================================

        def release_callback(
            future: Future[Any],
        ) -> None:

            # -------------------------------------------------
            # Cancellation
            # -------------------------------------------------

            if future.cancelled():

                self._finalize_execution(
                    execution,
                    status="CANCELLED",
                )

                return

            # -------------------------------------------------
            # Worker execution normally finalizes itself.
            #
            # This callback remains as a safety net for cases
            # where the Future completes without the worker
            # having finalized execution.
            # -------------------------------------------------

            if execution.execution_id in self._terminalized:

                return

            try:

                future.result()

            except Exception as exc:

                self._finalize_execution(
                    execution,
                    status="FAILED",
                    error=str(exc),
                )

            else:

                self._finalize_execution(
                    execution,
                    status="COMPLETED",
                )

        # =====================================================
        # Register callback
        # =====================================================

        future.add_done_callback(
            release_callback
        )

        return execution, future

    # =========================================================
    # Run
    # =========================================================

    def run(
        self,
        investigation_id: int,
        agent_name: str,
        fn: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """
        Execute an agent synchronously.

        Cleanup is guaranteed before run() returns or raises.
        """

        execution, future = self.submit(
            investigation_id=investigation_id,
            agent_name=agent_name,
            fn=fn,
            *args,
            **kwargs,
        )

        try:

            return future.result()

        finally:

            # The completion callback may already have released
            # the execution. _release() is intentionally
            # idempotent, so this is safe.
            self._release(
                execution.execution_id
            )

    # =========================================================
    # Queue information
    # =========================================================

    def queued_count(
        self,
    ) -> int:

        with self._lock:

            return self._queued

    def queue_available_capacity(
        self,
    ) -> int:

        with self._lock:

            return max(
                0,
                self.max_queue_size
                - self._queued,
            )

    # =========================================================
    # Active execution information
    # =========================================================

    def active_executions(
        self,
    ) -> list[AgentExecution]:

        with self._lock:

            return list(
                self._active.values()
            )

    def active_count(
        self,
    ) -> int:

        with self._lock:

            return len(
                self._active
            )

    def active_count_for_investigation(
        self,
        investigation_id: int,
    ) -> int:

        with self._lock:

            return len(
                self._active_by_investigation.get(
                    investigation_id,
                    set(),
                )
            )

    # =========================================================
    # Capacity information
    # =========================================================

    def available_capacity(
        self,
    ) -> int:

        with self._lock:

            return max(
                0,
                self.max_workers
                - len(self._active),
            )

    def available_capacity_for_investigation(
        self,
        investigation_id: int,
    ) -> int:

        with self._lock:

            active = len(
                self._active_by_investigation.get(
                    investigation_id,
                    set(),
                )
            )

            return max(
                0,
                self.max_per_investigation
                - active,
            )

    # =========================================================
    # Resource snapshot
    # =========================================================

    def resource_snapshot(
        self,
    ) -> dict[str, int]:

        with self._lock:

            active = len(
                self._active
            )

            return {
                "active": active,
                "limit": self.max_workers,
                "available": max(
                    0,
                    self.max_workers - active,
                ),
                "queued": self._queued,
                "queue_limit": self.max_queue_size,
                "queue_available": max(
                    0,
                    self.max_queue_size
                    - self._queued,
                ),
            }

    def runtime_health_snapshot(
        self,
    ) -> dict[str, Any]:
        """
        Return a production-safe snapshot of the
        agent execution runtime.

        Health is derived from execution capacity,
        queue pressure, failures, distributed
        investigation state, and shutdown state.
        """

        # -----------------------------------------------------
        # Execution / queue state
        # -----------------------------------------------------

        resources = self.resource_snapshot()

        active = resources["active"]
        limit = resources["limit"]
        queued = resources["queued"]
        queue_limit = resources["queue_limit"]

        # -----------------------------------------------------
        # Shutdown state
        # -----------------------------------------------------

        with self._lock:
            closed = self._closed

        shutdown_state = (
            "SHUTTING_DOWN"
            if closed
            else "RUNNING"
        )

        # -----------------------------------------------------
        # Distributed investigation state
        # -----------------------------------------------------

        investigations = (
            self.all_investigation_states()
        )

        running_investigations = 0
        completed_tasks = 0
        failed_tasks = 0

        for investigation in investigations:
            if investigation["active_tasks"] > 0:
                running_investigations += 1

            completed_tasks += investigation[
                "completed_tasks"
            ]

            failed_tasks += investigation[
                "failed_tasks"
            ]

        # -----------------------------------------------------
        # Failure telemetry
        # -----------------------------------------------------

        failure_snapshot = (
            self.failure_telemetry_snapshot()
        )

        failure_aggregate = (
            self.failure_telemetry_aggregate()
        )

        # -----------------------------------------------------
        # Runtime health classification
        # -----------------------------------------------------

        if closed:
            health_status = "SHUTTING_DOWN"

        elif limit > 0 and active >= limit:
            health_status = "SATURATED"

        elif queue_limit > 0 and queued >= queue_limit:
            health_status = "SATURATED"

        elif failed_tasks > 0:
            health_status = "DEGRADED"

        else:
            health_status = "HEALTHY"

        return {
            "status": health_status,
            "shutdown": {
                "state": shutdown_state,
                "closed": closed,
            },
            "execution": {
                "active": active,
                "limit": limit,
                "available": resources[
                    "available"
                ],
                "queued": queued,
                "queue_limit": queue_limit,
                "queue_available": resources[
                    "queue_available"
                ],
            },
            "investigations": {
                "tracked": len(investigations),
                "running": running_investigations,
                "completed_tasks": completed_tasks,
                "failed_tasks": failed_tasks,
            },
            "failures": {
                "aggregate": failure_aggregate,
                "recent": failure_snapshot,
            },
        }

    def queue_snapshot(
        self,
    ) -> dict[str, int]:

        with self._lock:

            return {
                "queued": self._queued,
                "limit": self.max_queue_size,
                "available": max(
                    0,
                    self.max_queue_size
                    - self._queued,
                ),
            }

    def investigation_resource_snapshot(
        self,
        investigation_id: int,
    ) -> dict[str, int]:

        with self._lock:

            active = len(
                self._active_by_investigation.get(
                    investigation_id,
                    set(),
                )
            )

            return {
                "active": active,
                "limit": self.max_per_investigation,
                "available": max(
                    0,
                    self.max_per_investigation
                    - active,
                ),
            }

    # =========================================================
    # Distributed execution state
    # =========================================================


    def observability_snapshot(
        self,
        investigation_id: int | None = None,
    ) -> dict[str, Any]:

        return self.observability_exporter.export(
            investigation_id
    )

    def investigation_execution_state(
        self,
        investigation_id: int,
    ) -> dict[str, Any]:

        return self.distributed_state.snapshot(
            investigation_id
        )

    def all_investigation_states(
        self,
    ) -> list[dict[str, Any]]:

        return self.distributed_state.all_snapshots()

    def execution_metrics_snapshot(
            self,
        ) -> dict[str, Any]:

            """
            Return a thread-safe snapshot of runtime
            agent execution metrics.
            """

            return self.execution_metrics.snapshot()

    def execution_metrics_history(
            self,
        ) -> list[dict[str, Any]]:

            """
            Return serialized runtime execution metrics.
            """

            return [
                {
                    "execution_id": metric.execution_id,
                    "investigation_id": (
                        metric.investigation_id
                    ),
                    "agent_name": metric.agent_name,
                    "started_at": metric.started_at,
                    "completed_at": metric.completed_at,
                    "duration_ms": round(
                        metric.duration_ms,
                        2,
                    ),
                    "trace_id": metric.trace_id,
                    "span_id": metric.span_id,
                    "parent_span_id": metric.parent_span_id,
                    "status": metric.status,
                    "error": metric.error,
                }
                for metric in self.execution_metrics.executions()
            ]

    def reset_execution_metrics(
            self,
        ) -> None:

            """
            Reset runtime execution metrics.
            """

            self.execution_metrics.reset()



    # =========================================================
    # Agent spans
    # =========================================================

    def execution_spans(
        self,
    ) -> list[dict[str, Any]]:
        """
        Return serialized agent execution spans.
        """

        return self.span_collector.to_dict()


    def find_execution_span(
        self,
        span_id: str,
    ) -> AgentSpan | None:
        """
        Find an execution span by span ID.
        """

        return self.span_collector.find(
            span_id
        )

    def failure_telemetry_snapshot(
        self,
    ) -> dict[str, Any]:
        """
        Return failure/retry/timeout telemetry.
        """

        return self.failure_telemetry.snapshot()


    def failure_telemetry_aggregate(
        self,
    ) -> dict[str, Any]:
        """
        Return aggregate failure/retry/timeout telemetry.
        """

        return self.failure_telemetry.aggregate()


    def reset_failure_telemetry(
        self,
    ) -> None:
        """
        Reset failure/retry/timeout telemetry.
        """

        self.failure_telemetry.reset()

    def reset_execution_spans(
        self,
    ) -> None:
        """
        Clear collected execution spans.
        """

        self.span_collector.clear()


    def resource_metrics_snapshot(
        self,
    ) -> dict[str, Any]:
        """
        Return queue and worker resource telemetry.
        """

        return self.resource_metrics.snapshot(
            max_workers=self.max_workers,
            max_queue_size=self.max_queue_size,
        )


    def resource_metrics_history(
        self,
    ) -> list[dict[str, Any]]:
        """
        Return queue telemetry history.
        """

        return self.resource_metrics.history()


    def reset_resource_metrics(
        self,
    ) -> None:
        """
        Reset queue/resource telemetry.
        """

        self.resource_metrics.reset()

        # =========================================================
    # Investigation trace aggregation
    # =========================================================

    def investigation_trace_snapshot(
    self,
    investigation_id: int,
) -> dict[str, Any]:

        return self.investigation_traces.snapshot(
            investigation_id
        )

    def investigation_trace_summary(
        self,
        investigation_id: int,
    ) -> dict[str, Any]:

        return self.investigation_traces.summary(
            investigation_id
        )

    def investigation_timeline(
        self,
        investigation_id: int,
    ) -> list[dict[str, Any]]:

        return self.investigation_traces.timeline(
            investigation_id
        )

    def investigation_critical_path(
        self,
        investigation_id: int,
    ) -> dict[str, Any]:

        return self.investigation_traces.critical_path(
            investigation_id
        )

    def reset_investigation_trace(
        self,
        investigation_id: int | None = None,
    ) -> None:

        self.investigation_traces.reset(
            investigation_id
        )

    # =========================================================
    # Shutdown
    # =========================================================

    def shutdown(
        self,
        *,
        wait: bool = True,
        cancel_futures: bool = True,
    ) -> None:

        with self._condition:

            if self._closed:
                return

            self._closed = True

            self._condition.notify_all()

        self._executor.shutdown(
            wait=wait,
            cancel_futures=cancel_futures,
        )

    # =========================================================
    # Context manager
    # =========================================================

    def __enter__(
        self,
    ) -> "AgentExecutionManager":

        return self

    def __exit__(
        self,
        exc_type: Any,
        exc_value: Any,
        traceback: Any,
    ) -> None:

        self.shutdown()
