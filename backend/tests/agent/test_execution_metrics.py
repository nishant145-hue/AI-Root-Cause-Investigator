from __future__ import annotations

import pytest

from app.agent.execution_manager import (
    AgentExecutionManager,
)


def test_successful_execution_records_metrics():
    manager = AgentExecutionManager(
        max_workers=2,
        max_per_investigation=2,
    )

    try:
        result = manager.run(
            investigation_id=1,
            agent_name="investigator",
            fn=lambda: "success",
        )

        assert result == "success"

        snapshot = (
            manager.execution_metrics_snapshot()
        )

        assert snapshot[
            "total_executions"
        ] == 1

        assert snapshot[
            "successful_executions"
        ] == 1

        assert snapshot[
            "failed_executions"
        ] == 0

        assert snapshot[
            "cancelled_executions"
        ] == 0

        assert snapshot[
            "total_duration_ms"
        ] >= 0

        assert snapshot[
            "average_duration_ms"
        ] >= 0

        agent_stats = snapshot[
            "agent_statistics"
        ]["investigator"]

        assert agent_stats[
            "execution_count"
        ] == 1

        assert agent_stats[
            "success_count"
        ] == 1

        assert agent_stats[
            "failure_count"
        ] == 0

        assert agent_stats[
            "cancelled_count"
        ] == 0

    finally:
        manager.shutdown()


def test_failed_execution_records_metrics():
    manager = AgentExecutionManager(
        max_workers=2,
        max_per_investigation=2,
    )

    def failing_agent():
        raise RuntimeError(
            "agent failure"
        )

    try:
        with pytest.raises(
            RuntimeError,
            match="agent failure",
        ):
            manager.run(
                investigation_id=2,
                agent_name="reasoner",
                fn=failing_agent,
            )

        snapshot = (
            manager.execution_metrics_snapshot()
        )

        assert snapshot[
            "total_executions"
        ] == 1

        assert snapshot[
            "successful_executions"
        ] == 0

        assert snapshot[
            "failed_executions"
        ] == 1

        assert snapshot[
            "cancelled_executions"
        ] == 0

        agent_stats = snapshot[
            "agent_statistics"
        ]["reasoner"]

        assert agent_stats[
            "execution_count"
        ] == 1

        assert agent_stats[
            "success_count"
        ] == 0

        assert agent_stats[
            "failure_count"
        ] == 1

        assert agent_stats[
            "cancelled_count"
        ] == 0

    finally:
        manager.shutdown()


def test_multiple_agents_are_aggregated():
    manager = AgentExecutionManager(
        max_workers=3,
        max_per_investigation=3,
    )

    try:
        manager.run(
            investigation_id=10,
            agent_name="investigator",
            fn=lambda: 1,
        )

        manager.run(
            investigation_id=10,
            agent_name="investigator",
            fn=lambda: 2,
        )

        manager.run(
            investigation_id=10,
            agent_name="reasoner",
            fn=lambda: 3,
        )

        snapshot = (
            manager.execution_metrics_snapshot()
        )

        assert snapshot[
            "total_executions"
        ] == 3

        assert snapshot[
            "successful_executions"
        ] == 3

        assert snapshot[
            "failed_executions"
        ] == 0

        assert (
            snapshot[
                "agent_statistics"
            ][
                "investigator"
            ][
                "execution_count"
            ]
            == 2
        )

        assert (
            snapshot[
                "agent_statistics"
            ][
                "investigator"
            ][
                "success_count"
            ]
            == 2
        )

        assert (
            snapshot[
                "agent_statistics"
            ][
                "reasoner"
            ][
                "execution_count"
            ]
            == 1
        )

        assert (
            snapshot[
                "agent_statistics"
            ][
                "reasoner"
            ][
                "success_count"
            ]
            == 1
        )

    finally:
        manager.shutdown()


def test_execution_metrics_history_contains_execution_identity():
    manager = AgentExecutionManager(
        max_workers=2,
        max_per_investigation=2,
    )

    try:
        execution, future = manager.submit(
            investigation_id=42,
            agent_name="validator",
            fn=lambda: "ok",
        )

        assert future.result(
            timeout=3
        ) == "ok"

        history = (
            manager.execution_metrics_history()
        )

        assert len(history) == 1

        metric = history[0]

        assert metric[
            "execution_id"
        ] == execution.execution_id

        assert metric[
            "investigation_id"
        ] == 42

        assert metric[
            "agent_name"
        ] == "validator"

        assert metric[
            "status"
        ] == "COMPLETED"

        assert metric[
            "duration_ms"
        ] >= 0

        assert metric[
            "started_at"
        ] > 0

        assert metric[
            "completed_at"
        ] > 0

    finally:
        manager.shutdown()


def test_reset_execution_metrics():
    manager = AgentExecutionManager(
        max_workers=2,
        max_per_investigation=2,
    )

    try:
        manager.run(
            investigation_id=99,
            agent_name="memory",
            fn=lambda: "ok",
        )

        snapshot_before = (
            manager.execution_metrics_snapshot()
        )

        assert snapshot_before[
            "total_executions"
        ] == 1

        assert snapshot_before[
            "successful_executions"
        ] == 1

        assert (
            "memory"
            in snapshot_before[
                "agent_statistics"
            ]
        )

        manager.reset_execution_metrics()

        snapshot_after = (
            manager.execution_metrics_snapshot()
        )

        assert snapshot_after[
            "total_executions"
        ] == 0

        assert snapshot_after[
            "successful_executions"
        ] == 0

        assert snapshot_after[
            "failed_executions"
        ] == 0

        assert snapshot_after[
            "cancelled_executions"
        ] == 0

        assert snapshot_after[
            "total_duration_ms"
        ] == 0.0

        assert snapshot_after[
            "average_duration_ms"
        ] == 0.0

        assert snapshot_after[
            "agent_statistics"
        ] == {}

    finally:
        manager.shutdown()

def test_execution_contains_trace_context():
    manager = AgentExecutionManager(
        max_workers=2,
        max_per_investigation=2,
    )

    try:
        execution, future = manager.submit(
            investigation_id=100,
            agent_name="investigator",
            fn=lambda: "ok",
        )

        assert (
            future.result(timeout=3)
            == "ok"
        )

        assert execution.trace_id
        assert execution.span_id

        assert execution.parent_span_id

    finally:
        manager.shutdown()


def test_execution_metrics_contain_trace_context():
    manager = AgentExecutionManager(
        max_workers=2,
        max_per_investigation=2,
    )

    try:
        execution, future = manager.submit(
            investigation_id=101,
            agent_name="reasoner",
            fn=lambda: "ok",
        )

        assert (
            future.result(timeout=3)
            == "ok"
        )

        history = (
            manager.execution_metrics_history()
        )

        assert len(history) == 1

        metric = history[0]

        assert (
            metric["execution_id"]
            == execution.execution_id
        )

        assert (
            metric["trace_id"]
            == execution.trace_id
        )

        assert (
            metric["span_id"]
            == execution.span_id
        )

        assert (
            metric["parent_span_id"]
            == execution.parent_span_id
        )

    finally:
        manager.shutdown()
