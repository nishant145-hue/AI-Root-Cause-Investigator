from uuid import uuid4

from app.models.investigation import Investigation
from sqlmodel import Session, select

AUTH_PREFIX = "/api/v1/auth"
INVESTIGATION_PREFIX = "/api/v1/investigations"
DASHBOARD_PREFIX = "/api/v1/dashboard"


def create_test_user(client):
    suffix = uuid4().hex[:10]

    user = {
        "username": f"dashboard_owner_{suffix}",
        "email": f"dashboard_owner_{suffix}@example.com",
        "password": "Password123!",
        "full_name": "Dashboard Isolation User",
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
        "Authorization": f"Bearer {access_token}",
    }


def create_investigation(
    client,
    access_token,
    title,
):
    response = client.post(
        INVESTIGATION_PREFIX,
        headers=auth_headers(access_token),
        json={
            "title": title,
            "description": "Dashboard cross-user isolation test",
        },
    )

    assert response.status_code == 201

    return response.json()


# ------------------------------------------------------------------
# Authentication
# ------------------------------------------------------------------


def test_dashboard_requires_authentication(client):
    endpoints = [
        f"{DASHBOARD_PREFIX}/overview",
        f"{DASHBOARD_PREFIX}/recent",
        f"{DASHBOARD_PREFIX}/timeline",
        f"{DASHBOARD_PREFIX}/severity",
        f"{DASHBOARD_PREFIX}/root-causes",
        f"{DASHBOARD_PREFIX}/failed-components",
        f"{DASHBOARD_PREFIX}/confidence",
    ]

    for endpoint in endpoints:
        response = client.get(endpoint)

        assert response.status_code == 401, endpoint


# ------------------------------------------------------------------
# Recent investigation isolation
# ------------------------------------------------------------------


def test_dashboard_recent_isolated_between_users(client):
    user_a = create_test_user(client)
    user_b = create_test_user(client)

    tokens_a = login_user(client, user_a)
    tokens_b = login_user(client, user_b)

    investigation_a = create_investigation(
        client,
        tokens_a["access_token"],
        "Dashboard User A Investigation",
    )

    investigation_b = create_investigation(
        client,
        tokens_b["access_token"],
        "Dashboard User B Investigation",
    )

    response_a = client.get(
        f"{DASHBOARD_PREFIX}/recent",
        headers=auth_headers(tokens_a["access_token"]),
    )

    response_b = client.get(
        f"{DASHBOARD_PREFIX}/recent",
        headers=auth_headers(tokens_b["access_token"]),
    )

    assert response_a.status_code == 200
    assert response_b.status_code == 200

    data_a = response_a.json()
    data_b = response_b.json()

    ids_a = {
        item["id"]
        for item in data_a
    }

    ids_b = {
        item["id"]
        for item in data_b
    }

    assert investigation_a["id"] in ids_a
    assert investigation_b["id"] not in ids_a

    assert investigation_b["id"] in ids_b
    assert investigation_a["id"] not in ids_b


# ------------------------------------------------------------------
# Overview isolation
# ------------------------------------------------------------------


def test_dashboard_overview_isolated_between_users(
    client,
):
    user_a = create_test_user(client)
    user_b = create_test_user(client)

    tokens_a = login_user(client, user_a)
    tokens_b = login_user(client, user_b)

    create_investigation(
        client,
        tokens_a["access_token"],
        "User A Overview Investigation",
    )

    create_investigation(
        client,
        tokens_b["access_token"],
        "User B Overview Investigation",
    )

    response_a = client.get(
        f"{DASHBOARD_PREFIX}/overview",
        headers=auth_headers(tokens_a["access_token"]),
    )

    response_b = client.get(
        f"{DASHBOARD_PREFIX}/overview",
        headers=auth_headers(tokens_b["access_token"]),
    )

    assert response_a.status_code == 200
    assert response_b.status_code == 200

    overview_a = response_a.json()
    overview_b = response_b.json()

    assert overview_a["total_investigations"] == 1
    assert overview_b["total_investigations"] == 1


# ------------------------------------------------------------------
# Timeline isolation
# ------------------------------------------------------------------


def test_dashboard_timeline_isolated_between_users(
    client,
):
    user_a = create_test_user(client)
    user_b = create_test_user(client)

    tokens_a = login_user(client, user_a)
    tokens_b = login_user(client, user_b)

    create_investigation(
        client,
        tokens_a["access_token"],
        "User A Timeline Investigation",
    )

    create_investigation(
        client,
        tokens_b["access_token"],
        "User B Timeline Investigation",
    )

    response_a = client.get(
        f"{DASHBOARD_PREFIX}/timeline",
        headers=auth_headers(tokens_a["access_token"]),
    )

    response_b = client.get(
        f"{DASHBOARD_PREFIX}/timeline",
        headers=auth_headers(tokens_b["access_token"]),
    )

    assert response_a.status_code == 200
    assert response_b.status_code == 200

    timeline_a = response_a.json()
    timeline_b = response_b.json()

    count_a = sum(
        item["count"]
        for item in timeline_a
    )

    count_b = sum(
        item["count"]
        for item in timeline_b
    )

    assert count_a == 1
    assert count_b == 1