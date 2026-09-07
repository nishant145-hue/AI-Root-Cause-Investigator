import threading
import time

from app.agent.execution_manager import (
    AgentExecutionManager,
)


def test_resource_snapshot_starts_empty():
    manager = AgentExecutionManager(
        max_workers=2,
        max_per_investigation=2,
        max_queue_size=5,
    )

    try:
        snapshot = (
            manager.resource_metrics_snapshot()
        )

        assert snapshot["queued_count"] == 0
        assert snapshot["active_workers"] == 0
        assert snapshot["available_workers"] == 2
        assert snapshot["max_workers"] == 2
        assert snapshot["max_queue_size"] == 5
        assert snapshot["worker_utilization"] == 0.0

    finally:
        manager.shutdown()


def test_completed_execution_records_resource_metric():
    manager = AgentExecutionManager(
        max_workers=2,
        max_per_investigation=2,
        max_queue_size=5,
    )

    try:
        execution, future = manager.submit(
            investigation_id=100,
            agent_name="investigator",
            fn=lambda: "ok",
        )

        assert future.result(timeout=3) == "ok"

        history = (
            manager.resource_metrics_history()
        )

        assert len(history) == 1

        metric = history[0]

        assert (
            metric["execution_id"]
            == execution.execution_id
        )

        assert (
            metric["investigation_id"]
            == 100
        )

        assert (
            metric["agent_name"]
            == "investigator"
        )

        assert (
            metric["queue_wait_ms"]
            >= 0
        )

    finally:
        manager.shutdown()


def test_worker_utilization_returns_to_zero():
    manager = AgentExecutionManager(
        max_workers=1,
        max_per_investigation=1,
    )

    started = threading.Event()
    release = threading.Event()

    def worker():
        started.set()
        release.wait(timeout=3)
        return "ok"

    try:
        _, future = manager.submit(
            investigation_id=1,
            agent_name="investigator",
            fn=worker,
        )

        assert started.wait(timeout=3)

        snapshot = (
            manager.resource_metrics_snapshot()
        )

        assert snapshot["active_workers"] == 1
        assert snapshot["max_active_workers"] >= 1
        assert snapshot["worker_utilization"] == 1.0

        release.set()

        assert future.result(timeout=3) == "ok"

        snapshot = (
            manager.resource_metrics_snapshot()
        )

        assert snapshot["active_workers"] == 0
        assert snapshot["available_workers"] == 1

    finally:
        release.set()
        manager.shutdown()


def test_resource_metrics_can_be_reset():
    manager = AgentExecutionManager()

    try:
        manager.run(
            investigation_id=1,
            agent_name="investigator",
            fn=lambda: "ok",
        )

        assert (
            manager.resource_metrics_history()
        )

        manager.reset_resource_metrics()

        assert (
            manager.resource_metrics_history()
            == []
        )

        snapshot = (
            manager.resource_metrics_snapshot()
        )

        assert snapshot["queued_count"] == 0
        assert snapshot["max_queue_depth"] == 0
        assert snapshot["max_active_workers"] == 0

    finally:
        manager.shutdown()
