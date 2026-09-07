from tests.api.test_authorization_ownership import (
    auth_headers,
    create_investigation,
    create_test_user,
    login_user,
)


OBSERVABILITY_PREFIX = "/api/v1/observability"


# ------------------------------------------------------------------
# Investigation observability ownership
# ------------------------------------------------------------------


def test_user_can_access_own_investigation_observability(client):
    user = create_test_user(client)
    tokens = login_user(client, user)

    investigation = create_investigation(
        client,
        tokens["access_token"],
        "Own Observability Investigation",
    )

    response = client.get(
        f"{OBSERVABILITY_PREFIX}/investigations/"
        f"{investigation['id']}",
        headers=auth_headers(tokens["access_token"]),
    )

    assert response.status_code in (200, 404)


def test_user_cannot_access_another_users_observability(client):
    user_a = create_test_user(client)
    user_b = create_test_user(client)

    tokens_a = login_user(client, user_a)
    tokens_b = login_user(client, user_b)

    investigation_b = create_investigation(
        client,
        tokens_b["access_token"],
        "User B Observability Investigation",
    )

    response = client.get(
        f"{OBSERVABILITY_PREFIX}/investigations/"
        f"{investigation_b['id']}",
        headers=auth_headers(tokens_a["access_token"]),
    )

    assert response.status_code in (403, 404)


# ------------------------------------------------------------------
# Summary ownership
# ------------------------------------------------------------------


def test_user_cannot_access_another_users_observability_summary(
    client,
):
    user_a = create_test_user(client)
    user_b = create_test_user(client)

    tokens_a = login_user(client, user_a)
    tokens_b = login_user(client, user_b)

    investigation_b = create_investigation(
        client,
        tokens_b["access_token"],
        "User B Observability Summary",
    )

    response = client.get(
        f"{OBSERVABILITY_PREFIX}/investigations/"
        f"{investigation_b['id']}/summary",
        headers=auth_headers(tokens_a["access_token"]),
    )

    assert response.status_code in (403, 404)


# ------------------------------------------------------------------
# Timeline ownership
# ------------------------------------------------------------------


def test_user_cannot_access_another_users_investigation_timeline(
    client,
):
    user_a = create_test_user(client)
    user_b = create_test_user(client)

    tokens_a = login_user(client, user_a)
    tokens_b = login_user(client, user_b)

    investigation_b = create_investigation(
        client,
        tokens_b["access_token"],
        "User B Investigation Timeline",
    )

    response = client.get(
        f"{OBSERVABILITY_PREFIX}/investigations/"
        f"{investigation_b['id']}/timeline",
        headers=auth_headers(tokens_a["access_token"]),
    )

    assert response.status_code in (403, 404)


# ------------------------------------------------------------------
# Critical path ownership
# ------------------------------------------------------------------


def test_user_cannot_access_another_users_critical_path(
    client,
):
    user_a = create_test_user(client)
    user_b = create_test_user(client)

    tokens_a = login_user(client, user_a)
    tokens_b = login_user(client, user_b)

    investigation_b = create_investigation(
        client,
        tokens_b["access_token"],
        "User B Critical Path Investigation",
    )

    response = client.get(
        f"{OBSERVABILITY_PREFIX}/investigations/"
        f"{investigation_b['id']}/critical-path",
        headers=auth_headers(tokens_a["access_token"]),
    )

    assert response.status_code in (403, 404)


# ------------------------------------------------------------------
# Authentication protection
# ------------------------------------------------------------------


def test_observability_requires_authentication(client):
    response = client.get(
        f"{OBSERVABILITY_PREFIX}/investigations/1",
    )

    assert response.status_code == 401


def test_observability_summary_requires_authentication(client):
    response = client.get(
        f"{OBSERVABILITY_PREFIX}/investigations/1/summary",
    )

    assert response.status_code == 401


def test_observability_timeline_requires_authentication(client):
    response = client.get(
        f"{OBSERVABILITY_PREFIX}/investigations/1/timeline",
    )

    assert response.status_code == 401


def test_observability_critical_path_requires_authentication(
    client,
):
    response = client.get(
        f"{OBSERVABILITY_PREFIX}/investigations/1/critical-path",
    )

    assert response.status_code == 401


# ------------------------------------------------------------------
# Input validation
# ------------------------------------------------------------------


def test_observability_rejects_invalid_investigation_id(
    client,
    auth_headers,
):
    response = client.get(
        f"{OBSERVABILITY_PREFIX}/investigations/not-a-valid-id",
        headers=auth_headers,
    )

    assert response.status_code == 422


def test_observability_summary_rejects_invalid_investigation_id(
    client,
    auth_headers,
):
    response = client.get(
        f"{OBSERVABILITY_PREFIX}/investigations/"
        f"not-a-valid-id/summary",
        headers=auth_headers,
    )

    assert response.status_code == 422


def test_observability_timeline_rejects_invalid_investigation_id(
    client,
    auth_headers,
):
    response = client.get(
        f"{OBSERVABILITY_PREFIX}/investigations/"
        f"not-a-valid-id/timeline",
        headers=auth_headers,
    )

    assert response.status_code == 422


def test_observability_critical_path_rejects_invalid_investigation_id(
    client,
    auth_headers,
):
    response = client.get(
        f"{OBSERVABILITY_PREFIX}/investigations/"
        f"not-a-valid-id/critical-path",
        headers=auth_headers,
    )

    assert response.status_code == 422


# ------------------------------------------------------------------
# Information disclosure protection
# ------------------------------------------------------------------


def _assert_no_internal_details(response):
    detail = str(
        response.json().get("detail", "")
    ).lower()

    assert "traceback" not in detail
    assert "sqlalchemy" not in detail
    assert "postgres" not in detail
    assert "database" not in detail
    assert "password" not in detail
    assert "secret_key" not in detail


def test_observability_nonexistent_investigation_is_safe(
    client,
    auth_headers,
):
    response = client.get(
        f"{OBSERVABILITY_PREFIX}/investigations/999999999",
        headers=auth_headers,
    )

    assert response.status_code in (403, 404)

    _assert_no_internal_details(response)


def test_observability_summary_nonexistent_investigation_is_safe(
    client,
    auth_headers,
):
    response = client.get(
        f"{OBSERVABILITY_PREFIX}/investigations/"
        f"999999999/summary",
        headers=auth_headers,
    )

    assert response.status_code in (403, 404)

    _assert_no_internal_details(response)


def test_observability_timeline_nonexistent_investigation_is_safe(
    client,
    auth_headers,
):
    response = client.get(
        f"{OBSERVABILITY_PREFIX}/investigations/"
        f"999999999/timeline",
        headers=auth_headers,
    )

    assert response.status_code in (403, 404)

    _assert_no_internal_details(response)


def test_observability_critical_path_nonexistent_investigation_is_safe(
    client,
    auth_headers,
):
    response = client.get(
        f"{OBSERVABILITY_PREFIX}/investigations/"
        f"999999999/critical-path",
        headers=auth_headers,
    )

    assert response.status_code in (403, 404)

    _assert_no_internal_details(response)
