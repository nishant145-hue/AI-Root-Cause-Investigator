from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.models.notification import Notification
from app.models.user import User
from app.notifications.enums import (
    NotificationProvider,
    NotificationSeverity,
    NotificationStatus,
)


def test_notification_requires_authentication(client):
    response = client.get("/api/v1/notifications")

    assert response.status_code == 401


def test_get_notification_preferences(
    client,
    auth_headers,
):
    # Reset preferences so this test is independent
    # of data left by previous test runs.
    update_response = client.put(
        "/api/v1/notifications/preferences",
        headers=auth_headers,
        json={
            "email_enabled": True,
            "slack_enabled": False,
            "teams_enabled": False,
            "critical_only": False,
            "daily_digest": False,
            "weekly_digest": False,
        },
    )

    assert update_response.status_code == 200

    response = client.get(
        "/api/v1/notifications/preferences",
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["email_enabled"] is True
    assert data["slack_enabled"] is False
    assert data["teams_enabled"] is False
    assert data["critical_only"] is False
    assert data["daily_digest"] is False
    assert data["weekly_digest"] is False


def test_update_notification_preferences(
    client,
    auth_headers,
):
    response = client.put(
        "/api/v1/notifications/preferences",
        headers=auth_headers,
        json={
            "email_enabled": True,
            "slack_enabled": True,
            "teams_enabled": False,
            "critical_only": True,
            "daily_digest": True,
            "weekly_digest": False,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["email_enabled"] is True
    assert data["slack_enabled"] is True
    assert data["critical_only"] is True
    assert data["daily_digest"] is True


def test_list_notifications(
    client,
    auth_headers,
):
    response = client.get(
        "/api/v1/notifications",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_notification(
    client,
    auth_headers,
):
    mock_provider = MagicMock()
    mock_provider.send = AsyncMock(return_value=True)

    mock_manager = MagicMock()
    mock_manager.get_provider.return_value = mock_provider

    with patch(
        "app.api.v1.routes.notifications.create_notification_manager",
        return_value=mock_manager,
    ):
        response = client.post(
            "/api/v1/notifications",
            headers=auth_headers,
            json={
                "provider": "email",
                "severity": "critical",
                "subject": "Database failure",
                "message": "Production database is unavailable.",
                "metadata_json": {
                    "source": "integration-test",
                },
            },
        )

    assert response.status_code == 201

    data = response.json()

    assert data["provider"] == "email"
    assert data["severity"] == "critical"
    assert data["status"] == "sent"
    assert data["subject"] == "Database failure"


def test_notification_cannot_be_created_for_another_user(
    client,
    auth_headers,
):
    mock_provider = MagicMock()
    mock_provider.send = AsyncMock(return_value=True)

    mock_manager = MagicMock()
    mock_manager.get_provider.return_value = mock_provider

    with patch(
        "app.api.v1.routes.notifications.create_notification_manager",
        return_value=mock_manager,
    ):
        response = client.post(
            "/api/v1/notifications",
            headers=auth_headers,
            json={
                "user_id": 999999,
                "provider": "email",
                "severity": "critical",
                "subject": "Security test",
                "message": "This must belong to the authenticated user.",
            },
        )

    assert response.status_code == 201

    data = response.json()

    assert data["user_id"] != 999999


def test_notification_ownership_protection(
    client,
    auth_headers,
    db_session,
):
    user = db_session.exec(
        User.__table__.select().where(
            User.email == "pytest@example.com"
        )
    ).first()

    assert user is not None

    unique_id = uuid4().hex

    other_user = User(
        username=f"notification_other_user_{unique_id}",
        email=f"notification_other_{unique_id}@example.com",
        hashed_password="test-password",
        full_name="Other Notification User",
    )

    db_session.add(other_user)
    db_session.commit()
    db_session.refresh(other_user)

    notification = Notification(
        user_id=other_user.id,
        provider=NotificationProvider.EMAIL,
        severity=NotificationSeverity.CRITICAL,
        status=NotificationStatus.PENDING,
        subject="Private notification",
        message="This belongs to another user.",
        metadata_json={},
    )

    db_session.add(notification)
    db_session.commit()
    db_session.refresh(notification)

    response = client.get(
        f"/api/v1/notifications/{notification.id}",
        headers=auth_headers,
    )

    assert response.status_code == 404


def test_notification_not_found(
    client,
    auth_headers,
):
    response = client.get(
        "/api/v1/notifications/999999999",
        headers=auth_headers,
    )

    assert response.status_code == 404


def test_retry_limit_protection(
    client,
    auth_headers,
    db_session,
):
    user = db_session.exec(
        User.__table__.select().where(
            User.email == "pytest@example.com"
        )
    ).first()

    assert user is not None

    notification = Notification(
        user_id=user.id,
        provider=NotificationProvider.EMAIL,
        severity=NotificationSeverity.CRITICAL,
        status=NotificationStatus.FAILED,
        subject="Retry test",
        message="Retry limit test.",
        retry_count=3,
        metadata_json={},
    )

    db_session.add(notification)
    db_session.commit()
    db_session.refresh(notification)

    response = client.post(
        f"/api/v1/notifications/{notification.id}/retry",
        headers=auth_headers,
    )

    assert response.status_code == 400
    assert "retry limit" in response.json()["detail"].lower()