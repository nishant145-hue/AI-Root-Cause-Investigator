from app.models.notification import Notification
from app.models.user import User
from app.notifications.enums import (
    NotificationProvider,
    NotificationSeverity,
)
from fastapi.testclient import TestClient


def test_archive_notification(
    client: TestClient,
    auth_headers: dict,
):
    response = client.post(
        "/api/v1/notifications",
        headers=auth_headers,
        json={
            "provider": "email",
            "severity": "info",
            "subject": "Archive Test",
            "message": "Notification to archive",
        },
    )

    assert response.status_code == 201

    notification_id = response.json()["id"]

    response = client.patch(
        f"/api/v1/notifications/{notification_id}/archive",
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == notification_id
    assert data["is_archived"] is True
    assert data["archived_at"] is not None


def test_unarchive_notification(
    client: TestClient,
    auth_headers: dict,
):
    response = client.post(
        "/api/v1/notifications",
        headers=auth_headers,
        json={
            "provider": "email",
            "severity": "info",
            "subject": "Unarchive Test",
            "message": "Notification to unarchive",
        },
    )

    assert response.status_code == 201

    notification_id = response.json()["id"]

    response = client.patch(
        f"/api/v1/notifications/{notification_id}/archive",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["is_archived"] is True

    response = client.patch(
        f"/api/v1/notifications/{notification_id}/unarchive",
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["is_archived"] is False
    assert data["archived_at"] is None


def test_archive_is_idempotent(
    client: TestClient,
    auth_headers: dict,
):
    response = client.post(
        "/api/v1/notifications",
        headers=auth_headers,
        json={
            "provider": "email",
            "severity": "info",
            "subject": "Idempotent Archive",
            "message": "Test",
        },
    )

    notification_id = response.json()["id"]

    first = client.patch(
        f"/api/v1/notifications/{notification_id}/archive",
        headers=auth_headers,
    )

    second = client.patch(
        f"/api/v1/notifications/{notification_id}/archive",
        headers=auth_headers,
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["is_archived"] is True


def test_unarchive_is_idempotent(
    client: TestClient,
    auth_headers: dict,
):
    response = client.post(
        "/api/v1/notifications",
        headers=auth_headers,
        json={
            "provider": "email",
            "severity": "info",
            "subject": "Idempotent Unarchive",
            "message": "Test",
        },
    )

    notification_id = response.json()["id"]

    first = client.patch(
        f"/api/v1/notifications/{notification_id}/unarchive",
        headers=auth_headers,
    )

    second = client.patch(
        f"/api/v1/notifications/{notification_id}/unarchive",
        headers=auth_headers,
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["is_archived"] is False
    assert second.json()["archived_at"] is None
    
def test_notification_archive_filter(
    client: TestClient,
    auth_headers: dict,
):
    response = client.post(
        "/api/v1/notifications",
        headers=auth_headers,
        json={
            "provider": "email",
            "severity": "info",
            "subject": "Filter Test",
            "message": "Test",
        },
    )

    assert response.status_code == 201

    notification_id = response.json()["id"]

    response = client.patch(
        f"/api/v1/notifications/{notification_id}/archive",
        headers=auth_headers,
    )

    assert response.status_code == 200

    archived = client.get(
        "/api/v1/notifications?is_archived=true",
        headers=auth_headers,
    )

    assert archived.status_code == 200

    ids = [item["id"] for item in archived.json()]

    assert notification_id in ids

    active = client.get(
        "/api/v1/notifications?is_archived=false",
        headers=auth_headers,
    )

    assert active.status_code == 200

    active_ids = [item["id"] for item in active.json()]

    assert notification_id not in active_ids
    
def test_cannot_archive_another_users_notification(
    client: TestClient,
    auth_headers: dict,
    db_session,
):
    import uuid

    unique_id = uuid.uuid4().hex[:12]

    other_user = User(
        username=f"archive_other_{unique_id}",
        email=f"archive_other_{unique_id}@example.com",
        full_name="Other User",
        hashed_password="hashed",
        role="user",
        is_active=True,
        is_verified=True,
    )

    db_session.add(other_user)
    db_session.commit()
    db_session.refresh(other_user)

    notification = Notification(
        user_id=other_user.id,
        provider=NotificationProvider.EMAIL,
        severity=NotificationSeverity.INFO,
        subject="Private Notification",
        message="Should not be accessible",
    )

    db_session.add(notification)
    db_session.commit()
    db_session.refresh(notification)

    response = client.patch(
        f"/api/v1/notifications/{notification.id}/archive",
        headers=auth_headers,
    )

    assert response.status_code == 404

    db_session.refresh(notification)

    assert notification.is_archived is False
    assert notification.archived_at is None
    
def test_archive_all_notifications(
    client: TestClient,
    auth_headers: dict,
):
    for index in range(3):
        response = client.post(
            "/api/v1/notifications",
            headers=auth_headers,
            json={
                "provider": "email",
                "severity": "info",
                "subject": f"Archive All {index}",
                "message": "Test",
            },
        )

        assert response.status_code == 201

    response = client.patch(
        "/api/v1/notifications/archive-all",
        headers=auth_headers,
    )

    assert response.status_code == 200

    # The exact number may include notifications created by
    # previous tests, so verify the endpoint succeeded.
    assert isinstance(response.json(), int)

    archived = client.get(
        "/api/v1/notifications?is_archived=true",
        headers=auth_headers,
    )

    assert archived.status_code == 200
    assert all(
        notification["is_archived"] is True
        for notification in archived.json()
    )


def test_archive_all_is_idempotent(
    client: TestClient,
    auth_headers: dict,
):
    response = client.post(
        "/api/v1/notifications",
        headers=auth_headers,
        json={
            "provider": "email",
            "severity": "info",
            "subject": "Archive All Idempotency",
            "message": "Test",
        },
    )

    assert response.status_code == 201

    first = client.patch(
        "/api/v1/notifications/archive-all",
        headers=auth_headers,
    )

    assert first.status_code == 200

    second = client.patch(
        "/api/v1/notifications/archive-all",
        headers=auth_headers,
    )

    assert second.status_code == 200

    # The second call should have nothing new to archive.
    assert second.json() == 0