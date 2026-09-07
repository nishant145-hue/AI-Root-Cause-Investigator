import threading
from collections import defaultdict
from typing import Any


class MetricsCollector:
    """Thread-safe application and analytics metrics collector."""

    def __init__(self) -> None:
        self._lock = threading.Lock()

        # ---------------------------------------------------------
        # HTTP request metrics
        # ---------------------------------------------------------

        self._request_count = 0
        self._request_errors = 0

        self._status_codes: dict[int, int] = defaultdict(int)
        self._methods: dict[str, int] = defaultdict(int)
        self._paths: dict[str, int] = defaultdict(int)

        self._total_duration_ms = 0.0
        self._max_duration_ms = 0.0

        # ---------------------------------------------------------
        # Analytics metrics
        # ---------------------------------------------------------

        self._analytics_dashboard_requests = 0
        self._analytics_dashboard_successes = 0
        self._analytics_dashboard_failures = 0

        self._analytics_dashboard_duration_ms = 0.0
        self._analytics_dashboard_max_duration_ms = 0.0

        self._analytics_validation_requests = 0
        self._analytics_validation_successes = 0
        self._analytics_validation_normalized = 0
        self._analytics_validation_failures = 0

        self._analytics_export_requests: dict[str, int] = (
            defaultdict(int)
        )

        self._analytics_export_successes: dict[str, int] = (
            defaultdict(int)
        )

        self._analytics_export_failures: dict[str, int] = (
            defaultdict(int)
        )

        self._analytics_export_duration_ms: dict[str, float] = (
            defaultdict(float)
        )

        self._analytics_export_max_duration_ms: dict[str, float] = (
            defaultdict(float)
        )

    # =========================================================
    # HTTP metrics
    # =========================================================

    def record_request(
        self,
        *,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
    ) -> None:
        """Record one completed HTTP request."""

        with self._lock:
            self._request_count += 1

            if status_code >= 500:
                self._request_errors += 1

            self._status_codes[status_code] += 1
            self._methods[method] += 1
            self._paths[path] += 1

            self._total_duration_ms += duration_ms
            self._max_duration_ms = max(
                self._max_duration_ms,
                duration_ms,
            )

    # =========================================================
    # Analytics dashboard metrics
    # =========================================================

    def record_analytics_dashboard_request(
        self,
        *,
        success: bool,
        duration_ms: float,
    ) -> None:
        """
        Record one analytics dashboard operation.

        Investigation IDs are intentionally not stored here to
        avoid high-cardinality metrics.
        """

        with self._lock:
            self._analytics_dashboard_requests += 1

            if success:
                self._analytics_dashboard_successes += 1
            else:
                self._analytics_dashboard_failures += 1

            self._analytics_dashboard_duration_ms += duration_ms

            self._analytics_dashboard_max_duration_ms = max(
                self._analytics_dashboard_max_duration_ms,
                duration_ms,
            )

    # =========================================================
    # Analytics validation metrics
    # =========================================================

    def record_analytics_validation(
        self,
        *,
        status: str,
    ) -> None:
        """
        Record an analytics validation operation.

        Supported statuses:
            success
            normalized
            failure
        """

        normalized_status = status.lower().strip()

        with self._lock:
            self._analytics_validation_requests += 1

            if normalized_status == "success":
                self._analytics_validation_successes += 1

            elif normalized_status == "normalized":
                self._analytics_validation_normalized += 1

            elif normalized_status == "failure":
                self._analytics_validation_failures += 1

            else:
                self._analytics_validation_failures += 1

    # =========================================================
    # Analytics export metrics
    # =========================================================

    def record_analytics_export(
        self,
        *,
        export_format: str,
        success: bool,
        duration_ms: float,
    ) -> None:
        """
        Record an analytics/report export.

        export_format should be a low-cardinality value such as:
            csv
            excel
            pdf
            json
        """

        export_format = export_format.lower().strip()

        with self._lock:
            self._analytics_export_requests[
                export_format
            ] += 1

            self._analytics_export_duration_ms[
                export_format
            ] += duration_ms

            self._analytics_export_max_duration_ms[
                export_format
            ] = max(
                self._analytics_export_max_duration_ms[
                    export_format
                ],
                duration_ms,
            )

            if success:
                self._analytics_export_successes[
                    export_format
                ] += 1
            else:
                self._analytics_export_failures[
                    export_format
                ] += 1

    # =========================================================
    # Snapshot
    # =========================================================

    def snapshot(self) -> dict[str, Any]:
        """Return a thread-safe snapshot of all metrics."""

        with self._lock:
            average_duration_ms = (
                self._total_duration_ms
                / self._request_count
                if self._request_count
                else 0.0
            )

            dashboard_average_duration_ms = (
                self._analytics_dashboard_duration_ms
                / self._analytics_dashboard_requests
                if self._analytics_dashboard_requests
                else 0.0
            )

            export_metrics: dict[str, Any] = {}

            formats = set(
                self._analytics_export_requests
            ) | set(
                self._analytics_export_duration_ms
            )

            for export_format in formats:
                requests = (
                    self._analytics_export_requests[
                        export_format
                    ]
                )

                export_metrics[export_format] = {
                    "requests": requests,
                    "successes": (
                        self._analytics_export_successes[
                            export_format
                        ]
                    ),
                    "failures": (
                        self._analytics_export_failures[
                            export_format
                        ]
                    ),
                    "duration_ms": {
                        "average": round(
                            (
                                self._analytics_export_duration_ms[
                                    export_format
                                ]
                                / requests
                                if requests
                                else 0.0
                            ),
                            2,
                        ),
                        "maximum": round(
                            self._analytics_export_max_duration_ms[
                                export_format
                            ],
                            2,
                        ),
                    },
                }

            return {
                # -------------------------------------------------
                # Existing HTTP metrics
                # -------------------------------------------------

                "requests": {
                    "total": self._request_count,
                    "errors_5xx": self._request_errors,
                },
                "status_codes": dict(
                    self._status_codes
                ),
                "methods": dict(
                    self._methods
                ),
                "paths": dict(
                    self._paths
                ),
                "duration_ms": {
                    "average": round(
                        average_duration_ms,
                        2,
                    ),
                    "maximum": round(
                        self._max_duration_ms,
                        2,
                    ),
                },

                # -------------------------------------------------
                # Analytics metrics
                # -------------------------------------------------

                "analytics": {
                    "dashboard": {
                        "requests": (
                            self._analytics_dashboard_requests
                        ),
                        "successes": (
                            self._analytics_dashboard_successes
                        ),
                        "failures": (
                            self._analytics_dashboard_failures
                        ),
                        "duration_ms": {
                            "average": round(
                                dashboard_average_duration_ms,
                                2,
                            ),
                            "maximum": round(
                                self._analytics_dashboard_max_duration_ms,
                                2,
                            ),
                        },
                    },

                    "validation": {
                        "requests": (
                            self._analytics_validation_requests
                        ),
                        "successes": (
                            self._analytics_validation_successes
                        ),
                        "normalized": (
                            self._analytics_validation_normalized
                        ),
                        "failures": (
                            self._analytics_validation_failures
                        ),
                    },

                    "exports": export_metrics,
                },
            }

    # =========================================================
    # Reset
    # =========================================================

    def reset(self) -> None:
        """Reset all collected metrics."""

        with self._lock:
            # HTTP
            self._request_count = 0
            self._request_errors = 0

            self._status_codes.clear()
            self._methods.clear()
            self._paths.clear()

            self._total_duration_ms = 0.0
            self._max_duration_ms = 0.0

            # Dashboard
            self._analytics_dashboard_requests = 0
            self._analytics_dashboard_successes = 0
            self._analytics_dashboard_failures = 0

            self._analytics_dashboard_duration_ms = 0.0
            self._analytics_dashboard_max_duration_ms = 0.0

            # Validation
            self._analytics_validation_requests = 0
            self._analytics_validation_successes = 0
            self._analytics_validation_normalized = 0
            self._analytics_validation_failures = 0

            # Exports
            self._analytics_export_requests.clear()
            self._analytics_export_successes.clear()
            self._analytics_export_failures.clear()
            self._analytics_export_duration_ms.clear()
            self._analytics_export_max_duration_ms.clear()


metrics = MetricsCollector()
