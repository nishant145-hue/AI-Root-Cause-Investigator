from app.agent.execution_manager import AgentExecutionManager


def test_successful_execution_emits_one_terminal_log(monkeypatch):
    events = []

    def fake_log_agent_event(
        event,
        *args,
        **kwargs,
    ):
        events.append(event)

    monkeypatch.setattr(
        "app.agent.execution_manager.log_agent_event",
        fake_log_agent_event,
    )

    manager = AgentExecutionManager(
        max_workers=1,
        max_per_investigation=1,
    )

    try:
        execution, future = manager.submit(
            investigation_id=9001,
            agent_name="investigator",
            fn=lambda: "ok",
        )

        assert future.result(timeout=3) == "ok"

        terminal_events = [
            event
            for event in events
            if event
            in {
                "agent_execution_completed",
                "agent_execution_failed",
                "agent_execution_cancelled",
            }
        ]

        assert terminal_events == [
            "agent_execution_completed"
        ]

    finally:
        manager.shutdown()


def test_failed_execution_emits_one_terminal_log(monkeypatch):
    events = []

    def fake_log_agent_event(
        event,
        *args,
        **kwargs,
    ):
        events.append(event)

    monkeypatch.setattr(
        "app.agent.execution_manager.log_agent_event",
        fake_log_agent_event,
    )

    manager = AgentExecutionManager(
        max_workers=1,
        max_per_investigation=1,
    )

    def failing_agent():
        raise RuntimeError("boom")

    try:
        execution, future = manager.submit(
            investigation_id=9002,
            agent_name="investigator",
            fn=failing_agent,
        )

        try:
            future.result(timeout=3)
        except RuntimeError:
            pass

        terminal_events = [
            event
            for event in events
            if event
            in {
                "agent_execution_completed",
                "agent_execution_failed",
                "agent_execution_cancelled",
            }
        ]

        assert terminal_events == [
            "agent_execution_failed"
        ]

    finally:
        manager.shutdown()
