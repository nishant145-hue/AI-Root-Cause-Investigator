from __future__ import annotations

import threading
import time

import pytest

from app.agent.execution_manager import (
    AgentExecutionError,
    AgentExecutionManager,
    AgentResourceExhaustedError,
)


def test_manager_executes_agent():

    manager = AgentExecutionManager(
        max_workers=2,
        max_per_investigation=1,
    )

    try:

        result = manager.run(
            investigation_id=1,
            agent_name="investigator",
            fn=lambda: {
                "status": "success"
            },
        )

        assert result == {
            "status": "success"
        }

        assert manager.active_count() == 0

    finally:
        manager.shutdown()


def test_execution_has_unique_id():

    manager = AgentExecutionManager(
        max_workers=2,
        max_per_investigation=2,
    )

    try:

        execution_1, future_1 = manager.submit(
            investigation_id=1,
            agent_name="investigator",
            fn=lambda: "one",
        )

        execution_2, future_2 = manager.submit(
            investigation_id=1,
            agent_name="reasoner",
            fn=lambda: "two",
        )

        assert (
            execution_1.execution_id
            != execution_2.execution_id
        )

        assert (
            execution_1.agent_name
            == "investigator"
        )

        assert (
            execution_2.agent_name
            == "reasoner"
        )

        assert future_1.result() == "one"
        assert future_2.result() == "two"

    finally:
        manager.shutdown()


def test_global_concurrency_limit():

    manager = AgentExecutionManager(
        max_workers=1,
        max_per_investigation=1,
    )

    started = threading.Event()
    release = threading.Event()

    def blocking_agent():

        started.set()

        release.wait(
            timeout=5
        )

        return "done"

    try:

        _, future = manager.submit(
            investigation_id=1,
            agent_name="investigator",
            fn=blocking_agent,
        )

        assert started.wait(
            timeout=2
        )

        with pytest.raises(
            AgentResourceExhaustedError
        ):

            manager.submit(
                investigation_id=2,
                agent_name="reasoner",
                fn=lambda: "blocked",
            )

        release.set()

        assert future.result(
            timeout=2
        ) == "done"

    finally:

        release.set()
        manager.shutdown()


def test_per_investigation_limit():

    manager = AgentExecutionManager(
        max_workers=3,
        max_per_investigation=1,
    )

    started = threading.Event()
    release = threading.Event()

    def blocking_agent():

        started.set()

        release.wait(
            timeout=5
        )

        return "done"

    try:

        _, future = manager.submit(
            investigation_id=100,
            agent_name="investigator",
            fn=blocking_agent,
        )

        assert started.wait(
            timeout=2
        )

        with pytest.raises(
            AgentResourceExhaustedError
        ):

            manager.submit(
                investigation_id=100,
                agent_name="reasoner",
                fn=lambda: "blocked",
            )

        # A different investigation is still allowed.
        _, other_future = manager.submit(
            investigation_id=200,
            agent_name="reasoner",
            fn=lambda: "other",
        )

        assert other_future.result(
            timeout=2
        ) == "other"

        release.set()

        assert future.result(
            timeout=2
        ) == "done"

    finally:

        release.set()
        manager.shutdown()


def test_resources_are_released_after_exception():

    manager = AgentExecutionManager(
        max_workers=1,
        max_per_investigation=1,
    )

    def failing_agent():

        raise RuntimeError(
            "agent failed"
        )

    try:

        with pytest.raises(
            RuntimeError,
            match="agent failed",
        ):

            manager.run(
                investigation_id=1,
                agent_name="investigator",
                fn=failing_agent,
            )

        assert manager.active_count() == 0

        # Capacity should be reusable.
        result = manager.run(
            investigation_id=1,
            agent_name="investigator",
            fn=lambda: "recovered",
        )

        assert result == "recovered"

    finally:
        manager.shutdown()


def test_resources_are_released_after_success():

    manager = AgentExecutionManager(
        max_workers=1,
        max_per_investigation=1,
    )

    try:

        result = manager.run(
            investigation_id=50,
            agent_name="investigator",
            fn=lambda: "success",
        )

        assert result == "success"

        assert (
            manager.active_count_for_investigation(
                50
            )
            == 0
        )

    finally:
        manager.shutdown()


def test_closed_manager_rejects_new_execution():

    manager = AgentExecutionManager(
        max_workers=1,
        max_per_investigation=1,
    )

    manager.shutdown()

    with pytest.raises(
        AgentExecutionError,
        match="closed",
    ):

        manager.submit(
            investigation_id=1,
            agent_name="investigator",
            fn=lambda: "blocked",
        )


def test_invalid_configuration():

    with pytest.raises(
        ValueError
    ):

        AgentExecutionManager(
            max_workers=0
        )

    with pytest.raises(
        ValueError
    ):

        AgentExecutionManager(
            max_workers=2,
            max_per_investigation=0,
        )

    with pytest.raises(
        ValueError
    ):

        AgentExecutionManager(
            max_workers=1,
            max_per_investigation=2,
        )

def test_available_global_capacity():

    manager = AgentExecutionManager(
        max_workers=3,
        max_per_investigation=2,
    )

    try:
        assert (
            manager.available_capacity()
            == 3
        )

        _, future = manager.submit(
            1,
            "investigator",
            lambda: "done",
        )

        assert future.result(
            timeout=2
        ) == "done"

        assert (
            manager.available_capacity()
            == 3
        )

    finally:
        manager.shutdown()


def test_available_investigation_capacity():

    manager = AgentExecutionManager(
        max_workers=5,
        max_per_investigation=2,
    )

    try:

        assert (
            manager.available_capacity_for_investigation(
                100
            )
            == 2
        )

    finally:
        manager.shutdown()


def test_investigation_resource_snapshot():

    manager = AgentExecutionManager(
        max_workers=5,
        max_per_investigation=2,
    )

    try:

        snapshot = (
            manager.investigation_resource_snapshot(
                100
            )
        )

        assert snapshot == {
            "active": 0,
            "limit": 2,
            "available": 2,
        }

    finally:
        manager.shutdown()


def test_global_resource_snapshot():

    manager = AgentExecutionManager(
        max_workers=5,
        max_per_investigation=2,
    )

    try:

        snapshot = (
            manager.resource_snapshot()
        )

        assert snapshot == {
            "active": 0,
            "limit": 5,
            "available": 5,
            "queued": 0,
            "queue_limit": 20,
            "queue_available": 20,
        }
    finally:
        manager.shutdown()

def test_one_investigation_cannot_monopolize_workers():

    import threading

    manager = AgentExecutionManager(
        max_workers=4,
        max_per_investigation=2,
    )

    release = threading.Event()
    started = threading.Event()

    def blocking_agent():

        started.set()

        release.wait(
            timeout=5
        )

        return "done"

    try:

        # Investigation 1 consumes its entire quota.
        _, future_1 = manager.submit(
            1,
            "investigator",
            blocking_agent,
        )

        _, future_2 = manager.submit(
            1,
            "reasoner",
            blocking_agent,
        )

        assert started.wait(
            timeout=2
        )

        assert (
            manager.active_count_for_investigation(
                1
            )
            == 2
        )

        # Investigation 1 cannot acquire another slot.
        with pytest.raises(
            AgentResourceExhaustedError
        ):

            manager.submit(
                1,
                "validator",
                lambda: "blocked",
            )

        # But Investigation 2 can still execute.
        _, other_future = manager.submit(
            2,
            "investigator",
            lambda: "investigation-2",
        )

        assert other_future.result(
            timeout=2
        ) == "investigation-2"

        release.set()

        assert future_1.result(
            timeout=2
        ) == "done"

        assert future_2.result(
            timeout=2
        ) == "done"

    finally:

        release.set()
        manager.shutdown()

def test_queue_limit_is_configurable():

    manager = AgentExecutionManager(
        max_workers=1,
        max_per_investigation=1,
        max_queue_size=2,
    )

    try:

        assert manager.max_queue_size == 2

        assert (
            manager.queue_available_capacity()
            == 2
        )

    finally:
        manager.shutdown()


def test_queue_count_is_zero_when_idle():

    manager = AgentExecutionManager(
        max_workers=2,
        max_per_investigation=1,
        max_queue_size=2,
    )

    try:

        assert manager.queued_count() == 0

    finally:
        manager.shutdown()


def test_resource_snapshot_contains_queue_information():

    manager = AgentExecutionManager(
        max_workers=2,
        max_per_investigation=1,
        max_queue_size=5,
    )

    try:

        snapshot = (
            manager.resource_snapshot()
        )

        assert snapshot == {
            "active": 0,
            "limit": 2,
            "available": 2,
            "queued": 0,
            "queue_limit": 5,
            "queue_available": 5,
        }

    finally:
        manager.shutdown()


def test_negative_queue_size_is_rejected():

    with pytest.raises(
        ValueError,
        match="max_queue_size",
    ):

        AgentExecutionManager(
            max_workers=2,
            max_per_investigation=1,
            max_queue_size=-1,
        )

def test_execution_creates_running_span():
    manager = AgentExecutionManager(
        max_workers=2,
        max_per_investigation=2,
    )

    try:
        execution, future = manager.submit(
            investigation_id=200,
            agent_name="investigator",
            fn=lambda: "ok",
        )

        assert execution.span is not None

        assert (
            execution.span.trace_id
            == execution.trace_id
        )

        assert (
            execution.span.span_id
            == execution.span_id
        )

        assert (
            execution.span.parent_span_id
            == execution.parent_span_id
        )

        assert (
            future.result(timeout=3)
            == "ok"
        )

        assert (
            execution.span.status
            == "COMPLETED"
        )

        assert (
            execution.span.ended_at
            is not None
        )

        assert (
            execution.span.duration_ms
            is not None
        )

        assert (
            execution.span.duration_ms
            >= 0
        )

    finally:
        manager.shutdown()


def test_failed_execution_fails_span():
    manager = AgentExecutionManager(
        max_workers=2,
        max_per_investigation=2,
    )

    def failing_agent():
        raise RuntimeError(
            "span failure"
        )

    try:
        execution, future = manager.submit(
            investigation_id=201,
            agent_name="reasoner",
            fn=failing_agent,
        )

        with pytest.raises(
            RuntimeError,
            match="span failure",
        ):
            future.result(timeout=3)

        assert execution.span is not None

        assert (
            execution.span.status
            == "FAILED"
        )

        assert (
            execution.span.error
            == "span failure"
        )

        assert (
            execution.span.ended_at
            is not None
        )

    finally:
        manager.shutdown()


def test_execution_span_contains_execution_metadata():
    manager = AgentExecutionManager(
        max_workers=2,
        max_per_investigation=2,
    )

    try:
        execution, future = manager.submit(
            investigation_id=202,
            agent_name="validator",
            fn=lambda: "ok",
        )

        assert (
            future.result(timeout=3)
            == "ok"
        )

        spans = (
            manager.execution_spans()
        )

        assert len(spans) == 1

        span = spans[0]

        assert (
            span["trace_id"]
            == execution.trace_id
        )

        assert (
            span["span_id"]
            == execution.span_id
        )

        assert (
            span["parent_span_id"]
            == execution.parent_span_id
        )

        assert (
            span["agent"]
            == "validator"
        )

        assert (
            span["action"]
            == "agent_execution"
        )

        assert (
            span["status"]
            == "COMPLETED"
        )

        assert (
            span["attributes"][
                "execution_id"
            ]
            == execution.execution_id
        )

        assert (
            span["attributes"][
                "investigation_id"
            ]
            == 202
        )

    finally:
        manager.shutdown()


def test_reset_execution_spans():
    manager = AgentExecutionManager(
        max_workers=2,
        max_per_investigation=2,
    )

    try:
        manager.run(
            investigation_id=203,
            agent_name="memory",
            fn=lambda: "ok",
        )

        assert len(
            manager.execution_spans()
        ) == 1

        manager.reset_execution_spans()

        assert (
            manager.execution_spans()
            == []
        )

    finally:
        manager.shutdown()

def test_per_investigation_concurrency_limit_is_enforced():
    """
    Verify that AgentExecutionManager rejects executions beyond
    the configured per-investigation concurrency limit.
    """

    import threading

    from app.agent.execution_manager import (
        AgentExecutionManager,
        AgentResourceExhaustedError,
    )

    manager = AgentExecutionManager(
        max_workers=10,
        max_per_investigation=2,
        max_queue_size=20,
    )

    investigation_id = 5001

    start_execution = threading.Event()
    release_execution = threading.Event()

    results = []
    results_lock = threading.Lock()

    def worker():
        start_execution.set()
        release_execution.wait(timeout=10)
        return "completed"

    def execute():
        try:
            result = manager.run(
                investigation_id=investigation_id,
                agent_name="concurrency-test-agent",
                fn=worker,
            )

            with results_lock:
                results.append(("completed", result))

        except AgentResourceExhaustedError as exc:
            with results_lock:
                results.append(("rejected", str(exc)))

    try:
        threads = [
            threading.Thread(target=execute)
            for _ in range(4)
        ]

        for thread in threads:
            thread.start()

        assert start_execution.wait(timeout=5)

        # At this point the first two executions should occupy
        # the per-investigation capacity.
        assert manager.active_count_for_investigation(
            investigation_id
        ) <= 2

        # Allow the accepted executions to finish.
        release_execution.set()

        for thread in threads:
            thread.join(timeout=10)

        assert all(
            not thread.is_alive()
            for thread in threads
        )

        completed = [
            item
            for item in results
            if item[0] == "completed"
        ]

        rejected = [
            item
            for item in results
            if item[0] == "rejected"
        ]

        # Exactly two executions may be admitted concurrently.
        assert len(completed) == 2
        assert len(rejected) == 2

        assert manager.active_count_for_investigation(
            investigation_id
        ) == 0

    finally:
        release_execution.set()

        manager.shutdown()

def test_per_investigation_limit_does_not_block_other_investigations():
    """
    Verify that the per-investigation limit is isolated:
    one investigation reaching its limit must not prevent
    another investigation from executing.
    """

    import threading

    from app.agent.execution_manager import AgentExecutionManager

    manager = AgentExecutionManager(
        max_workers=4,
        max_per_investigation=2,
        max_queue_size=20,
    )

    investigation_a = 6001
    investigation_b = 6002

    release_a = threading.Event()
    started_a = threading.Event()

    results = []
    results_lock = threading.Lock()

    def worker_a():
        started_a.set()
        release_a.wait(timeout=10)
        return "A"

    def worker_b():
        return "B"

    def execute_a():
        try:
            result = manager.run(
                investigation_id=investigation_a,
                agent_name="agent-a",
                fn=worker_a,
            )

            with results_lock:
                results.append(("A", "completed", result))

        except Exception as exc:
            with results_lock:
                results.append(("A", "failed", type(exc).__name__))

    def execute_b():
        try:
            result = manager.run(
                investigation_id=investigation_b,
                agent_name="agent-b",
                fn=worker_b,
            )

            with results_lock:
                results.append(("B", "completed", result))

        except Exception as exc:
            with results_lock:
                results.append(("B", "failed", type(exc).__name__))

    try:
        threads_a = [
            threading.Thread(target=execute_a)
            for _ in range(2)
        ]

        for thread in threads_a:
            thread.start()

        assert started_a.wait(timeout=5)

        # Both slots for investigation A should be occupied.
        assert manager.active_count_for_investigation(
            investigation_a
        ) == 2

        # Investigation B must still be able to execute.
        thread_b = threading.Thread(target=execute_b)
        thread_b.start()
        thread_b.join(timeout=5)

        assert not thread_b.is_alive()

        with results_lock:
            b_results = [
                item
                for item in results
                if item[0] == "B"
            ]

        assert b_results == [
            ("B", "completed", "B")
        ]

        # Release investigation A.
        release_a.set()

        for thread in threads_a:
            thread.join(timeout=10)

        assert all(
            not thread.is_alive()
            for thread in threads_a
        )

        with results_lock:
            a_results = [
                item
                for item in results
                if item[0] == "A"
            ]

        assert len(a_results) == 2
        assert all(
            item[1:] == ("completed", "A")
            for item in a_results
        )

    finally:
        release_a.set()

        manager.shutdown()

def test_distributed_state_tracks_successful_execution():
    """
    Verify that a successful manager execution updates
    distributed investigation state correctly.
    """

    from app.agent.execution_manager import AgentExecutionManager

    manager = AgentExecutionManager(
        max_workers=2,
        max_per_investigation=2,
        max_queue_size=20,
    )

    investigation_id = 7001

    try:
        result = manager.run(
            investigation_id=investigation_id,
            agent_name="investigator",
            fn=lambda: "success",
        )

        assert result == "success"

        snapshot = manager.distributed_state.snapshot(
            investigation_id
        )

        assert snapshot["investigation_id"] == investigation_id
        assert snapshot["active_tasks"] == 0
        assert snapshot["queued_tasks"] == 0
        assert snapshot["completed_tasks"] == 1
        assert snapshot["failed_tasks"] == 0
        assert snapshot["last_agent"] == "investigator"

    finally:
        manager.shutdown()

def test_distributed_state_tracks_failed_execution():
    """
    Verify that a failed manager execution updates
    distributed investigation state correctly.
    """

    import pytest

    from app.agent.execution_manager import AgentExecutionManager

    manager = AgentExecutionManager(
        max_workers=2,
        max_per_investigation=2,
        max_queue_size=20,
    )

    investigation_id = 7002

    def failing_agent():
        raise RuntimeError("simulated execution failure")

    try:
        with pytest.raises(
            RuntimeError,
            match="simulated execution failure",
        ):
            manager.run(
                investigation_id=investigation_id,
                agent_name="reasoner",
                fn=failing_agent,
            )

        snapshot = manager.distributed_state.snapshot(
            investigation_id
        )

        assert snapshot["investigation_id"] == investigation_id
        assert snapshot["active_tasks"] == 0
        assert snapshot["queued_tasks"] == 0
        assert snapshot["completed_tasks"] == 0
        assert snapshot["failed_tasks"] == 1
        assert snapshot["last_agent"] == "reasoner"

    finally:
        manager.shutdown()

def test_distributed_state_tracks_repeated_executions():

    from app.agent.execution_manager import AgentExecutionManager

    manager = AgentExecutionManager(
        max_workers=2,
        max_per_investigation=2,
        max_queue_size=20,
    )

    investigation_id = 7003

    try:
        first_result = manager.run(
            investigation_id=investigation_id,
            agent_name="investigator",
            fn=lambda: "first",
        )

        second_result = manager.run(
            investigation_id=investigation_id,
            agent_name="reasoner",
            fn=lambda: "second",
        )

        assert first_result == "first"
        assert second_result == "second"

        snapshot = manager.distributed_state.snapshot(
            investigation_id
        )

        assert snapshot["investigation_id"] == investigation_id
        assert snapshot["active_tasks"] == 0
        assert snapshot["queued_tasks"] == 0

        assert snapshot["completed_tasks"] == 2
        assert snapshot["failed_tasks"] == 0

        # The latest execution should be reflected.
        assert snapshot["last_agent"] == "reasoner"

    finally:
        manager.shutdown()

def test_shutdown_prevents_new_execution():

    import pytest

    from app.agent.execution_manager import (
        AgentExecutionError,
        AgentExecutionManager,
    )

    manager = AgentExecutionManager(
        max_workers=2,
        max_per_investigation=2,
        max_queue_size=20,
    )

    try:
        manager.shutdown()

        with pytest.raises(
            AgentExecutionError,
            match="AgentExecutionManager is closed",
        ):
            manager.run(
                investigation_id=8001,
                agent_name="investigator",
                fn=lambda: "should-not-run",
            )

    finally:
        manager.shutdown()


def test_shutdown_is_idempotent():

    from app.agent.execution_manager import AgentExecutionManager

    manager = AgentExecutionManager(
        max_workers=2,
        max_per_investigation=2,
        max_queue_size=20,
    )

    manager.shutdown()

    # A second shutdown must be harmless.
    manager.shutdown()


def test_shutdown_waits_for_active_execution():

    import threading
    import time

    from app.agent.execution_manager import AgentExecutionManager

    manager = AgentExecutionManager(
        max_workers=2,
        max_per_investigation=2,
        max_queue_size=20,
    )

    started = threading.Event()
    release = threading.Event()

    def long_running_agent():
        started.set()

        assert release.wait(timeout=10)

        return "completed"

    result_holder = {}

    def execute():
        result_holder["result"] = manager.run(
            investigation_id=8002,
            agent_name="investigator",
            fn=long_running_agent,
        )

    worker = threading.Thread(target=execute)

    try:
        worker.start()

        assert started.wait(timeout=10)

        release.set()

        manager.shutdown(wait=True)

        worker.join(timeout=10)

        assert not worker.is_alive()
        assert result_holder["result"] == "completed"

    finally:
        release.set()
        manager.shutdown()
        worker.join(timeout=10)

def test_shutdown_cancels_queued_execution():

    import threading

    from app.agent.execution_manager import AgentExecutionManager

    manager = AgentExecutionManager(
        max_workers=2,
        max_per_investigation=2,
        max_queue_size=20,
    )

    started_count = 0
    started_lock = threading.Lock()
    both_started = threading.Event()
    release = threading.Event()

    results = {}

    def blocking_agent(name):
        nonlocal started_count

        with started_lock:
            started_count += 1

            if started_count == 2:
                both_started.set()

        assert release.wait(timeout=10)

        results[name] = "completed"

        return f"{name}-completed"

    def queued_agent():
        results["queued"] = "executed"

        return "queued-completed"

    try:
        running_future_1 = manager._executor.submit(
            blocking_agent,
            "running-1",
        )

        running_future_2 = manager._executor.submit(
            blocking_agent,
            "running-2",
        )

        assert both_started.wait(timeout=10)

        queued_future = manager._executor.submit(
            queued_agent
        )

        manager.shutdown(
            wait=False,
            cancel_futures=True,
        )

        release.set()

        assert running_future_1.result(
            timeout=10
        ) == "running-1-completed"

        assert running_future_2.result(
            timeout=10
        ) == "running-2-completed"

        assert queued_future.cancelled()

        assert "queued" not in results

    finally:
        release.set()
        manager.shutdown()

def test_context_manager_shuts_down_execution_manager():

    import pytest

    from app.agent.execution_manager import (
        AgentExecutionError,
        AgentExecutionManager,
    )

    with AgentExecutionManager(
        max_workers=2,
        max_per_investigation=2,
        max_queue_size=20,
    ) as manager:

        result = manager.run(
            investigation_id=8003,
            agent_name="investigator",
            fn=lambda: "completed",
        )

        assert result == "completed"

    with pytest.raises(
        AgentExecutionError,
        match="AgentExecutionManager is closed",
    ):
        manager.run(
            investigation_id=8003,
            agent_name="investigator",
            fn=lambda: "should-not-run",
        )
