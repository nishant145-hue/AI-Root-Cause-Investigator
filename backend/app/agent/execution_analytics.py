from typing import Any


class InvestigationExecutionAnalytics:
    """
    Calculate analytics from a unified investigation
    execution timeline.

    This class is read-only. It does not modify
    the investigation timeline.
    """

    def __init__(
        self,
        timeline: list[dict[str, Any]] | None = None,
    ) -> None:

        self.timeline = list(
            timeline or []
        )

    # ---------------------------------------------------------
    # Basic execution metrics
    # ---------------------------------------------------------

    def total_executions(self) -> int:
        return len(self.timeline)

    def successful_executions(self) -> int:
        return sum(
            1
            for trace in self.timeline
            if trace.get("status") == "COMPLETED"
        )

    def failed_executions(self) -> int:
        return sum(
            1
            for trace in self.timeline
            if trace.get("status") == "FAILED"
        )

    def total_duration_ms(self) -> float:
        return round(
            sum(
                float(
                    trace.get(
                        "duration_ms",
                        0.0,
                    )
                    or 0.0
                )
                for trace in self.timeline
            ),
            2,
        )

    # ---------------------------------------------------------
    # Retry metrics
    # ---------------------------------------------------------

    def retry_count(self) -> int:
        attempts = [
            int(
                trace.get(
                    "attempt",
                    1,
                )
                or 1
            )
            for trace in self.timeline
        ]

        return sum(
            max(attempt - 1, 0)
            for attempt in attempts
        )

    # ---------------------------------------------------------
    # Agent metrics
    # ---------------------------------------------------------

    def agent_execution_counts(
        self,
    ) -> dict[str, int]:

        counts: dict[str, int] = {}

        for trace in self.timeline:

            agent = trace.get(
                "agent",
                "unknown",
            )

            counts[agent] = (
                counts.get(agent, 0) + 1
            )

        return counts

    def slowest_agent(self) -> str | None:

        if not self.timeline:
            return None

        slowest = max(
            self.timeline,
            key=lambda trace: float(
                trace.get(
                    "duration_ms",
                    0.0,
                )
                or 0.0
            ),
        )

        return slowest.get("agent")

    def slowest_agent_duration_ms(
        self,
    ) -> float:

        if not self.timeline:
            return 0.0

        slowest = max(
            self.timeline,
            key=lambda trace: float(
                trace.get(
                    "duration_ms",
                    0.0,
                )
                or 0.0
            ),
        )

        return round(
            float(
                slowest.get(
                    "duration_ms",
                    0.0,
                )
                or 0.0
            ),
            2,
        )

    # ---------------------------------------------------------
    # Combined analytics
    # ---------------------------------------------------------

    def summary(self) -> dict[str, Any]:
        return {
            "total_executions": (
                self.total_executions()
            ),
            "successful_executions": (
                self.successful_executions()
            ),
            "failed_executions": (
                self.failed_executions()
            ),
            "total_duration_ms": (
                self.total_duration_ms()
            ),
            "retry_count": (
                self.retry_count()
            ),
            "slowest_agent": (
                self.slowest_agent()
            ),
            "slowest_agent_duration_ms": (
                self.slowest_agent_duration_ms()
            ),
            "agent_execution_counts": (
                self.agent_execution_counts()
            ),
        }

    def agent_performance(
        self,
    ) -> dict[str, dict[str, float | int]]:
        """
        Calculate performance metrics for every agent.
        """

        performance: dict[
            str,
            dict[str, float | int],
        ] = {}

        for trace in self.timeline:

            agent = trace.get(
                "agent",
                "unknown",
            )

            duration = float(
                trace.get(
                    "duration_ms",
                    0.0,
                )
                or 0.0
            )

            status = trace.get(
                "status"
            )

            if agent not in performance:
                performance[agent] = {
                    "execution_count": 0,
                    "success_count": 0,
                    "failure_count": 0,
                    "total_duration_ms": 0.0,
                    "average_duration_ms": 0.0,
                    "failure_rate": 0.0,
                }

            metrics = performance[agent]

            metrics["execution_count"] += 1

            if status == "COMPLETED":
                metrics["success_count"] += 1

            elif status == "FAILED":
                metrics["failure_count"] += 1

            metrics["total_duration_ms"] += duration

        for metrics in performance.values():

            execution_count = int(
                metrics["execution_count"]
            )

            total_duration = float(
                metrics["total_duration_ms"]
            )

            failure_count = int(
                metrics["failure_count"]
            )

            if execution_count:
                metrics[
                    "average_duration_ms"
                ] = round(
                    total_duration
                    / execution_count,
                    2,
                )

                metrics[
                    "failure_rate"
                ] = round(
                    failure_count
                    / execution_count,
                    4,
                )

            metrics[
                "total_duration_ms"
            ] = round(
                total_duration,
                2,
            )

        return performance


    def failure_retry_metrics(
        self,
    ) -> dict[str, Any]:
        """
        Calculate failure and retry metrics for
        the investigation execution timeline.
        """

        failed_traces = [
            trace
            for trace in self.timeline
            if trace.get("status") == "FAILED"
        ]

        retry_traces = [
            trace
            for trace in self.timeline
            if int(
                trace.get(
                    "attempt",
                    1,
                )
                or 1
            ) > 1
        ]

        failures_by_agent: dict[str, int] = {}

        retries_by_agent: dict[str, int] = {}

        for trace in failed_traces:

            agent = trace.get(
                "agent",
                "unknown",
            )

            failures_by_agent[agent] = (
                failures_by_agent.get(agent, 0)
                + 1
            )

        for trace in retry_traces:

            agent = trace.get(
                "agent",
                "unknown",
            )

            retries_by_agent[agent] = (
                retries_by_agent.get(agent, 0)
                + 1
            )

        return {
            "total_failures": len(
                failed_traces
            ),
            "total_retries": len(
                retry_traces
            ),
            "failures_by_agent": (
                failures_by_agent
            ),
            "retries_by_agent": (
                retries_by_agent
            ),
        }

    def bottleneck_agents(
        self,
        threshold_multiplier: float = 1.5,
    ) -> list[dict[str, Any]]:
        """
        Identify agents whose average execution
        duration is significantly above the overall
        average execution duration.
        """

        if not self.timeline:
            return []

        durations = [
            float(
                trace.get(
                    "duration_ms",
                    0.0,
                )
                or 0.0
            )
            for trace in self.timeline
        ]

        overall_average = (
            sum(durations) / len(durations)
        )

        if overall_average <= 0:
            return []

        performance = self.agent_performance()

        bottlenecks = []

        for agent, metrics in performance.items():

            average_duration = float(
                metrics["average_duration_ms"]
            )

            if (
                average_duration
                > overall_average
                * threshold_multiplier
            ):
                bottlenecks.append(
                    {
                        "agent": agent,
                        "average_duration_ms": (
                            average_duration
                        ),
                        "overall_average_duration_ms": (
                            round(
                                overall_average,
                                2,
                            )
                        ),
                        "slowdown_ratio": round(
                            average_duration
                            / overall_average,
                            2,
                        ),
                    }
                )

        bottlenecks.sort(
            key=lambda item: item[
                "average_duration_ms"
            ],
            reverse=True,
        )

        return bottlenecks

    def efficiency_score(
        self,
    ) -> dict[str, Any]:
        """
        Calculate an overall investigation efficiency score
        between 0 and 100.
        """

        if not self.timeline:
            return {
                "score": 0.0,
                "rating": "NO_DATA",
                "success_rate": 0.0,
                "failure_rate": 0.0,
                "retry_rate": 0.0,
                "bottleneck_count": 0,
            }

        total = len(self.timeline)

        completed = sum(
            1
            for trace in self.timeline
            if trace.get("status") == "COMPLETED"
        )

        failed = sum(
            1
            for trace in self.timeline
            if trace.get("status") == "FAILED"
        )

        retries = sum(
            1
            for trace in self.timeline
            if int(
                trace.get("attempt", 1) or 1
            ) > 1
        )

        success_rate = completed / total
        failure_rate = failed / total
        retry_rate = retries / total

        bottlenecks = self.bottleneck_agents()

        # ---------------------------------------------------------
        # Efficiency scoring
        # ---------------------------------------------------------

        score = (
            success_rate * 60
            + (1 - failure_rate) * 20
            + (1 - retry_rate) * 20
        )

        # Penalize bottlenecks.
        score -= len(bottlenecks) * 5

        score = max(
            0.0,
            min(
                100.0,
                score,
            ),
        )

        score = round(
            score,
            2,
        )

        if score >= 90:
            rating = "EXCELLENT"

        elif score >= 75:
            rating = "GOOD"

        elif score >= 50:
            rating = "FAIR"

        else:
            rating = "POOR"

        return {
            "score": score,
            "rating": rating,
            "success_rate": round(
                success_rate,
                4,
            ),
            "failure_rate": round(
                failure_rate,
                4,
            ),
            "retry_rate": round(
                retry_rate,
                4,
            ),
            "bottleneck_count": len(
                bottlenecks
            ),
        }

    def unified_summary(self) -> dict[str, Any]:
        """
        Return a unified analytics summary.

        Combines the original execution metrics with
        advanced agent performance, failure/retry,
        bottleneck, and efficiency analytics.
        """

        return {
            "execution": {
                "total_executions": (
                    self.total_executions()
                ),
                "successful_executions": (
                    self.successful_executions()
                ),
                "failed_executions": (
                    self.failed_executions()
                ),
                "total_duration_ms": (
                    self.total_duration_ms()
                ),
                "retry_count": (
                    self.retry_count()
                ),
                "agent_execution_counts": (
                    self.agent_execution_counts()
                ),
                "slowest_agent": (
                    self.slowest_agent()
                ),
                "slowest_agent_duration_ms": (
                    self.slowest_agent_duration_ms()
                ),
            },
            "agent_performance": (
            self.agent_performance()
            ),
            "failure_retry": (
                self.failure_retry_metrics()
            ),
            "bottlenecks": (
                self.bottleneck_agents()
            ),
            "efficiency": (
                self.efficiency_score()
            ),
        }
