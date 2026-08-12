from uuid import uuid4


AUTH_PREFIX = "/api/v1/auth"
PREFERENCES_ENDPOINT = "/api/v1/notifications/preferences"


def create_test_user(client):
    suffix = uuid4().hex[:10]

    user = {
        "username": f"pref_{suffix}",
        "email": f"pref_{suffix}@example.com",
        "password": "Password123!",
        "full_name": "Preference Ownership User",
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

    data = response.json()

    assert "access_token" in data

    return data


def auth_headers(access_token):
    return {
        "Authorization": f"Bearer {access_token}",
    }


# ------------------------------------------------------------------
# Authentication
# ------------------------------------------------------------------


def test_get_preferences_requires_authentication(client):
    response = client.get(
        PREFERENCES_ENDPOINT,
    )

    assert response.status_code == 401


def test_update_preferences_requires_authentication(client):
    response = client.put(
        PREFERENCES_ENDPOINT,
        json={
            "email_enabled": False,
        },
    )

    assert response.status_code == 401


# ------------------------------------------------------------------
# Own preferences
# ------------------------------------------------------------------


def test_user_can_get_own_preferences(client):
    user = create_test_user(client)
    tokens = login_user(client, user)

    response = client.get(
        PREFERENCES_ENDPOINT,
        headers=auth_headers(tokens["access_token"]),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["user_id"] is not None
    assert data["email_enabled"] is True
    assert data["slack_enabled"] is False
    assert data["teams_enabled"] is False
    assert data["critical_only"] is False
    assert data["daily_digest"] is False
    assert data["weekly_digest"] is False


def test_user_can_update_own_preferences(client):
    user = create_test_user(client)
    tokens = login_user(client, user)

    response = client.put(
        PREFERENCES_ENDPOINT,
        headers=auth_headers(tokens["access_token"]),
        json={
            "email_enabled": False,
            "slack_enabled": True,
            "teams_enabled": True,
            "critical_only": True,
            "daily_digest": True,
            "weekly_digest": True,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["email_enabled"] is False
    assert data["slack_enabled"] is True
    assert data["teams_enabled"] is True
    assert data["critical_only"] is True
    assert data["daily_digest"] is True
    assert data["weekly_digest"] is True


# ------------------------------------------------------------------
# User isolation
# ------------------------------------------------------------------


def test_users_have_separate_notification_preferences(client):
    user_a = create_test_user(client)
    user_b = create_test_user(client)

    tokens_a = login_user(client, user_a)
    tokens_b = login_user(client, user_b)

    response_a = client.get(
        PREFERENCES_ENDPOINT,
        headers=auth_headers(tokens_a["access_token"]),
    )

    response_b = client.get(
        PREFERENCES_ENDPOINT,
        headers=auth_headers(tokens_b["access_token"]),
    )

    assert response_a.status_code == 200
    assert response_b.status_code == 200

    preferences_a = response_a.json()
    preferences_b = response_b.json()

    assert preferences_a["user_id"] != preferences_b["user_id"]
    assert preferences_a["id"] != preferences_b["id"]


def test_updating_user_a_preferences_does_not_modify_user_b(
    client,
):
    user_a = create_test_user(client)
    user_b = create_test_user(client)

    tokens_a = login_user(client, user_a)
    tokens_b = login_user(client, user_b)

    # Create preferences for both users.
    response_a = client.get(
        PREFERENCES_ENDPOINT,
        headers=auth_headers(tokens_a["access_token"]),
    )

    response_b = client.get(
        PREFERENCES_ENDPOINT,
        headers=auth_headers(tokens_b["access_token"]),
    )

    assert response_a.status_code == 200
    assert response_b.status_code == 200

    preferences_a_before = response_a.json()
    preferences_b_before = response_b.json()

    # User A changes every preference.
    update_response = client.put(
        PREFERENCES_ENDPOINT,
        headers=auth_headers(tokens_a["access_token"]),
        json={
            "email_enabled": False,
            "slack_enabled": True,
            "teams_enabled": True,
            "critical_only": True,
            "daily_digest": True,
            "weekly_digest": True,
        },
    )

    assert update_response.status_code == 200

    # User B reads their preferences again.
    response_b_after = client.get(
        PREFERENCES_ENDPOINT,
        headers=auth_headers(tokens_b["access_token"]),
    )

    assert response_b_after.status_code == 200

    preferences_b_after = response_b_after.json()

    # User B's preference record must remain unchanged.
    assert preferences_b_after["id"] == preferences_b_before["id"]
    assert (
        preferences_b_after["user_id"]
        == preferences_b_before["user_id"]
    )

    assert (
        preferences_b_after["email_enabled"]
        == preferences_b_before["email_enabled"]
    )
    assert (
        preferences_b_after["slack_enabled"]
        == preferences_b_before["slack_enabled"]
    )
    assert (
        preferences_b_after["teams_enabled"]
        == preferences_b_before["teams_enabled"]
    )
    assert (
        preferences_b_after["critical_only"]
        == preferences_b_before["critical_only"]
    )
    assert (
        preferences_b_after["daily_digest"]
        == preferences_b_before["daily_digest"]
    )
    assert (
        preferences_b_after["weekly_digest"]
        == preferences_b_before["weekly_digest"]
    )

    # Confirm User A actually changed.
    response_a_after = client.get(
        PREFERENCES_ENDPOINT,
        headers=auth_headers(tokens_a["access_token"]),
    )

    assert response_a_after.status_code == 200

    preferences_a_after = response_a_after.json()

    assert preferences_a_after["id"] == preferences_a_before["id"]
    assert preferences_a_after["user_id"] == preferences_a_before["user_id"]

    assert preferences_a_after["email_enabled"] is False
    assert preferences_a_after["slack_enabled"] is True
    assert preferences_a_after["teams_enabled"] is True
    assert preferences_a_after["critical_only"] is True
    assert preferences_a_after["daily_digest"] is True
    assert preferences_a_after["weekly_digest"] is True