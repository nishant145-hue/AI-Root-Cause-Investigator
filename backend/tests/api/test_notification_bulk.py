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
    subject: str,
):
    response = client.post(
        "/api/v1/notifications",
        headers=auth_headers,
        json={
            "provider": "email",
            "severity": "info",
            "subject": subject,
            "message": "Bulk notification test",
        },
    )

    assert response.status_code == 201

    return response.json()


def test_bulk_archive_notifications(
    client: TestClient,
    auth_headers: dict,
):
    first = create_notification(
        client,
        auth_headers,
        "Bulk Archive 1",
    )

    second = create_notification(
        client,
        auth_headers,
        "Bulk Archive 2",
    )

    notification_ids = [
        first["id"],
        second["id"],
    ]

    response = client.patch(
        "/api/v1/notifications/bulk/archive",
        headers=auth_headers,
        json={
            "notification_ids": notification_ids,
        },
    )

    assert response.status_code == 200
    assert response.json() == 2

    for notification_id in notification_ids:
        response = client.get(
            f"/api/v1/notifications/{notification_id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert response.json()["is_archived"] is True
        assert response.json()["archived_at"] is not None


def test_bulk_archive_is_idempotent(
    client: TestClient,
    auth_headers: dict,
):
    notification = create_notification(
        client,
        auth_headers,
        "Bulk Archive Idempotent",
    )

    notification_id = notification["id"]

    first = client.patch(
        "/api/v1/notifications/bulk/archive",
        headers=auth_headers,
        json={
            "notification_ids": [notification_id],
        },
    )

    assert first.status_code == 200
    assert first.json() == 1

    second = client.patch(
        "/api/v1/notifications/bulk/archive",
        headers=auth_headers,
        json={
            "notification_ids": [notification_id],
        },
    )

    assert second.status_code == 200
    assert second.json() == 0


def test_bulk_archive_nonexistent_ids(
    client: TestClient,
    auth_headers: dict,
):
    response = client.patch(
        "/api/v1/notifications/bulk/archive",
        headers=auth_headers,
        json={
            "notification_ids": [999999998, 999999999],
        },
    )

    assert response.status_code == 200
    assert response.json() == 0


def test_bulk_archive_cannot_modify_another_users_notification(
    client: TestClient,
    auth_headers: dict,
    db_session,
):
    import uuid

    unique_id = uuid.uuid4().hex[:12]

    other_user = User(
        username=f"bulk_archive_other_{unique_id}",
        email=f"bulk_archive_other_{unique_id}@example.com",
        full_name="Other Bulk User",
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
        subject="Private Bulk Notification",
        message="Must not be archived",
    )

    db_session.add(notification)
    db_session.commit()
    db_session.refresh(notification)

    notification_id = notification.id

    response = client.patch(
        "/api/v1/notifications/bulk/archive",
        headers=auth_headers,
        json={
            "notification_ids": [notification_id],
        },
    )

    assert response.status_code == 200
    assert response.json() == 0

    db_session.refresh(notification)

    assert notification.is_archived is False
    assert notification.archived_at is None
    
def test_bulk_unarchive_notifications(
    client: TestClient,
    auth_headers: dict,
):
    first = create_notification(
        client,
        auth_headers,
        "Bulk Unarchive 1",
    )

    second = create_notification(
        client,
        auth_headers,
        "Bulk Unarchive 2",
    )

    notification_ids = [
        first["id"],
        second["id"],
    ]

    archive_response = client.patch(
        "/api/v1/notifications/bulk/archive",
        headers=auth_headers,
        json={
            "notification_ids": notification_ids,
        },
    )

    assert archive_response.status_code == 200
    assert archive_response.json() == 2

    response = client.patch(
        "/api/v1/notifications/bulk/unarchive",
        headers=auth_headers,
        json={
            "notification_ids": notification_ids,
        },
    )

    assert response.status_code == 200
    assert response.json() == 2

    for notification_id in notification_ids:
        response = client.get(
            f"/api/v1/notifications/{notification_id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert response.json()["is_archived"] is False
        assert response.json()["archived_at"] is None


def test_bulk_unarchive_is_idempotent(
    client: TestClient,
    auth_headers: dict,
):
    notification = create_notification(
        client,
        auth_headers,
        "Bulk Unarchive Idempotent",
    )

    notification_id = notification["id"]

    archive = client.patch(
        "/api/v1/notifications/bulk/archive",
        headers=auth_headers,
        json={
            "notification_ids": [notification_id],
        },
    )

    assert archive.status_code == 200
    assert archive.json() == 1

    first = client.patch(
        "/api/v1/notifications/bulk/unarchive",
        headers=auth_headers,
        json={
            "notification_ids": [notification_id],
        },
    )

    assert first.status_code == 200
    assert first.json() == 1

    second = client.patch(
        "/api/v1/notifications/bulk/unarchive",
        headers=auth_headers,
        json={
            "notification_ids": [notification_id],
        },
    )

    assert second.status_code == 200
    assert second.json() == 0
    
def test_bulk_mark_read(
    client: TestClient,
    auth_headers: dict,
):
    first = create_notification(
        client,
        auth_headers,
        "Bulk Read 1",
    )

    second = create_notification(
        client,
        auth_headers,
        "Bulk Read 2",
    )

    ids = [first["id"], second["id"]]

    response = client.patch(
        "/api/v1/notifications/bulk/read",
        headers=auth_headers,
        json={"notification_ids": ids},
    )

    assert response.status_code == 200
    assert response.json() == 2

    for notification_id in ids:
        response = client.get(
            f"/api/v1/notifications/{notification_id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert response.json()["is_read"] is True
        assert response.json()["read_at"] is not None


def test_bulk_mark_unread(
    client: TestClient,
    auth_headers: dict,
):
    notification = create_notification(
        client,
        auth_headers,
        "Bulk Unread",
    )

    notification_id = notification["id"]

    read_response = client.patch(
        "/api/v1/notifications/bulk/read",
        headers=auth_headers,
        json={"notification_ids": [notification_id]},
    )

    assert read_response.status_code == 200
    assert read_response.json() == 1

    unread_response = client.patch(
        "/api/v1/notifications/bulk/unread",
        headers=auth_headers,
        json={"notification_ids": [notification_id]},
    )

    assert unread_response.status_code == 200
    assert unread_response.json() == 1

    response = client.get(
        f"/api/v1/notifications/{notification_id}",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["is_read"] is False
    assert response.json()["read_at"] is None


def test_bulk_read_is_idempotent(
    client: TestClient,
    auth_headers: dict,
):
    notification = create_notification(
        client,
        auth_headers,
        "Bulk Read Idempotent",
    )

    notification_id = notification["id"]

    first = client.patch(
        "/api/v1/notifications/bulk/read",
        headers=auth_headers,
        json={"notification_ids": [notification_id]},
    )

    assert first.status_code == 200
    assert first.json() == 1

    second = client.patch(
        "/api/v1/notifications/bulk/read",
        headers=auth_headers,
        json={"notification_ids": [notification_id]},
    )

    assert second.status_code == 200
    assert second.json() == 0


def test_bulk_unread_is_idempotent(
    client: TestClient,
    auth_headers: dict,
):
    notification = create_notification(
        client,
        auth_headers,
        "Bulk Unread Idempotent",
    )

    notification_id = notification["id"]

    # First make the notification read.
    read_response = client.patch(
        "/api/v1/notifications/bulk/read",
        headers=auth_headers,
        json={"notification_ids": [notification_id]},
    )

    assert read_response.status_code == 200
    assert read_response.json() == 1

    # Now mark it unread.
    first = client.patch(
        "/api/v1/notifications/bulk/unread",
        headers=auth_headers,
        json={"notification_ids": [notification_id]},
    )

    assert first.status_code == 200
    assert first.json() == 1

    # Calling unread again should do nothing.
    second = client.patch(
        "/api/v1/notifications/bulk/unread",
        headers=auth_headers,
        json={"notification_ids": [notification_id]},
    )

    assert second.status_code == 200
    assert second.json() == 0