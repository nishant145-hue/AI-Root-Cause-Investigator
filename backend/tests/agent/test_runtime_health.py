from concurrent.futures import Future

import pytest

from app.agent.execution_manager import (
    AgentExecutionManager,
)


def test_runtime_health_reports_healthy_state():
    manager = AgentExecutionManager(
        max_workers=2,
        max_per_investigation=2,
        max_queue_size=2,
    )

    try:
        snapshot = manager.runtime_health_snapshot()

        assert snapshot["status"] == "HEALTHY"

        assert snapshot["shutdown"]["state"] == "RUNNING"
        assert snapshot["shutdown"]["closed"] is False

        assert snapshot["execution"]["active"] == 0
        assert snapshot["execution"]["limit"] == 2
        assert snapshot["execution"]["available"] == 2
        assert snapshot["execution"]["queued"] == 0
        assert snapshot["execution"]["queue_limit"] == 2

        assert snapshot["investigations"]["tracked"] == 0
        assert snapshot["investigations"]["running"] == 0

    finally:
        manager.shutdown()


def test_runtime_health_reports_saturated_state():
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event

    manager = AgentExecutionManager(
        max_workers=1,
        max_per_investigation=1,
        max_queue_size=1,
    )

    started = Event()
    release = Event()

    def blocking_task():
        started.set()
        release.wait(timeout=10)
        return "released"

    executor = ThreadPoolExecutor(max_workers=1)

    try:
        future = executor.submit(
            manager.run,
            12345,
            "saturation_test_agent",
            blocking_task,
        )

        assert started.wait(timeout=5)

        snapshot = manager.runtime_health_snapshot()

        assert snapshot["status"] == "SATURATED"
        assert snapshot["execution"]["active"] == 1
        assert snapshot["execution"]["limit"] == 1
        assert snapshot["execution"]["available"] == 0
        assert snapshot["investigations"]["running"] >= 1

        release.set()
        assert future.result(timeout=10) == "released"

    finally:
        release.set()
        executor.shutdown(wait=True)
        manager.shutdown()

def test_runtime_health_reports_shutting_down_state():
    manager = AgentExecutionManager(
        max_workers=1,
        max_per_investigation=1,
        max_queue_size=1,
    )

    assert (
        manager.runtime_health_snapshot()["status"]
        == "HEALTHY"
    )

    manager.shutdown()

    snapshot = manager.runtime_health_snapshot()

    assert snapshot["status"] == "SHUTTING_DOWN"
    assert snapshot["shutdown"]["state"] == "SHUTTING_DOWN"
    assert snapshot["shutdown"]["closed"] is True


def test_runtime_health_tracks_investigation_execution():
    manager = AgentExecutionManager(
        max_workers=2,
        max_per_investigation=2,
        max_queue_size=2,
    )

    try:
        result = manager.run(
            12345,
            "health_test_agent",
            lambda: "success",
        )

        assert result == "success"

        snapshot = manager.runtime_health_snapshot()

        assert snapshot["investigations"]["tracked"] >= 1
        assert snapshot["investigations"]["completed_tasks"] >= 1
    finally:
        manager.shutdown()

def test_runtime_health_reports_degraded_state_after_failure():
    manager = AgentExecutionManager(
        max_workers=1,
        max_per_investigation=1,
        max_queue_size=1,
    )

    def failing_task():
        raise RuntimeError("intentional health test failure")

    try:
        with pytest.raises(RuntimeError, match="intentional health test failure"):
            manager.run(
                12345,
                "degraded_test_agent",
                failing_task,
            )

        snapshot = manager.runtime_health_snapshot()

        assert snapshot["status"] == "DEGRADED"
        assert snapshot["investigations"]["failed_tasks"] >= 1
        assert snapshot["failures"]["aggregate"]

    finally:
        manager.shutdown()
