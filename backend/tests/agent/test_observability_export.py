from app.agent.execution_manager import (
    AgentExecutionManager,
)


def test_observability_export_contains_version():

    manager = AgentExecutionManager(
        max_workers=2,
        max_per_investigation=2,
    )

    try:

        snapshot = (
            manager.observability_snapshot()
        )

        assert snapshot["version"] == "1.0"

        assert "resource" in snapshot

        assert "failures" in snapshot

    finally:

        manager.shutdown()

def test_observability_export_contains_investigation():

    manager = AgentExecutionManager(
        max_workers=2,
        max_per_investigation=2,
    )

    try:

        execution, future = manager.submit(
            investigation_id=500,
            agent_name="investigator",
            fn=lambda: "ok",
        )

        assert future.result(
            timeout=3
        ) == "ok"

        snapshot = (
            manager.observability_snapshot(
                investigation_id=500
            )
        )

        assert (
            snapshot["investigation"]
            ["investigation_id"]
            == 500
        )

        assert (
            snapshot["investigation"]
            ["trace"]
            ["trace_id"]
        )

        assert len(
            snapshot["investigation"]
            ["timeline"]
        ) == 1

    finally:

        manager.shutdown()
