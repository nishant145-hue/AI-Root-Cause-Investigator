from fastapi.testclient import TestClient

from app.models.notification import Notification
from app.models.user import User
from app.notifications.enums import (
    NotificationProvider,
    NotificationSeverity,
)


def create_notification(
    client: TestClient,
    auth_headers: dict,
    subject: str = "Delete Test",
):
    response = client.post(
        "/api/v1/notifications",
        headers=auth_headers,
        json={
            "provider": "email",
            "severity": "info",
            "subject": subject,
            "message": "Notification for delete testing",
        },
    )

    assert response.status_code == 201

    return response.json()


def test_delete_own_notification(
    client: TestClient,
    auth_headers: dict,
):
    notification = create_notification(
        client,
        auth_headers,
        "Delete Own Notification",
    )

    notification_id = notification["id"]

    response = client.delete(
        f"/api/v1/notifications/{notification_id}",
        headers=auth_headers,
    )

    assert response.status_code == 204
    assert response.content == b""

    response = client.get(
        f"/api/v1/notifications/{notification_id}",
        headers=auth_headers,
    )

    assert response.status_code == 404


def test_delete_nonexistent_notification(
    client: TestClient,
    auth_headers: dict,
):
    response = client.delete(
        "/api/v1/notifications/999999999",
        headers=auth_headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Notification not found."


def test_delete_already_deleted_notification(
    client: TestClient,
    auth_headers: dict,
):
    notification = create_notification(
        client,
        auth_headers,
        "Already Deleted",
    )

    notification_id = notification["id"]

    first = client.delete(
        f"/api/v1/notifications/{notification_id}",
        headers=auth_headers,
    )

    assert first.status_code == 204

    second = client.delete(
        f"/api/v1/notifications/{notification_id}",
        headers=auth_headers,
    )

    assert second.status_code == 404


def test_delete_archived_notification(
    client: TestClient,
    auth_headers: dict,
):
    notification = create_notification(
        client,
        auth_headers,
        "Delete Archived",
    )

    notification_id = notification["id"]

    archive_response = client.patch(
        f"/api/v1/notifications/{notification_id}/archive",
        headers=auth_headers,
    )

    assert archive_response.status_code == 200
    assert archive_response.json()["is_archived"] is True

    delete_response = client.delete(
        f"/api/v1/notifications/{notification_id}",
        headers=auth_headers,
    )

    assert delete_response.status_code == 204

    get_response = client.get(
        f"/api/v1/notifications/{notification_id}",
        headers=auth_headers,
    )

    assert get_response.status_code == 404


def test_cannot_delete_another_users_notification(
    client: TestClient,
    auth_headers: dict,
    db_session,
):
    import uuid

    unique_id = uuid.uuid4().hex[:12]

    other_user = User(
        username=f"delete_other_{unique_id}",
        email=f"delete_other_{unique_id}@example.com",
        full_name="Other Delete User",
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
        subject="Private Delete Test",
        message="Should not be deleted",
    )

    db_session.add(notification)
    db_session.commit()
    db_session.refresh(notification)

    notification_id = notification.id

    response = client.delete(
        f"/api/v1/notifications/{notification_id}",
        headers=auth_headers,
    )

    assert response.status_code == 404

    db_session.refresh(notification)

    assert notification.id == notification_id
    assert notification.user_id == other_user.id


def test_delete_does_not_delete_another_users_notification(
    client: TestClient,
    auth_headers: dict,
    db_session,
):
    import uuid

    unique_id = uuid.uuid4().hex[:12]

    other_user = User(
        username=f"delete_protect_{unique_id}",
        email=f"delete_protect_{unique_id}@example.com",
        full_name="Protected User",
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
        severity=NotificationSeverity.WARNING,
        subject="Protected Notification",
        message="Must remain in database",
    )

    db_session.add(notification)
    db_session.commit()
    db_session.refresh(notification)

    notification_id = notification.id

    response = client.delete(
        f"/api/v1/notifications/{notification_id}",
        headers=auth_headers,
    )

    assert response.status_code == 404

    database_notification = db_session.get(
        Notification,
        notification_id,
    )

    assert database_notification is not None
    assert database_notification.user_id == other_user.id