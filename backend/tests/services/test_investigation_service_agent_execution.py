from unittest.mock import MagicMock, patch

from app.agent.langgraph_runtime import LangGraphInvestigationOutcome
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

    critical_path = {
        "investigation_id": 101,
        "critical_path_ms": 125.50,
        "executions": [
            "execution-root",
            "execution-child",
        ],
    }

    manager.investigation_critical_path.return_value = (
        critical_path
    )

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

    assert result[0] == ai_result

    assert result[1]["total_agents"] == 5
    assert result[1]["successful_agents"] == 5
    assert result[1]["failed_agents"] == 0
    assert result[1]["critical_path"] == critical_path

    manager.investigation_critical_path.assert_called_once_with(
        101
    )

    manager.run.assert_called_once()

    call_kwargs = manager.run.call_args.kwargs

    assert call_kwargs["investigation_id"] == 101
    assert call_kwargs["agent_name"] == "langgraph_investigation"
    assert callable(call_kwargs["fn"])

def test_investigation_service_persists_critical_path_analytics(
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
        "timeline": [],
        "total_agents": 5,
        "successful_agents": 5,
        "failed_agents": 0,
    }

    critical_path = {
        "investigation_id": 101,
        "critical_path_ms": 125.50,
        "executions": [
            "execution-root",
            "execution-child",
        ],
    }

    manager = MagicMock()

    manager.run.return_value = (
        ai_result,
        execution_analytics,
    )

    manager.investigation_critical_path.return_value = (
        critical_path
    )

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

    assert result[0] == ai_result

    assert result[1]["critical_path"] == (
        critical_path
    )

    assert result[1]["total_agents"] == 5

    manager.run.assert_called_once()

    manager.investigation_critical_path.assert_called_once_with(
        101
    )

def test_investigation_service_preserves_langgraph_outcome_analytics(
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

    execution_analytics = {
        "execution": {
            "total_executions": 11,
            "successful_executions": 7,
            "failed_executions": 0,
            "total_duration_ms": 13710.0,
            "retry_count": 2,
        },
        "timeline": [
            {
                "agent": "investigator",
                "action": "search_logs",
                "status": "COMPLETED",
                "duration_ms": 8.6,
            },
        ],
    }

    outcome = LangGraphInvestigationOutcome(
        status="VALIDATION_FAILED",
        result=None,
        execution_analytics=execution_analytics,
        summary="Investigation completed without a validated root cause.",
        root_cause=None,
        failed_component=None,
        severity=None,
        confidence=0.0,
        additional_notes="No root cause was validated.",
    )

    critical_path = {
        "investigation_id": 101,
        "critical_path_ms": 125.50,
        "executions": [
            "execution-root",
            "execution-child",
        ],
    }

    manager = MagicMock()
    manager.investigation_critical_path.return_value = (
        critical_path
    )

    def manager_run(*, investigation_id, agent_name, fn, **kwargs):
        assert investigation_id == 101
        assert agent_name == "langgraph_investigation"
        assert callable(fn)

        runtime_result = fn()

        assert runtime_result is outcome

        return runtime_result

    manager.run.side_effect = manager_run

    with (
        patch(
            "app.services.investigation_service.get_execution_manager",
            return_value=manager,
        ),
        patch(
            "app.services.investigation_service.run_langgraph_investigation",
            return_value=outcome,
        ),
    ):
        result = service._run_ai_investigation(
            investigation=investigation,
            log_file_id=303,
            user_id=202,
        )

    assert result[0] is outcome

    assert result[1]["execution"] == (
        execution_analytics["execution"]
    )

    assert result[1]["timeline"] == (
        execution_analytics["timeline"]
    )

    assert result[1]["critical_path"] == (
        critical_path
    )

    manager.run.assert_called_once()

    manager.investigation_critical_path.assert_called_once_with(
        101
    )