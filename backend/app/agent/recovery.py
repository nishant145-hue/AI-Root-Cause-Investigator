from __future__ import annotations

from concurrent.futures import (
    ThreadPoolExecutor,
)
from concurrent.futures import (
    TimeoutError as FutureTimeoutError,
)
from typing import Any, Callable

from app.agent.agent_isolation import (
    refresh_agent_isolation,
)
from app.agent.circuit_breaker_runtime import (
    allow_agent_execution,
    record_agent_failure,
    record_agent_success,
)
from app.agent.failure_telemetry import (
    FailureTelemetryCollector,
)
from app.agent.structured_logging import (
    agent_log_context,
    log_agent_event,
)
from app.agent.timeout import AgentTimeoutError
from app.agent.timeout_policy import AgentTimeoutPolicy


def run_with_failure_capture(
    state: dict[str, Any],
    agent_name: str,
    node: Callable[..., dict[str, Any]],
    timeout_seconds: float | None = None,
    telemetry: FailureTelemetryCollector | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """
    Execute an agent node with:

    - Circuit-breaker protection
    - Failure capture
    - Timeout protection
    - Cancellation metadata
    - Successful execution tracking

    Execution flow:

        Circuit Breaker
              |
              +---- BLOCKED --> CIRCUIT_OPEN
              |
              +---- ALLOWED
                       |
                       v
                Execute Agent
                   /       \
             success      failure
                |            |
                v            v
       record_success  record_failure

    Unexpected exceptions are converted into LangGraph
    failure state.

    A synchronous agent is executed in a worker thread so
    the caller can enforce an execution deadline.

    Important:
        A running Python thread cannot be forcibly killed.
        Timeout cancellation therefore prevents pending work
        where possible, but does not terminate an already
        running synchronous function.
    """

    # ---------------------------------------------------------
    # Circuit Breaker
    # ---------------------------------------------------------

    if not allow_agent_execution(
        state,
        agent_name,
    ):
        message = (
            f"Agent '{agent_name}' is blocked "
            "by the circuit breaker."
        )

        return {
            "last_failed_agent": agent_name,
            "last_failure_type": "CIRCUIT_OPEN",
            "last_failure_message": message,
            "investigation_status": "FAILED",
            "failure_metadata": {
                "agent": agent_name,
                "failure_type": "CIRCUIT_OPEN",
                "message": message,
            },
            "cancellation_requested": False,
            "cancellation_reason": None,
            "cancelled_agent": None,
            "cancellation_metadata": {
                "cancelled": False,
                "agent": agent_name,
                "reason": None,
            },
        }

    # ---------------------------------------------------------
    # Timeout policy
    # ---------------------------------------------------------

    policy = AgentTimeoutPolicy.from_settings()

    timeout = (
        timeout_seconds
        if timeout_seconds is not None
        else policy.timeout_for("agent")
    )

    # ---------------------------------------------------------
    # Worker executor
    # ---------------------------------------------------------

    executor = ThreadPoolExecutor(
        max_workers=1,
        thread_name_prefix=f"agent-{agent_name}",
    )

    future = executor.submit(
        node,
        state,
        **kwargs,
    )

    # ---------------------------------------------------------
    # Execute agent
    # ---------------------------------------------------------

    try:
        result = future.result(
            timeout=timeout,
        )

        # -----------------------------------------------------
        # Validate state update
        # -----------------------------------------------------

        if not isinstance(result, dict):
            raise RuntimeError(
                f"{agent_name} returned "
                f"an invalid state update."
            )

        # -----------------------------------------------------
        # Record successful execution
        # -----------------------------------------------------

        record_agent_success(
            state,
            agent_name,
        )

        # -----------------------------------------------------
        # Normal shutdown
        # -----------------------------------------------------

        executor.shutdown(
            wait=True,
            cancel_futures=True,
        )

        return result

    # ---------------------------------------------------------
    # Execution deadline exceeded
    # ---------------------------------------------------------

    except FutureTimeoutError:

    # ---------------------------------------------------------
    # Race-condition protection
    # ---------------------------------------------------------

        if future.done():

            try:
                future.result()

            except Exception as exc:

                record_agent_failure(
                    state,
                    agent_name,
                )

                refresh_agent_isolation(
                    state,
                    agent_name,
                    )

                executor.shutdown(
                    wait=False,
                    cancel_futures=True,
                )

                failure_type = (
                    "TRANSIENT"
                    if isinstance(
                        exc,
                        (
                            TimeoutError,
                            ConnectionError,
                        ),
                    )
                    else "CRITICAL"
                    )

                if telemetry is not None:
                    telemetry.record_failure(
                        agent_name=agent_name,
                        failure_type=failure_type,
                        message=str(exc),
                        attempt=(
                            int(
                                state.get(
                                    "retry_counts",
                                    {},
                                ).get(
                                    agent_name,
                                    0,
                                )
                            )
                            + 1
                        ),
                        investigation_id=state.get(
                            "investigation_id"
                        ),
                        metadata={
                            "source": "recovery",
                            "future_timeout_race": True,
                        },
                    )

                return {
                "last_failed_agent": agent_name,
                "last_failure_type": failure_type,
                "last_failure_message": str(exc),
                "investigation_status": "FAILED",
                "failure_metadata": {
                    "agent": agent_name,
                    "failure_type": (
                        "TIMEOUT"
                        if isinstance(
                            exc,
                            TimeoutError,
                        )
                        else "ERROR"
                    ),
                    "message": str(exc),
                },
                "cancellation_requested": False,
                "cancellation_reason": None,
                "cancelled_agent": None,
                "cancellation_metadata": {
                    "cancelled": False,
                    "agent": agent_name,
                    "reason": None,
                },
            }

    # ---------------------------------------------------------
    # Actual execution timeout
    # ---------------------------------------------------------

        future.cancel()

        record_agent_failure(
            state,
            agent_name,
        )

        refresh_agent_isolation(
            state,
            agent_name,
        )

        timeout_error = AgentTimeoutError(
            agent_name=agent_name,
            timeout_seconds=timeout,
        )

        if telemetry is not None:
            telemetry.record_timeout(
                agent_name=agent_name,
                timeout_seconds=timeout,
                attempt=(
                    int(
                        state.get(
                            "retry_counts",
                            {},
                        ).get(
                            agent_name,
                            0,
                        )
                    )
                    + 1
                ),
                message=str(timeout_error),
                investigation_id=state.get(
                    "investigation_id"
                ),
                metadata={
                    "source": "recovery",
                    "failure_type": "TIMEOUT",
                },
            )

        executor.shutdown(
            wait=False,
            cancel_futures=True,
        )

        return {
            "last_failed_agent": agent_name,
            "last_failure_type": "TRANSIENT",
            "last_failure_message": str(
                timeout_error
            ),
            "investigation_status": "FAILED",
            "failure_metadata": {
                "agent": agent_name,
                "failure_type": "TIMEOUT",
                "message": str(timeout_error),
                "timeout_seconds": timeout,
            },
            "cancellation_requested": True,
            "cancellation_reason": "AGENT_TIMEOUT",
            "cancelled_agent": agent_name,
            "cancellation_metadata": {
                "cancelled": True,
                "agent": agent_name,
                "reason": "AGENT_TIMEOUT",
                "timeout_seconds": timeout,
            },
        }

        # -----------------------------------------------------
        # Actual execution timeout
        # -----------------------------------------------------

        future.cancel()

        # Record timeout as an agent failure.
        record_agent_failure(
            state,
            agent_name,
        )
        refresh_agent_isolation(
            state,
            agent_name,
        )

        executor.shutdown(
            wait=False,
            cancel_futures=True,
        )

        timeout_error = AgentTimeoutError(
            agent_name=agent_name,
            timeout_seconds=timeout,
        )

        return {
            "last_failed_agent": agent_name,
            "last_failure_type": "TRANSIENT",
            "last_failure_message": str(
                timeout_error
            ),
            "investigation_status": "FAILED",
            "failure_metadata": {
                "agent": agent_name,
                "failure_type": "TIMEOUT",
                "message": str(timeout_error),
                "timeout_seconds": timeout,
            },
            "cancellation_requested": True,
            "cancellation_reason": "AGENT_TIMEOUT",
            "cancelled_agent": agent_name,
            "cancellation_metadata": {
                "cancelled": True,
                "agent": agent_name,
                "reason": "AGENT_TIMEOUT",
                "timeout_seconds": timeout,
            },
        }

    # ---------------------------------------------------------
    # Unexpected / normal agent exception
    # ---------------------------------------------------------

    except Exception as exc:

        # Record the failure in the circuit breaker.
        record_agent_failure(
            state,
            agent_name,
        )
        refresh_agent_isolation(
            state,
            agent_name,
        )

        executor.shutdown(
            wait=False,
            cancel_futures=True,
        )

        failure_type = (
            "TRANSIENT"
            if isinstance(
                exc,
                (
                    TimeoutError,
                    ConnectionError,
                ),
            )
            else "CRITICAL"
        )

        if telemetry is not None:

            telemetry.record_failure(
            agent_name=agent_name,
            failure_type=failure_type,
            message=str(exc),
            attempt=(
                int(
                    state.get(
                        "retry_counts",
                        {},
                    ).get(
                        agent_name,
                        0,
                    )
                )
                + 1
            ),
            investigation_id=state.get(
                "investigation_id"
            ),
            metadata={
                "source": "recovery",
            },
        )

        # ---------------------------------------------------------
# Structured timeout event
# ---------------------------------------------------------

        log_agent_event(
            "agent_execution_timeout",
            level="WARNING",
        agent_name=agent_name,
        investigation_id=state.get(
            "investigation_id"
        ),
        timeout_seconds=timeout,
        execution_id=state.get(
            "execution_id"
        ),
        trace_id=state.get(
            "trace_id"
        ),
        )

        return {
            "last_failed_agent": agent_name,
            "last_failure_type": failure_type,
            "last_failure_message": str(exc),
            "investigation_status": "FAILED",
            "failure_metadata": {
                "agent": agent_name,
                "failure_type": (
                    "TIMEOUT"
                    if isinstance(
                        exc,
                        TimeoutError,
                    )
                    else "ERROR"
                ),
                "message": str(exc),
            },
            "cancellation_requested": False,
            "cancellation_reason": None,
            "cancelled_agent": None,
            "cancellation_metadata": {
                "cancelled": False,
                "agent": agent_name,
                "reason": None,
            },
        }
