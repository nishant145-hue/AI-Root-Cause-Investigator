from unittest.mock import patch

from app.agent.execution_manager import AgentExecutionManager
from app.agent.langgraph_runtime import (
    run_langgraph_investigation,
)
from app.services.llm.schemas import AIInvestigationResponse


def test_execution_manager_runs_langgraph_runtime():
    manager = AgentExecutionManager(
        max_workers=2,
        max_per_investigation=1,
        max_queue_size=2,
    )

    ai_result = AIInvestigationResponse(
        summary="Database investigation completed.",
        root_cause="Connection pool exhausted",
        failed_component="Database",
        severity="Critical",
        confidence=0.95,
        evidence=[],
        recommendations=[],
        additional_notes=None,
    )

    analytics = {
        "total_agents": 5,
        "successful_agents": 5,
        "failed_agents": 0,
    }

    def fake_runtime(**kwargs):
        assert kwargs["user_id"] == 202
        assert kwargs["log_file_id"] == 303
        assert kwargs["incident_summary"] == "Database timeout"

        return ai_result, analytics

    try:
        result = manager.run(
            investigation_id=101,
            agent_name="langgraph_investigation",
            fn=fake_runtime,
            user_id=202,
            log_file_id=303,
            incident_summary="Database timeout",
        )

        assert result[0] == ai_result
        assert result[1] == analytics

    finally:
        manager.shutdown(wait=True)

def test_concurrent_investigations_are_isolated(monkeypatch):
    """
    Verify that concurrent investigations executed through the shared
    AgentExecutionManager do not leak state between investigations.
    """

    from concurrent.futures import ThreadPoolExecutor
    from app.agent.execution_manager_provider import get_execution_manager

    manager = get_execution_manager()

    results = {}

    def execute(investigation_id):
        def worker():
            return {
                "investigation_id": investigation_id,
                "observations": [
                    f"observation-{investigation_id}"
                ],
            }

        return manager.run(
            investigation_id=investigation_id,
            agent_name=f"test-agent-{investigation_id}",
            fn=worker,
        )

    investigation_ids = [1001, 1002, 1003, 1004]

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            investigation_id: executor.submit(
                execute,
                investigation_id,
            )
            for investigation_id in investigation_ids
        }

        for investigation_id, future in futures.items():
            results[investigation_id] = future.result()

    assert set(results) == set(investigation_ids)

    for investigation_id in investigation_ids:
        result = results[investigation_id]

        assert result["investigation_id"] == investigation_id
        assert result["observations"] == [
            f"observation-{investigation_id}"
        ]
