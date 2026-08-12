def notification_payload():
    return {
        "provider": "email",
        "severity": "info",
        "subject": "Test notification",
        "message": "Test notification message.",
    }


def test_notification_rejects_empty_subject(client, auth_headers):
    payload = notification_payload()
    payload["subject"] = ""

    response = client.post(
        "/api/v1/notifications",
        json=payload,
        headers=auth_headers,
    )

    assert response.status_code == 422


def test_notification_rejects_whitespace_subject(
    client,
    auth_headers,
):
    payload = notification_payload()
    payload["subject"] = "   "

    response = client.post(
        "/api/v1/notifications",
        json=payload,
        headers=auth_headers,
    )

    assert response.status_code == 422


def test_notification_rejects_empty_message(
    client,
    auth_headers,
):
    payload = notification_payload()
    payload["message"] = ""

    response = client.post(
        "/api/v1/notifications",
        json=payload,
        headers=auth_headers,
    )

    assert response.status_code == 422


def test_notification_rejects_oversized_subject(
    client,
    auth_headers,
):
    payload = notification_payload()
    payload["subject"] = "A" * 256

    response = client.post(
        "/api/v1/notifications",
        json=payload,
        headers=auth_headers,
    )

    assert response.status_code == 422


def test_notification_rejects_oversized_message(
    client,
    auth_headers,
):
    payload = notification_payload()
    payload["message"] = "A" * 10_001

    response = client.post(
        "/api/v1/notifications",
        json=payload,
        headers=auth_headers,
    )

    assert response.status_code == 422


def test_notification_rejects_control_character_in_subject(
    client,
    auth_headers,
):
    payload = notification_payload()
    payload["subject"] = "Test\x00Notification"

    response = client.post(
        "/api/v1/notifications",
        json=payload,
        headers=auth_headers,
    )

    assert response.status_code == 422


def test_notification_rejects_control_character_in_message(
    client,
    auth_headers,
):
    payload = notification_payload()
    payload["message"] = "Test\x00message"

    response = client.post(
        "/api/v1/notifications",
        json=payload,
        headers=auth_headers,
    )

    assert response.status_code == 422


def test_notification_rejects_invalid_provider(
    client,
    auth_headers,
):
    payload = notification_payload()
    payload["provider"] = "invalid-provider"

    response = client.post(
        "/api/v1/notifications",
        json=payload,
        headers=auth_headers,
    )

    assert response.status_code == 422


def test_notification_rejects_invalid_severity(
    client,
    auth_headers,
):
    payload = notification_payload()
    payload["severity"] = "invalid-severity"

    response = client.post(
        "/api/v1/notifications",
        json=payload,
        headers=auth_headers,
    )

    assert response.status_code == 422


def test_notification_rejects_invalid_user_id(
    client,
    auth_headers,
):
    payload = notification_payload()
    payload["user_id"] = -1

    response = client.post(
        "/api/v1/notifications",
        json=payload,
        headers=auth_headers,
    )

    assert response.status_code == 422


def test_notification_accepts_valid_payload(
    client,
    auth_headers,
):
    payload = notification_payload()

    response = client.post(
        "/api/v1/notifications",
        json=payload,
        headers=auth_headers,
    )

    assert response.status_code == 201