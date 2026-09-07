from typing import Any

from app.core.metrics import metrics
from app.schemas.analytics import (
    AgentPerformanceRead,
    AnalyticsOverview,
    BottleneckRead,
    ExecutionTimelineEntryRead,
    FailureRetryMetricsRead,
    InvestigationAnalyticsDashboardRead,
)


class AnalyticsValidationService:
    """
    Validates, normalizes, and builds production-safe analytics
    representations.

    The service accepts malformed or partially persisted analytics
    without allowing them to break the dashboard API.
    """

    # ============================================================
    # Generic safe helpers
    # ============================================================

    @staticmethod
    def _safe_dict(value: Any) -> dict[str, Any]:
        if isinstance(value, dict):
            return value

        return {}

    @staticmethod
    def _safe_list(value: Any) -> list[Any]:
        if isinstance(value, list):
            return value

        if isinstance(value, tuple):
            return list(value)

        return []

    @staticmethod
    def _safe_int(
        value: Any,
        default: int = 0,
    ) -> int:
        try:
            return int(value)
        except (
            TypeError,
            ValueError,
        ):
            return default

    @staticmethod
    def _safe_float(
        value: Any,
        default: float = 0.0,
    ) -> float:
        try:
            return float(value)
        except (
            TypeError,
            ValueError,
        ):
            return default

    @staticmethod
    def _safe_str(
        value: Any,
        default: str | None = None,
    ) -> str | None:
        if value is None:
            return default

        try:
            return str(value)
        except Exception:
            return default

    # ============================================================
    # Overview normalization
    # ============================================================

    @classmethod
    def normalize_overview(
        cls,
        value: Any,
    ) -> AnalyticsOverview:
        data = cls._safe_dict(value)

        total_executions = max(
            0,
            cls._safe_int(
                data.get(
                    "total_executions",
                    data.get(
                        "executions",
                        0,
                    ),
                )
            ),
        )

        successful_executions = max(
            0,
            cls._safe_int(
            data.get(
                "successful_executions",
                data.get(
                    "success_count",
                    data.get(
                        "successes",
                        0,
                        ),
                    ),
                )
            ),
        )

        failed_executions = max(
            0,
            cls._safe_int(
                data.get(
                    "failed_executions",
                data.get(
                    "failure_count",
                data.get(
                    "failures",
                    0,
                    ),
                ),
            )
        ),
    )

        total_duration_ms = max(
            0.0,
            cls._safe_float(
                data.get(
                    "total_duration_ms",
                    0.0,
                )
            ),
        )

        retry_count = max(
            0,
            cls._safe_int(
                data.get(
                    "retry_count",
                    data.get(
                        "retries",
                        0,
                    ),
                )
            ),
        )

        efficiency_score = cls._safe_float(
            data.get(
                "efficiency_score",
                0.0,
            )
        )

        efficiency_score = max(
            0.0,
            min(
                100.0,
                efficiency_score,
            ),
        )

        return AnalyticsOverview(
            total_executions=total_executions,
            successful_executions=successful_executions,
            failed_executions=failed_executions,
            total_duration_ms=total_duration_ms,
            retry_count=retry_count,
            efficiency_score=efficiency_score,
        )

    # ============================================================
    # Agent performance normalization
    # ============================================================

    @classmethod
    def normalize_agent_performance(
        cls,
        value: Any,
    ) -> list[AgentPerformanceRead]:
        raw_items = cls._safe_list(value)

        result: list[
            AgentPerformanceRead
        ] = []

        for item in raw_items:
            data = cls._safe_dict(item)

            agent = cls._safe_str(
                data.get("agent"),
                "unknown",
            )

            executions = max(
                0,
                cls._safe_int(
                    data.get(
                        "executions",
                        data.get(
                            "execution_count",
                            0,
                        ),
                    )
                ),
            )

            successful_executions = max(
                0,
                cls._safe_int(
                    data.get(
                        "successful_executions",
                        data.get(
                            "success_count",
                            data.get(
                                "successes",
                                0,
                            ),
                        ),
                    )
                ),
            )

            failed_executions = max(
                0,
                cls._safe_int(
                    data.get(
                        "failed_executions",
                        data.get(
                            "failure_count",
                            data.get(
                                "failures",
                                0,
                            ),
                        ),
                    )
                ),
            )

            total_duration_ms = max(
                0.0,
                cls._safe_float(
                    data.get(
                        "total_duration_ms",
                        0.0,
                    )
                ),
            )

            average_duration_ms = max(
                0.0,
                cls._safe_float(
                    data.get(
                        "average_duration_ms",
                        (
                            total_duration_ms
                            / executions
                            if executions
                            else 0.0
                        ),
                    )
                ),
            )

            failure_rate = cls._safe_float(
                data.get(
                    "failure_rate",
                    (
                        failed_executions
                        / executions
                        * 100.0
                        if executions
                        else 0.0
                    ),
                )
            )

            failure_rate = max(
                0.0,
                min(
                    100.0,
                    failure_rate,
                ),
            )

            result.append(
                AgentPerformanceRead(
                    agent=agent or "unknown",
                    executions=executions,
                    successful_executions=(
                        successful_executions
                    ),
                    failed_executions=(
                        failed_executions
                    ),
                    total_duration_ms=(
                        total_duration_ms
                    ),
                    average_duration_ms=(
                        average_duration_ms
                    ),
                    failure_rate=failure_rate,
                )
            )

        return result

    # ============================================================
    # Bottleneck normalization
    # ============================================================

    @classmethod
    def normalize_bottlenecks(
        cls,
        value: Any,
    ) -> list[BottleneckRead]:
        raw_items = cls._safe_list(value)

        result: list[
            BottleneckRead
        ] = []

        for item in raw_items:
            if isinstance(item, str):
                result.append(
                    BottleneckRead(
                        agent=item,
                        is_bottleneck=True,
                    )
                )
                continue

            data = cls._safe_dict(item)

            agent = cls._safe_str(
                data.get(
                    "agent",
                    "unknown",
                ),
                "unknown",
            )

            average_duration_ms = max(
                0.0,
                cls._safe_float(
                    data.get(
                        "average_duration_ms",
                        0.0,
                    )
                ),
            )

            execution_count = max(
                0,
                cls._safe_int(
                    data.get(
                        "execution_count",
                        data.get(
                            "executions",
                            0,
                        ),
                    )
                ),
            )

            threshold_ms = max(
                0.0,
                cls._safe_float(
                    data.get(
                        "threshold_ms",
                        0.0,
                    )
                ),
            )

            is_bottleneck = bool(
                data.get(
                    "is_bottleneck",
                    (
                        average_duration_ms
                        > threshold_ms
                        if threshold_ms > 0
                        else False
                    ),
                )
            )

            result.append(
                BottleneckRead(
                    agent=agent or "unknown",
                    average_duration_ms=(
                        average_duration_ms
                    ),
                    execution_count=(
                        execution_count
                    ),
                    threshold_ms=threshold_ms,
                    is_bottleneck=is_bottleneck,
                )
            )

        return result

    # ============================================================
    # Failure/retry normalization
    # ============================================================

    @classmethod
    def normalize_failure_retry_metrics(
        cls,
        value: Any,
    ) -> FailureRetryMetricsRead:
        data = cls._safe_dict(value)

        failed_agents_raw = data.get(
            "failed_agents",
            data.get(
                "failures_by_agent",
                {},
            ),
        )

        retry_by_agent_raw = data.get(
            "retry_by_agent",
            data.get(
                "retries_by_agent",
                {},
            ),
        )

        failed_agents: dict[
            str,
            int,
        ] = {}

        if isinstance(
            failed_agents_raw,
            dict,
        ):
            for agent, count in (
                failed_agents_raw.items()
            ):
                failed_agents[
                    str(agent)
                ] = max(
                    0,
                    cls._safe_int(count),
                )

        retry_by_agent: dict[
            str,
            int,
        ] = {}

        if isinstance(
            retry_by_agent_raw,
            dict,
        ):
            for agent, count in (
                retry_by_agent_raw.items()
            ):
                retry_by_agent[
                    str(agent)
                ] = max(
                    0,
                    cls._safe_int(count),
                )

        total_failures = max(
            0,
            cls._safe_int(
                data.get(
                    "total_failures",
                    sum(
                        failed_agents.values()
                    ),
                )
            ),
        )

        total_retries = max(
            0,
            cls._safe_int(
                data.get(
                    "total_retries",
                    data.get(
                        "retry_count",
                        sum(
                            retry_by_agent.values()
                        ),
                    ),
                )
            ),
        )

        return FailureRetryMetricsRead(
            total_failures=total_failures,
            total_retries=total_retries,
            failed_agents=failed_agents,
            retry_by_agent=retry_by_agent,
        )

    # ============================================================
    # Timeline normalization
    # ============================================================

    @classmethod
    def normalize_timeline(
        cls,
        value: Any,
    ) -> list[ExecutionTimelineEntryRead]:
        raw_items = cls._safe_list(value)

        result: list[
            ExecutionTimelineEntryRead
        ] = []

        for item in raw_items:

            # Ignore completely invalid timeline entries.
            if not isinstance(item, dict):
                continue

            data = item

            # Preserve metadata.
            metadata = cls._safe_dict(
                data.get(
                    "metadata",
                    {},
                )
            ).copy()

            # Preserve retry-related fields that may exist
            # at the top level of the timeline entry.
            if "attempt" in data:
                metadata["attempt"] = data[
                    "attempt"
                ]

            if "attempt_number" in data:
                metadata[
                    "attempt_number"
                ] = data[
                    "attempt_number"
                ]

            if "retry_count" in data:
                metadata[
                    "retry_count"
                ] = data[
                    "retry_count"
                ]

            if "retries" in data:
                metadata["retries"] = data[
                    "retries"
                ]

            # ------------------------------------------------
            # Duration normalization
            #
            # Valid numeric value:
            #     "50" -> 50.0
            #
            # Invalid value:
            #     "invalid" -> None
            #
            # This is important because malformed duration
            # values should not become 0.0 silently.
            # ------------------------------------------------

            duration_ms = None

            if data.get("duration_ms") is not None:
                try:
                    duration_ms = float(
                        data["duration_ms"]
                    )
                except (
                    TypeError,
                    ValueError,
                ):
                    duration_ms = None

            result.append(
                ExecutionTimelineEntryRead(
                    agent=cls._safe_str(
                        data.get("agent")
                    ),
                    action=cls._safe_str(
                        data.get("action")
                    ),
                    status=cls._safe_str(
                        data.get("status")
                    ),
                    started_at=cls._safe_str(
                        data.get("started_at")
                    ),
                    completed_at=cls._safe_str(
                        data.get("completed_at")
                    ),
                    duration_ms=duration_ms,
                    metadata=metadata,
                )
            )

        return result

    # ============================================================
    # Retry calculation
    # ============================================================

    @classmethod
    def calculate_retry_count(
        cls,
        timeline: list[
            ExecutionTimelineEntryRead
        ],
    ) -> int:
        """
        Calculate total retries from timeline entries.

        Priority:

        1. retry_count
        2. retries
        3. attempt
        4. attempt_number

        Examples:

            attempt=1 -> 0 retries
            attempt=2 -> 1 retry
            attempt=3 -> 2 retries
        """

        retry_count = 0

        for entry in timeline:
            metadata = (
                entry.metadata
                or {}
            )

            retries = 0

            # Explicit retry_count.
            if "retry_count" in metadata:
                retries = max(
                    0,
                    cls._safe_int(
                        metadata.get(
                            "retry_count"
                        )
                    ),
                )

            # Explicit retries.
            elif "retries" in metadata:
                retries = max(
                    0,
                    cls._safe_int(
                        metadata.get(
                            "retries"
                        )
                    ),
                )

            # Attempt number.
            elif "attempt" in metadata:
                attempt = max(
                    1,
                    cls._safe_int(
                        metadata.get(
                            "attempt"
                        ),
                        1,
                    ),
                )

                retries = max(
                    0,
                    attempt - 1,
                )

            # Alternate attempt field.
            elif (
                "attempt_number"
                in metadata
            ):
                attempt = max(
                    1,
                    cls._safe_int(
                        metadata.get(
                            "attempt_number"
                        ),
                        1,
                    ),
                )

                retries = max(
                    0,
                    attempt - 1,
                )

            retry_count += retries

        return max(
            0,
            retry_count,
        )

    # ============================================================
    # Dashboard
    # ============================================================

    @classmethod
    def build_dashboard(
        cls,
        investigation_id: int,
        analytics: Any,
    ) -> InvestigationAnalyticsDashboardRead:
        """
        Build a production-safe dashboard.

        Supports both persisted analytics and timeline-only
        analytics.
        """

        original_was_dict = isinstance(
            analytics,
            dict,
        )

        try:
            analytics = cls._safe_dict(
                analytics
            )

            # ----------------------------------------------------
            # Timeline
            # ----------------------------------------------------

            timeline_data = (
                cls.normalize_timeline(
                    analytics.get(
                        "timeline",
                        [],
                    )
                )
            )

            # ----------------------------------------------------
            # Overview
            # ----------------------------------------------------

            persisted_overview = (
                cls._safe_dict(
                    analytics.get(
                        "overview"
                    )
                )
            )

            if persisted_overview:
                overview = (
                    cls.normalize_overview(
                        persisted_overview
                    )
                )

            else:
                total_executions = len(
                    timeline_data
                )

                successful_executions = sum(
                    1
                    for entry in timeline_data
                    if str(
                        entry.status or ""
                    ).upper()
                    in {
                        "COMPLETED",
                        "SUCCESS",
                        "SUCCEEDED",
                    }
                )

                failed_executions = sum(
                    1
                    for entry in timeline_data
                    if str(
                        entry.status or ""
                    ).upper()
                    in {
                        "FAILED",
                        "FAILURE",
                        "ERROR",
                    }
                )

                total_duration_ms = sum(
                    float(
                        entry.duration_ms
                        or 0.0
                    )
                    for entry in timeline_data
                )

                retry_count = (
                    cls.calculate_retry_count(
                        timeline_data
                    )
                )

                efficiency_score = 0.0

                if total_executions:
                    efficiency_score = (
                        successful_executions
                        / total_executions
                    ) * 100.0

                overview = AnalyticsOverview(
                    total_executions=(
                        total_executions
                    ),
                    successful_executions=(
                        successful_executions
                    ),
                    failed_executions=(
                        failed_executions
                    ),
                    total_duration_ms=(
                        total_duration_ms
                    ),
                    retry_count=retry_count,
                    efficiency_score=(
                        efficiency_score
                    ),
                )

            # ----------------------------------------------------
            # Agent performance
            # ----------------------------------------------------

            persisted_agent_performance = (
                analytics.get(
                    "agent_performance",
                    [],
                )
            )

            if persisted_agent_performance:
                agent_performance = (
                    cls.normalize_agent_performance(
                        persisted_agent_performance
                    )
                )

            else:
                agent_stats: dict[
                    str,
                    dict[str, Any],
                ] = {}

                for entry in timeline_data:
                    agent = (
                        entry.agent
                        or "unknown"
                    )

                    if agent not in agent_stats:
                        agent_stats[agent] = {
                            "agent": agent,
                            "executions": 0,
                            "successful_executions": 0,
                            "failed_executions": 0,
                            "total_duration_ms": 0.0,
                        }

                    stats = agent_stats[
                        agent
                    ]

                    stats[
                        "executions"
                    ] += 1

                    status = str(
                        entry.status or ""
                    ).upper()

                    if status in {
                        "COMPLETED",
                        "SUCCESS",
                        "SUCCEEDED",
                    }:
                        stats[
                            "successful_executions"
                        ] += 1

                    elif status in {
                        "FAILED",
                        "FAILURE",
                        "ERROR",
                    }:
                        stats[
                            "failed_executions"
                        ] += 1

                    stats[
                        "total_duration_ms"
                    ] += float(
                        entry.duration_ms
                        or 0.0
                    )

                for stats in agent_stats.values():
                    executions = int(
                        stats[
                            "executions"
                        ]
                    )

                    total_duration_ms = float(
                        stats[
                            "total_duration_ms"
                        ]
                    )

                    stats[
                        "average_duration_ms"
                    ] = (
                        total_duration_ms
                        / executions
                        if executions
                        else 0.0
                    )

                    stats[
                        "failure_rate"
                    ] = (
                        (
                            stats[
                                "failed_executions"
                            ]
                            / executions
                        )
                        * 100.0
                        if executions
                        else 0.0
                    )

                agent_performance = (
                    cls.normalize_agent_performance(
                        list(
                            agent_stats.values()
                        )
                    )
                )

            # ----------------------------------------------------
            # Bottlenecks
            # ----------------------------------------------------

            bottlenecks = (
                cls.normalize_bottlenecks(
                    analytics.get(
                        "bottlenecks",
                        [],
                    )
                )
            )

            # ----------------------------------------------------
            # Failure / retry metrics
            # ----------------------------------------------------

            persisted_failure_retry = (
                cls._safe_dict(
                    analytics.get(
                        "failure_retry_metrics",
                        analytics.get(
                            "failure_retry",
                            {},
                        ),
                    )
                )
            )

            if persisted_failure_retry:
                failure_retry_metrics = (
                    cls.normalize_failure_retry_metrics(
                        persisted_failure_retry
                    )
                )

            else:
                failed_agents: dict[
                    str,
                    int,
                ] = {}

                retry_by_agent: dict[
                    str,
                    int,
                ] = {}

                for entry in timeline_data:
                    agent = (
                        entry.agent
                        or "unknown"
                    )

                    status = str(
                        entry.status or ""
                    ).upper()

                    if status in {
                        "FAILED",
                        "FAILURE",
                        "ERROR",
                    }:
                        failed_agents[
                            agent
                        ] = (
                            failed_agents.get(
                                agent,
                                0,
                            )
                            + 1
                        )

                    metadata = (
                        entry.metadata
                        or {}
                    )

                    retries = 0

                    if "retry_count" in metadata:
                        retries = max(
                            0,
                            cls._safe_int(
                                metadata.get(
                                    "retry_count"
                                )
                            ),
                        )

                    elif "retries" in metadata:
                        retries = max(
                            0,
                            cls._safe_int(
                                metadata.get(
                                    "retries"
                                )
                            ),
                        )

                    elif "attempt" in metadata:
                        attempt = max(
                            1,
                            cls._safe_int(
                                metadata.get(
                                    "attempt"
                                ),
                                1,
                            ),
                        )

                        retries = max(
                            0,
                            attempt - 1,
                        )

                    elif (
                        "attempt_number"
                        in metadata
                    ):
                        attempt = max(
                            1,
                            cls._safe_int(
                                metadata.get(
                                    "attempt_number"
                                ),
                                1,
                            ),
                        )

                        retries = max(
                            0,
                            attempt - 1,
                        )

                    if retries:
                        retry_by_agent[
                            agent
                        ] = (
                            retry_by_agent.get(
                                agent,
                                0,
                            )
                            + retries
                        )

                failure_retry_metrics = (
                    cls.normalize_failure_retry_metrics(
                        {
                            "total_failures": sum(
                                failed_agents.values()
                            ),
                            "total_retries": sum(
                                retry_by_agent.values()
                            ),
                            "failed_agents": (
                                failed_agents
                            ),
                            "retry_by_agent": (
                                retry_by_agent
                            ),
                        }
                    )
                )

            # ----------------------------------------------------
            # Final response
            # ----------------------------------------------------

            result = (
                InvestigationAnalyticsDashboardRead(
                    investigation_id=(
                        investigation_id
                    ),
                    overview=overview,
                    agent_performance=(
                        agent_performance
                    ),
                    bottlenecks=bottlenecks,
                    failure_retry_metrics=(
                        failure_retry_metrics
                    ),
                    timeline=timeline_data,
                )
            )

            # ----------------------------------------------------
            # Metrics
            # ----------------------------------------------------

            if original_was_dict:
                metrics.record_analytics_validation(
                    status="success"
                )
            else:
                metrics.record_analytics_validation(
                    status="normalized"
                )

            return result

        except Exception:
            metrics.record_analytics_validation(
                status="failure"
            )
            raise
