from unittest.mock import MagicMock, patch

from app.services.investigation_service import InvestigationService
from app.services.llm.schemas import AIInvestigationResponse


def test_investigation_service_uses_execution_manager_and_persists_result(
    db_session,
):
    repository = MagicMock()
    history_service = MagicMock()

    service = InvestigationService(
        repository=repository,
        history_service=history_service,
        db=db_session,
    )

    investigation = MagicMock()
    investigation.id = 101
    investigation.user_id = 202
    investigation.title = "Database outage"
    investigation.description = "Database connections are timing out"
    investigation.failed_component = None
    investigation.severity = None

    ai_result = AIInvestigationResponse(
        summary="Database investigation completed.",
        root_cause="Connection pool exhausted",
        failed_component="Database",
        severity="Critical",
        confidence=0.95,
        evidence=[],
        recommendations=[],
        additional_notes="Investigation completed successfully.",
    )

    execution_analytics = {
        "total_agents": 5,
        "successful_agents": 5,
        "failed_agents": 0,
    }

    manager = MagicMock()

    def manager_run(*, investigation_id, agent_name, fn, **kwargs):
        assert investigation_id == 101
        assert agent_name == "langgraph_investigation"
        assert callable(fn)

        # Execute the actual closure created by InvestigationService.
        runtime_result = fn()

        assert runtime_result == (ai_result, execution_analytics)

        return runtime_result

    manager.run.side_effect = manager_run

    with (
        patch(
            "app.services.investigation_service.get_execution_manager",
            return_value=manager,
        ),
        patch(
            "app.services.investigation_service.run_langgraph_investigation",
            return_value=(ai_result, execution_analytics),
        ),
    ):
        result = service._run_ai_investigation(
            investigation=investigation,
            log_file_id=303,
            user_id=202,
        )

    assert result == (ai_result, execution_analytics)

    manager.run.assert_called_once()

    call_kwargs = manager.run.call_args.kwargs

    assert call_kwargs["investigation_id"] == 101
    assert call_kwargs["agent_name"] == "langgraph_investigation"
    assert callable(call_kwargs["fn"])
