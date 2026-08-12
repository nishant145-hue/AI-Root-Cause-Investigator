from fastapi.testclient import TestClient


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
            "message": "Notification quality test",
        },
    )

    assert response.status_code == 201
    return response.json()


def test_notification_list_pagination(
    client: TestClient,
    auth_headers: dict,
):
    created_ids = []

    for index in range(3):
        notification = create_notification(
            client,
            auth_headers,
            f"Pagination Test {index}",
        )
        created_ids.append(notification["id"])

    response = client.get(
        "/api/v1/notifications?skip=0&limit=2",
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) <= 2


def test_notification_read_filter(
    client: TestClient,
    auth_headers: dict,
):
    notification = create_notification(
        client,
        auth_headers,
        "Read Filter Test",
    )

    notification_id = notification["id"]

    # Newly created notification should be unread.
    unread_response = client.get(
        "/api/v1/notifications?is_read=false",
        headers=auth_headers,
    )

    assert unread_response.status_code == 200

    unread_ids = [
        item["id"]
        for item in unread_response.json()
    ]

    assert notification_id in unread_ids

    # Mark it as read.
    read_response = client.patch(
        f"/api/v1/notifications/{notification_id}/read",
        headers=auth_headers,
    )

    assert read_response.status_code == 200

    # It should now appear in the read filter.
    read_filter_response = client.get(
        "/api/v1/notifications?is_read=true",
        headers=auth_headers,
    )

    assert read_filter_response.status_code == 200

    read_ids = [
        item["id"]
        for item in read_filter_response.json()
    ]

    assert notification_id in read_ids


def test_notification_archive_filter(
    client: TestClient,
    auth_headers: dict,
):
    notification = create_notification(
        client,
        auth_headers,
        "Archive Filter Test",
    )

    notification_id = notification["id"]

    # Initially active.
    active_response = client.get(
        "/api/v1/notifications?is_archived=false",
        headers=auth_headers,
    )

    assert active_response.status_code == 200

    active_ids = [
        item["id"]
        for item in active_response.json()
    ]

    assert notification_id in active_ids

    # Archive it.
    archive_response = client.patch(
        f"/api/v1/notifications/{notification_id}/archive",
        headers=auth_headers,
    )

    assert archive_response.status_code == 200

    # It should now appear in archived results.
    archived_response = client.get(
        "/api/v1/notifications?is_archived=true",
        headers=auth_headers,
    )

    assert archived_response.status_code == 200

    archived_ids = [
        item["id"]
        for item in archived_response.json()
    ]

    assert notification_id in archived_ids


def test_bulk_request_requires_notification_ids(
    client: TestClient,
    auth_headers: dict,
):
    response = client.patch(
        "/api/v1/notifications/bulk/archive",
        headers=auth_headers,
        json={},
    )

    assert response.status_code == 422


def test_bulk_request_rejects_empty_notification_ids(
    client: TestClient,
    auth_headers: dict,
):
    response = client.patch(
        "/api/v1/notifications/bulk/archive",
        headers=auth_headers,
        json={
            "notification_ids": [],
        },
    )

    assert response.status_code == 422


def test_bulk_request_rejects_more_than_100_ids(
    client: TestClient,
    auth_headers: dict,
):
    response = client.patch(
        "/api/v1/notifications/bulk/archive",
        headers=auth_headers,
        json={
            "notification_ids": list(range(1, 102)),
        },
    )

    assert response.status_code == 422


def test_notification_list_rejects_invalid_pagination(
    client: TestClient,
    auth_headers: dict,
):
    response = client.get(
        "/api/v1/notifications?skip=-1",
        headers=auth_headers,
    )

    assert response.status_code == 422

    response = client.get(
        "/api/v1/notifications?limit=0",
        headers=auth_headers,
    )

    assert response.status_code == 422

    response = client.get(
        "/api/v1/notifications?limit=101",
        headers=auth_headers,
    )

    assert response.status_code == 422


def test_notification_endpoints_require_authentication(
    client: TestClient,
):
    endpoints = [
        (
            "GET",
            "/api/v1/notifications",
        ),
        (
            "GET",
            "/api/v1/notifications/unread-count",
        ),
        (
            "PATCH",
            "/api/v1/notifications/read-all",
        ),
        (
            "PATCH",
            "/api/v1/notifications/archive-all",
        ),
        (
            "PATCH",
            "/api/v1/notifications/bulk/archive",
        ),
        (
            "PATCH",
            "/api/v1/notifications/bulk/unarchive",
        ),
        (
            "PATCH",
            "/api/v1/notifications/bulk/read",
        ),
        (
            "PATCH",
            "/api/v1/notifications/bulk/unread",
        ),
    ]

    for method, endpoint in endpoints:
        response = client.request(
            method,
            endpoint,
            json={
                "notification_ids": [1],
            }
            if "bulk/" in endpoint
            else None,
        )

        assert response.status_code in (401, 403), (
            f"{method} {endpoint} returned "
            f"{response.status_code}"
        )