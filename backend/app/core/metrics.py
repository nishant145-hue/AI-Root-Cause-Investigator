import threading
import time
from collections import defaultdict
from typing import Any


class MetricsCollector:
    """Lightweight in-process application metrics collector."""

    def __init__(self) -> None:
        self._lock = threading.Lock()

        self._request_count = 0
        self._request_errors = 0

        self._status_codes: dict[int, int] = defaultdict(int)
        self._methods: dict[str, int] = defaultdict(int)
        self._paths: dict[str, int] = defaultdict(int)

        self._total_duration_ms = 0.0
        self._max_duration_ms = 0.0

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

    def snapshot(self) -> dict[str, Any]:
        """Return a thread-safe snapshot of current metrics."""

        with self._lock:
            average_duration_ms = (
                self._total_duration_ms / self._request_count
                if self._request_count
                else 0.0
            )

            return {
                "requests": {
                    "total": self._request_count,
                    "errors_5xx": self._request_errors,
                },
                "status_codes": dict(self._status_codes),
                "methods": dict(self._methods),
                "paths": dict(self._paths),
                "duration_ms": {
                    "average": round(average_duration_ms, 2),
                    "maximum": round(self._max_duration_ms, 2),
                },
            }

    def reset(self) -> None:
        """Reset all collected metrics."""

        with self._lock:
            self._request_count = 0
            self._request_errors = 0

            self._status_codes.clear()
            self._methods.clear()
            self._paths.clear()

            self._total_duration_ms = 0.0
            self._max_duration_ms = 0.0


metrics = MetricsCollector()