from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.exceptions.ai_exceptions import AIError
from app.models.investigation import Investigation, InvestigationStatus
from app.services.investigation_service import InvestigationService
from app.services.llm.schemas import AIInvestigationResponse


@pytest.fixture
def repository():
    return MagicMock()


@pytest.fixture
def history_service():
    return MagicMock()


@pytest.fixture
def db():
    return MagicMock()


@pytest.fixture
def service(repository, history_service, db):
    return InvestigationService(
        repository=repository,
        history_service=history_service,
        db=db,
    )


@pytest.fixture
def investigation():
    return Investigation(
        id=1,
        title="Database Failure",
        description="Testing AI",
        status=InvestigationStatus.OPEN,
        user_id=2,
    )


@pytest.fixture
def ai_result():
    return AIInvestigationResponse(
        summary="Summary",
        root_cause="Connection pool exhausted",
        failed_component="Database",
        severity="Critical",
        confidence=0.95,
        evidence=[],
        recommendations=[],
        additional_notes="Increase pool size.",
    )


def test_run_ai_success(
    service,
    repository,
    history_service,
    investigation,
    ai_result,
):
    service.get_by_id = MagicMock(
        return_value=investigation
    )

    service._run_ai_investigation = MagicMock(
        return_value=ai_result
    )

    repository.update.return_value = investigation

    result = service.run_ai_investigation(
        investigation_id=1,
        log_file_id=10,
        user_id=2,
    )

    assert result.status == InvestigationStatus.COMPLETED
    assert result.summary == "Summary"
    assert result.root_cause == "Connection pool exhausted"

    assert history_service.create.call_count == 2

    repository.update.assert_called_once()


def test_investigation_not_found(service):

    service.get_by_id = MagicMock(
        side_effect=HTTPException(
            status_code=404,
            detail="Investigation not found",
        )
    )

    with pytest.raises(HTTPException):
        service.run_ai_investigation(
            investigation_id=1,
            log_file_id=10,
            user_id=2,
        )


def test_ai_error_marks_failed(
    service,
    history_service,
    investigation,
):
    service.get_by_id = MagicMock(
        return_value=investigation
    )

    service._run_ai_investigation = MagicMock(
        side_effect=AIError("Groq unavailable")
    )

    service._mark_investigation_failed = MagicMock()

    with pytest.raises(HTTPException):
        service.run_ai_investigation(
            investigation_id=1,
            log_file_id=10,
            user_id=2,
        )

    service._mark_investigation_failed.assert_called_once()

    assert history_service.create.call_count == 2


def test_unexpected_exception_marks_failed(
    service,
    history_service,
    investigation,
):
    service.get_by_id = MagicMock(
        return_value=investigation
    )

    service._run_ai_investigation = MagicMock(
        side_effect=Exception("Unexpected Error")
    )

    service._mark_investigation_failed = MagicMock()

    with pytest.raises(HTTPException):
        service.run_ai_investigation(
            investigation_id=1,
            log_file_id=10,
            user_id=2,
        )

    service._mark_investigation_failed.assert_called_once()

    assert history_service.create.call_count == 2


def test_mark_investigation_failed(
    service,
    repository,
    investigation,
):
    repository.update.return_value = investigation

    result = service._mark_investigation_failed(
        investigation
    )

    assert result.status == InvestigationStatus.FAILED

    repository.update.assert_called_once()


def test_save_ai_results(
    service,
    repository,
    investigation,
    ai_result,
):
    repository.update.return_value = investigation

    result = service._save_ai_results(
        investigation,
        ai_result,
    )

    assert result.summary == "Summary"
    assert result.root_cause == "Connection pool exhausted"
    assert result.failed_component == "Database"
    assert result.severity == "Critical"
    assert result.confidence == 0.95
    assert result.additional_notes == "Increase pool size."

    assert result.status == InvestigationStatus.COMPLETED

    repository.update.assert_called_once()