from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.api.v1 import investigation as investigation_api
from app.models.investigation import (
    Investigation,
    InvestigationStatus,
)
from app.models.user import User
from app.notifications.enums import (
    NotificationProvider,
    NotificationSeverity,
)
from app.schemas.investigation import RunAIInvestigationRequest


@pytest.fixture
def test_user():
    return User(
        id=2,
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        hashed_password="hashed",
        role="user",
        is_active=True,
        is_verified=True,
    )


@pytest.fixture
def completed_investigation():
    return Investigation(
        id=1,
        title="Database Failure",
        description="Database investigation",
        status=InvestigationStatus.COMPLETED,
        user_id=2,
        summary="Database connection failure",
        root_cause="Connection pool exhausted",
        failed_component="Database",
        severity="Critical",
        confidence=0.95,
        additional_notes="Increase pool size.",
    )


@pytest.fixture
def failed_investigation():
    return Investigation(
        id=1,
        title="Database Failure",
        description="Database investigation",
        status=InvestigationStatus.FAILED,
        user_id=2,
    )


@pytest.fixture
def request_data():
    return RunAIInvestigationRequest(
        log_file_id=10,
    )


def test_completed_investigation_schedules_notification(
    test_user,
    completed_investigation,
    request_data,
):
    service = MagicMock()

    service.run_ai_investigation.return_value = (
        completed_investigation
    )

    notification = MagicMock()
    notification.id = 100

    with (
        patch.object(
            investigation_api,
            "NotificationService",
        ) as notification_service_class,
        patch.object(
            investigation_api,
            "create_notification_manager",
        ) as manager_factory,
        patch.object(
            investigation_api,
            "enqueue_notification_delivery",
        ) as enqueue,
    ):
        notification_service = (
            notification_service_class.return_value
        )

        notification_service.create_notification.return_value = (
            notification
        )

        result = investigation_api.run_ai_investigation(
            investigation_id=1,
            request=request_data,
            background_tasks=MagicMock(),
            current_user=test_user,
            service=service,
        )

    assert result.status == InvestigationStatus.COMPLETED

    notification_service.create_notification.assert_called_once()

    call_kwargs = (
        notification_service
        .create_notification
        .call_args.kwargs
    )

    assert call_kwargs["user_id"] == test_user.id
    assert call_kwargs["provider"] == NotificationProvider.EMAIL
    assert call_kwargs["severity"] == NotificationSeverity.INFO
    assert call_kwargs["subject"] == (
        "Investigation Completed: Database Failure"
    )

    assert call_kwargs["metadata"]["investigation_id"] == 1
    assert call_kwargs["metadata"]["status"] == "COMPLETED"
    assert call_kwargs["metadata"]["root_cause"] == (
        "Connection pool exhausted"
    )
    assert call_kwargs["metadata"]["failed_component"] == (
        "Database"
    )
    assert call_kwargs["metadata"]["severity"] == "Critical"
    assert call_kwargs["metadata"]["confidence"] == 0.95

    enqueue.assert_called_once()


def test_completed_notification_uses_user_email(
    test_user,
    completed_investigation,
    request_data,
):
    service = MagicMock()

    service.run_ai_investigation.return_value = (
        completed_investigation
    )

    notification = MagicMock()
    notification.id = 101

    with (
        patch.object(
            investigation_api,
            "NotificationService",
        ) as notification_service_class,
        patch.object(
            investigation_api,
            "create_notification_manager",
        ),
        patch.object(
            investigation_api,
            "enqueue_notification_delivery",
        ) as enqueue,
    ):
        notification_service_class.return_value \
            .create_notification.return_value = notification

        investigation_api.run_ai_investigation(
            investigation_id=1,
            request=request_data,
            background_tasks=MagicMock(),
            current_user=test_user,
            service=service,
        )

    args = enqueue.call_args.args

    assert args[1] == notification.id
    assert args[2] == test_user.email


def test_notification_failure_does_not_change_completed_investigation(
    test_user,
    completed_investigation,
    request_data,
):
    service = MagicMock()

    service.run_ai_investigation.return_value = (
        completed_investigation
    )

    with patch.object(
        investigation_api,
        "NotificationService",
        side_effect=Exception(
            "Notification database unavailable"
        ),
    ):
        result = investigation_api.run_ai_investigation(
            investigation_id=1,
            request=request_data,
            background_tasks=MagicMock(),
            current_user=test_user,
            service=service,
        )

    assert result.status == InvestigationStatus.COMPLETED


def test_investigation_service_called_with_correct_arguments(
    test_user,
    completed_investigation,
    request_data,
):
    service = MagicMock()

    service.run_ai_investigation.return_value = (
        completed_investigation
    )

    with (
        patch.object(
            investigation_api,
            "NotificationService",
        ),
        patch.object(
            investigation_api,
            "create_notification_manager",
        ),
        patch.object(
            investigation_api,
            "enqueue_notification_delivery",
        ),
    ):
        investigation_api.run_ai_investigation(
            investigation_id=1,
            request=request_data,
            background_tasks=MagicMock(),
            current_user=test_user,
            service=service,
        )

    service.run_ai_investigation.assert_called_once_with(
        investigation_id=1,
        log_file_id=10,
        user_id=2,
    )
    
def test_failed_investigation_schedules_error_notification(
    test_user,
    failed_investigation,
    request_data,
):
    service = MagicMock()

    service.run_ai_investigation.side_effect = HTTPException(
        status_code=502,
        detail="AI provider unavailable",
    )

    service.repository.get_by_id.return_value = (
        failed_investigation
    )

    notification = MagicMock()
    notification.id = 200

    with (
        patch.object(
            investigation_api,
            "NotificationService",
        ) as notification_service_class,
        patch.object(
            investigation_api,
            "create_notification_manager",
        ),
        patch.object(
            investigation_api,
            "enqueue_notification_delivery",
        ) as enqueue,
    ):
        notification_service_class.return_value \
            .create_notification.return_value = notification

        with pytest.raises(HTTPException) as exc_info:
            investigation_api.run_ai_investigation(
                investigation_id=1,
                request=request_data,
                background_tasks=MagicMock(),
                current_user=test_user,
                service=service,
            )

    assert exc_info.value.status_code == 502

    notification_service = (
        notification_service_class.return_value
    )

    notification_service.create_notification.assert_called_once()

    call_kwargs = (
        notification_service
        .create_notification
        .call_args.kwargs
    )

    assert call_kwargs["user_id"] == test_user.id
    assert call_kwargs["provider"] == NotificationProvider.EMAIL
    assert call_kwargs["severity"] == NotificationSeverity.ERROR

    assert call_kwargs["subject"] == (
        "Investigation Failed: Database Failure"
    )

    assert call_kwargs["metadata"]["investigation_id"] == 1
    assert call_kwargs["metadata"]["status"] == "FAILED"
    assert call_kwargs["metadata"]["error"] == (
        "AI provider unavailable"
    )

    assert (
        "AI provider unavailable"
        in call_kwargs["message"]
    )

    enqueue.assert_called_once()

    enqueue_args = enqueue.call_args.args

    assert enqueue_args[1] == notification.id
    assert enqueue_args[2] == test_user.email

def test_failed_investigation_notification_contains_failure_details(
    test_user,
    failed_investigation,
    request_data,
):
    service = MagicMock()

    service.run_ai_investigation.side_effect = HTTPException(
        status_code=502,
        detail="Groq API timeout",
    )

    service.repository.get_by_id.return_value = (
        failed_investigation
    )

    notification = MagicMock()
    notification.id = 201

    with (
        patch.object(
            investigation_api,
            "NotificationService",
        ) as notification_service_class,
        patch.object(
            investigation_api,
            "create_notification_manager",
        ),
        patch.object(
            investigation_api,
            "enqueue_notification_delivery",
        ),
    ):
        notification_service_class.return_value \
            .create_notification.return_value = notification

        with pytest.raises(HTTPException):
            investigation_api.run_ai_investigation(
                investigation_id=1,
                request=request_data,
                background_tasks=MagicMock(),
                current_user=test_user,
                service=service,
            )

    call_kwargs = (
        notification_service_class.return_value
        .create_notification
        .call_args.kwargs
    )

    assert call_kwargs["metadata"] == {
        "investigation_id": 1,
        "status": "FAILED",
        "error": "Groq API timeout",
    }

    assert "Groq API timeout" in call_kwargs["message"]


def test_failed_investigation_notification_failure_preserves_original_error(
    test_user,
    failed_investigation,
    request_data,
):
    service = MagicMock()

    service.run_ai_investigation.side_effect = HTTPException(
        status_code=502,
        detail="AI provider unavailable",
    )

    service.repository.get_by_id.return_value = (
        failed_investigation
    )

    with patch.object(
        investigation_api,
        "NotificationService",
        side_effect=Exception(
            "Notification service unavailable"
        ),
    ):
        with pytest.raises(HTTPException) as exc_info:
            investigation_api.run_ai_investigation(
                investigation_id=1,
                request=request_data,
                background_tasks=MagicMock(),
                current_user=test_user,
                service=service,
            )

    assert exc_info.value.status_code == 502
    assert exc_info.value.detail == (
        "AI provider unavailable"
    )