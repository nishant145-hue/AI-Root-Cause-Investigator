from app.agent.execution_manager import (
    AgentExecutionManager,
)


def test_investigation_trace_single_execution():

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

        assert future.result(
            timeout=3
        ) == "ok"

        trace = (
            manager.investigation_trace_snapshot(
                100
            )
        )

        assert trace[
            "investigation_id"
        ] == 100

        assert trace["trace_id"]

        assert len(
            trace["executions"]
        ) == 1

        assert (
            trace["executions"][0][
                "execution_id"
            ]
            == execution.execution_id
        )

    finally:

        manager.shutdown()

def test_investigation_timeline():

    manager = AgentExecutionManager(
        max_workers=2,
        max_per_investigation=2,
    )

    try:

        first, first_future = manager.submit(
            investigation_id=200,
            agent_name="investigator",
            fn=lambda: "first",
        )

        second, second_future = manager.submit(
            investigation_id=200,
            agent_name="reasoner",
            fn=lambda: "second",
        )

        assert first_future.result(
            timeout=3
        ) == "first"

        assert second_future.result(
            timeout=3
        ) == "second"

        timeline = (
            manager.investigation_timeline(
                200
            )
        )

        assert len(timeline) == 2

        assert all(
            item["investigation_id"]
            if "investigation_id" in item
            else True
            for item in timeline
        )

        assert {
            item["agent_name"]
            for item in timeline
        } == {
            "investigator",
            "reasoner",
        }

    finally:

        manager.shutdown()

def test_investigation_critical_path():

    manager = AgentExecutionManager(
        max_workers=3,
        max_per_investigation=3,
    )

    try:

        first, first_future = manager.submit(
            investigation_id=300,
            agent_name="investigator",
            fn=lambda: "first",
        )

        assert first_future.result(
            timeout=3
        ) == "first"

        second, second_future = manager.submit(
            investigation_id=300,
            agent_name="reasoner",
            fn=lambda: "second",
        )

        assert second_future.result(
            timeout=3
        ) == "second"

        result = (
            manager.investigation_critical_path(
                300
            )
        )

        assert (
            result["investigation_id"]
            == 300
        )

        assert (
            result["critical_path_ms"]
            >= 0
        )

        assert result["executions"]

    finally:

        manager.shutdown()
