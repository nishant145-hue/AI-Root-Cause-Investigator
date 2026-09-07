from uuid import uuid4


AUTH_PREFIX = "/api/v1/auth"


def create_test_user(client):
    suffix = uuid4().hex[:10]

    user = {
        "username": f"analytics_report_{suffix}",
        "email": f"analytics_report_{suffix}@example.com",
        "password": "Password123!",
        "full_name": "Analytics Report User",
    }

    response = client.post(
        f"{AUTH_PREFIX}/register",
        json=user,
    )

    assert response.status_code == 201

    return user


def login_user(client, user):
    response = client.post(
        f"{AUTH_PREFIX}/login",
        data={
            "username": user["email"],
            "password": user["password"],
        },
    )

    assert response.status_code == 200

    return response.json()


def auth_headers(access_token):
    return {
        "Authorization": f"Bearer {access_token}"
    }


def create_investigation(
    client,
    access_token,
    title,
):
    response = client.post(
        "/api/v1/investigations",
        headers=auth_headers(access_token),
        json={
            "title": title,
            "description": "Analytics reporting test",
        },
    )

    assert response.status_code == 201

    return response.json()


def test_analytics_report_requires_authentication(
    client,
):
    response = client.get(
        "/api/v1/investigations/1/analytics/report"
    )

    assert response.status_code == 401


def test_analytics_report_returns_json(
    client,
):
    user = create_test_user(client)

    tokens = login_user(
        client,
        user,
    )

    investigation = create_investigation(
        client,
        tokens["access_token"],
        "Analytics Report Test",
    )

    response = client.get(
        f"/api/v1/investigations/"
        f"{investigation['id']}/analytics/report",
        headers=auth_headers(
            tokens["access_token"]
        ),
    )

    assert response.status_code == 200

    assert response.headers[
        "content-type"
    ].startswith(
        "application/json"
    )

    data = response.json()

    assert (
        data["investigation_id"]
        == investigation["id"]
    )

    assert "overview" in data

    assert "agent_performance" in data

    assert "bottlenecks" in data

    assert "failure_retry_metrics" in data

    assert "timeline" in data


def test_analytics_report_is_user_isolated(
    client,
):
    user_a = create_test_user(client)
    user_b = create_test_user(client)

    tokens_a = login_user(
        client,
        user_a,
    )

    tokens_b = login_user(
        client,
        user_b,
    )

    investigation_a = create_investigation(
        client,
        tokens_a["access_token"],
        "USER_A_ANALYTICS",
    )

    investigation_b = create_investigation(
        client,
        tokens_b["access_token"],
        "USER_B_ANALYTICS",
    )

    response = client.get(
        f"/api/v1/investigations/"
        f"{investigation_b['id']}/analytics/report",
        headers=auth_headers(
            tokens_a["access_token"]
        ),
    )

    assert response.status_code == 404

    response = client.get(
        f"/api/v1/investigations/"
        f"{investigation_a['id']}/analytics/report",
        headers=auth_headers(
            tokens_b["access_token"]
        ),
    )

    assert response.status_code == 404
