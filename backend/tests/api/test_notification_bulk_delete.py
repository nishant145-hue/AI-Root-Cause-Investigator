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
            "message": "Bulk delete test",
        },
    )

    assert response.status_code == 201

    return response.json()


def test_bulk_delete_notifications(
    client: TestClient,
    auth_headers: dict,
):
    first = create_notification(
        client,
        auth_headers,
        "Bulk Delete 1",
    )

    second = create_notification(
        client,
        auth_headers,
        "Bulk Delete 2",
    )

    ids = [
        first["id"],
        second["id"],
    ]

    response = client.request(
        "DELETE",
        "/api/v1/notifications/bulk",
        headers=auth_headers,
        json={
            "notification_ids": ids,
        },
    )

    assert response.status_code == 200
    assert response.json() == 2

    for notification_id in ids:
        response = client.get(
            f"/api/v1/notifications/{notification_id}",
            headers=auth_headers,
        )

        assert response.status_code == 404


def test_bulk_delete_is_idempotent(
    client: TestClient,
    auth_headers: dict,
):
    notification = create_notification(
        client,
        auth_headers,
        "Bulk Delete Idempotent",
    )

    notification_id = notification["id"]

    first = client.request(
        "DELETE",
        "/api/v1/notifications/bulk",
        headers=auth_headers,
        json={
            "notification_ids": [notification_id],
        },
    )

    assert first.status_code == 200
    assert first.json() == 1

    second = client.request(
        "DELETE",
        "/api/v1/notifications/bulk",
        headers=auth_headers,
        json={
            "notification_ids": [notification_id],
        },
    )

    assert second.status_code == 200
    assert second.json() == 0


def test_bulk_delete_nonexistent_ids(
    client: TestClient,
    auth_headers: dict,
):
    response = client.request(
        "DELETE",
        "/api/v1/notifications/bulk",
        headers=auth_headers,
        json={
            "notification_ids": [
                999999998,
                999999999,
            ],
        },
    )

    assert response.status_code == 200
    assert response.json() == 0


def test_bulk_delete_archived_notifications(
    client: TestClient,
    auth_headers: dict,
):
    notification = create_notification(
        client,
        auth_headers,
        "Bulk Delete Archived",
    )

    notification_id = notification["id"]

    archive_response = client.patch(
        f"/api/v1/notifications/{notification_id}/archive",
        headers=auth_headers,
    )

    assert archive_response.status_code == 200
    assert archive_response.json()["is_archived"] is True

    delete_response = client.request(
        "DELETE",
        "/api/v1/notifications/bulk",
        headers=auth_headers,
        json={
            "notification_ids": [notification_id],
        },
    )

    assert delete_response.status_code == 200
    assert delete_response.json() == 1

    get_response = client.get(
        f"/api/v1/notifications/{notification_id}",
        headers=auth_headers,
    )

    assert get_response.status_code == 404


def test_bulk_delete_cannot_delete_another_users_notification(
    client: TestClient,
    auth_headers: dict,
    db_session,
):
    import uuid

    unique_id = uuid.uuid4().hex[:12]

    other_user = User(
        username=f"bulk_delete_other_{unique_id}",
        email=f"bulk_delete_other_{unique_id}@example.com",
        full_name="Other Bulk Delete User",
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
        subject="Private Bulk Delete",
        message="Must not be deleted",
    )

    db_session.add(notification)
    db_session.commit()
    db_session.refresh(notification)

    notification_id = notification.id

    response = client.request(
        "DELETE",
        "/api/v1/notifications/bulk",
        headers=auth_headers,
        json={
            "notification_ids": [notification_id],
        },
    )

    assert response.status_code == 200
    assert response.json() == 0

    db_session.refresh(notification)

    assert notification.id == notification_id
    assert notification.user_id == other_user.id


def test_bulk_delete_mixed_ownership(
    client: TestClient,
    auth_headers: dict,
    db_session,
):
    import uuid

    own_notification = create_notification(
        client,
        auth_headers,
        "Own Bulk Delete",
    )

    unique_id = uuid.uuid4().hex[:12]

    other_user = User(
        username=f"bulk_mixed_{unique_id}",
        email=f"bulk_mixed_{unique_id}@example.com",
        full_name="Mixed Ownership User",
        hashed_password="hashed",
        role="user",
        is_active=True,
        is_verified=True,
    )

    db_session.add(other_user)
    db_session.commit()
    db_session.refresh(other_user)

    other_notification = Notification(
        user_id=other_user.id,
        provider=NotificationProvider.EMAIL,
        severity=NotificationSeverity.INFO,
        subject="Other User Notification",
        message="Must remain",
    )

    db_session.add(other_notification)
    db_session.commit()
    db_session.refresh(other_notification)

    response = client.request(
        "DELETE",
        "/api/v1/notifications/bulk",
        headers=auth_headers,
        json={
            "notification_ids": [
                own_notification["id"],
                other_notification.id,
            ],
        },
    )

    assert response.status_code == 200

    # Only the current user's notification should be deleted.
    assert response.json() == 1

    own_result = client.get(
        f"/api/v1/notifications/{own_notification['id']}",
        headers=auth_headers,
    )

    assert own_result.status_code == 404

    db_session.refresh(other_notification)

    assert other_notification.id is not None
    assert other_notification.user_id == other_user.id