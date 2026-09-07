from __future__ import annotations

from typing import Any


class ObservabilityExporter:
    """
    Builds a production-safe observability snapshot
    from the agent telemetry collectors.
    """

    def __init__(
        self,
        *,
        investigation_traces,
        execution_metrics,
        resource_metrics,
        failure_telemetry,
        max_workers: int,
        max_queue_size: int,
    ) -> None:

        self.investigation_traces = (
            investigation_traces
        )

        self.execution_metrics = (
            execution_metrics
        )

        self.resource_metrics = (
            resource_metrics
        )

        self.failure_telemetry = (
            failure_telemetry
        )

        self.max_workers = max_workers
        self.max_queue_size = max_queue_size

    # =========================================================
    # Investigation
    # =========================================================

    def investigation_snapshot(
        self,
        investigation_id: int,
    ) -> dict[str, Any]:

        return {
            "investigation_id": investigation_id,
            "trace": (
                self.investigation_traces.snapshot(
                    investigation_id
                )
            ),
            "summary": (
                self.investigation_traces.summary(
                    investigation_id
                )
            ),
            "timeline": (
                self.investigation_traces.timeline(
                    investigation_id
                )
            ),
            "critical_path": (
                self.investigation_traces.critical_path(
                    investigation_id
                )
            ),
        }

    # =========================================================
    # Runtime metrics
    # =========================================================

    def execution_snapshot(
        self,
    ) -> dict[str, Any]:

        return self.execution_metrics.snapshot()

    def resource_snapshot(
        self,
    ) -> dict[str, Any]:

        return self.resource_metrics.snapshot(
            max_workers=self.max_workers,
            max_queue_size=self.max_queue_size,
        )

    def failure_snapshot(
        self,
    ) -> dict[str, Any]:

        return self.failure_telemetry.snapshot()

    # =========================================================
    # Unified export
    # =========================================================

    def export(
        self,
        investigation_id: int | None = None,
    ) -> dict[str, Any]:

        payload: dict[str, Any] = {
            "version": "1.0",
            "execution": (
                self.execution_snapshot()
            ),
            "resource": (
                self.resource_snapshot()
            ),
            "failures": (
                self.failure_snapshot()
            ),
        }

        if investigation_id is not None:

            payload["investigation"] = (
                self.investigation_snapshot(
                    investigation_id
                )
            )

        return payload
