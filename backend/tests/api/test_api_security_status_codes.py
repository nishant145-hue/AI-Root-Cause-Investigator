from uuid import uuid4


AUTH_PREFIX = "/api/v1/auth"
INVESTIGATION_PREFIX = "/api/v1/investigations"
REPORT_PREFIX = "/api/v1/reports"
PREFERENCES_ENDPOINT = "/api/v1/notifications/preferences"


def create_test_user(client):
    suffix = uuid4().hex[:10]

    user = {
        "username": f"security_{suffix}",
        "email": f"security_{suffix}@example.com",
        "password": "Password123!",
        "full_name": "API Security Test User",
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


def auth_headers(token):
    return {
        "Authorization": f"Bearer {token}",
    }


def create_investigation(client, token, title="Security Test"):
    response = client.post(
        INVESTIGATION_PREFIX,
        headers=auth_headers(token),
        json={
            "title": title,
            "description": "API security status-code test",
        },
    )

    assert response.status_code == 201

    return response.json()


# ==================================================================
# 401 — Unauthorized
# ==================================================================


def test_investigation_list_requires_authentication(client):
    response = client.get(
        INVESTIGATION_PREFIX,
    )

    assert response.status_code == 401


def test_investigation_create_requires_authentication(client):
    response = client.post(
        INVESTIGATION_PREFIX,
        json={
            "title": "Unauthenticated Investigation",
            "description": "Should not be created",
        },
    )

    assert response.status_code == 401


def test_investigation_read_requires_authentication(client):
    response = client.get(
        f"{INVESTIGATION_PREFIX}/1",
    )

    assert response.status_code == 401


def test_preferences_require_authentication(client):
    response = client.get(
        PREFERENCES_ENDPOINT,
    )

    assert response.status_code == 401


def test_report_requires_authentication(client):
    response = client.get(
        f"{REPORT_PREFIX}/csv",
    )

    assert response.status_code == 401


def test_invalid_bearer_token_returns_401(client):
    response = client.get(
        INVESTIGATION_PREFIX,
        headers={
            "Authorization": "Bearer definitely-invalid-token",
        },
    )

    assert response.status_code == 401


def test_malformed_authorization_header_returns_401(client):
    response = client.get(
        INVESTIGATION_PREFIX,
        headers={
            "Authorization": "NotBearer token",
        },
    )

    assert response.status_code == 401


# ==================================================================
# 403 — Forbidden / authorization boundary
# ==================================================================


def test_user_cannot_modify_another_users_investigation(
    client,
):
    user_a = create_test_user(client)
    user_b = create_test_user(client)

    tokens_a = login_user(client, user_a)
    tokens_b = login_user(client, user_b)

    investigation_b = create_investigation(
        client,
        tokens_b["access_token"],
        "User B Security Resource",
    )

    response = client.put(
        f"{INVESTIGATION_PREFIX}/{investigation_b['id']}",
        headers=auth_headers(tokens_a["access_token"]),
        json={
            "title": "Unauthorized Update",
        },
    )

    # Depending on the resource's anti-enumeration policy,
    # ownership violations may intentionally be represented
    # as either 403 or 404.
    assert response.status_code in (403, 404)


# ==================================================================
# 404 — Resource not found
# ==================================================================


def test_nonexistent_investigation_returns_404(
    client,
):
    user = create_test_user(client)
    tokens = login_user(client, user)

    response = client.get(
        f"{INVESTIGATION_PREFIX}/999999999",
        headers=auth_headers(tokens["access_token"]),
    )

    assert response.status_code == 404


def test_nonexistent_investigation_history_returns_404(
    client,
):
    user = create_test_user(client)
    tokens = login_user(client, user)

    response = client.get(
        f"{INVESTIGATION_PREFIX}/999999999/history",
        headers=auth_headers(tokens["access_token"]),
    )

    assert response.status_code == 404


def test_nonexistent_investigation_delete_returns_404(
    client,
):
    user = create_test_user(client)
    tokens = login_user(client, user)

    response = client.delete(
        f"{INVESTIGATION_PREFIX}/999999999",
        headers=auth_headers(tokens["access_token"]),
    )

    assert response.status_code == 404


def test_nonexistent_investigation_update_returns_404(
    client,
):
    user = create_test_user(client)
    tokens = login_user(client, user)

    response = client.put(
        f"{INVESTIGATION_PREFIX}/999999999",
        headers=auth_headers(tokens["access_token"]),
        json={
            "title": "Does Not Exist",
        },
    )

    assert response.status_code == 404


# ==================================================================
# 422 — Validation Error
# ==================================================================


def test_investigation_missing_required_title_returns_422(
    client,
):
    user = create_test_user(client)
    tokens = login_user(client, user)

    response = client.post(
        INVESTIGATION_PREFIX,
        headers=auth_headers(tokens["access_token"]),
        json={
            "description": "Title is missing",
        },
    )

    assert response.status_code == 422


def test_investigation_title_too_short_returns_422(
    client,
):
    user = create_test_user(client)
    tokens = login_user(client, user)

    response = client.post(
        INVESTIGATION_PREFIX,
        headers=auth_headers(tokens["access_token"]),
        json={
            "title": "ab",
            "description": "Invalid title",
        },
    )

    assert response.status_code == 422


def test_investigation_title_too_long_returns_422(
    client,
):
    user = create_test_user(client)
    tokens = login_user(client, user)

    response = client.post(
        INVESTIGATION_PREFIX,
        headers=auth_headers(tokens["access_token"]),
        json={
            "title": "x" * 256,
            "description": "Title exceeds maximum length",
        },
    )

    assert response.status_code == 422


def test_investigation_malformed_json_returns_422(
    client,
):
    user = create_test_user(client)
    tokens = login_user(client, user)

    response = client.post(
        INVESTIGATION_PREFIX,
        headers={
            **auth_headers(tokens["access_token"]),
            "Content-Type": "application/json",
        },
        content='{"title": ',
    )

    assert response.status_code == 422


def test_investigation_update_invalid_title_returns_422(
    client,
):
    user = create_test_user(client)
    tokens = login_user(client, user)

    investigation = create_investigation(
        client,
        tokens["access_token"],
        "Valid Investigation",
    )

    response = client.put(
        f"{INVESTIGATION_PREFIX}/{investigation['id']}",
        headers=auth_headers(tokens["access_token"]),
        json={
            "title": "ab",
        },
    )

    assert response.status_code == 422


# ==================================================================
# Malformed resource IDs
# ==================================================================


def test_malformed_investigation_id_returns_422(
    client,
):
    user = create_test_user(client)
    tokens = login_user(client, user)

    response = client.get(
        f"{INVESTIGATION_PREFIX}/not-a-number",
        headers=auth_headers(tokens["access_token"]),
    )

    assert response.status_code == 422


def test_malformed_history_investigation_id_returns_422(
    client,
):
    user = create_test_user(client)
    tokens = login_user(client, user)

    response = client.get(
        f"{INVESTIGATION_PREFIX}/not-a-number/history",
        headers=auth_headers(tokens["access_token"]),
    )

    assert response.status_code == 422


def test_malformed_update_investigation_id_returns_422(
    client,
):
    user = create_test_user(client)
    tokens = login_user(client, user)

    response = client.put(
        f"{INVESTIGATION_PREFIX}/not-a-number",
        headers=auth_headers(tokens["access_token"]),
        json={
            "title": "Invalid ID",
        },
    )

    assert response.status_code == 422
    
def test_negative_investigation_id_does_not_cause_server_error(
    client,
):
    user = create_test_user(client)
    tokens = login_user(client, user)

    response = client.get(
        f"{INVESTIGATION_PREFIX}/-1",
        headers=auth_headers(tokens["access_token"]),
    )

    assert response.status_code in (404, 422)
    
def test_extremely_large_investigation_id_does_not_cause_server_error(
    client,
):
    user = create_test_user(client)
    tokens = login_user(client, user)

    response = client.get(
        f"{INVESTIGATION_PREFIX}/999999999999999999999999999999999999",
        headers=auth_headers(tokens["access_token"]),
    )

    assert response.status_code in (404, 422)
    
def test_investigation_object_title_returns_422(
    client,
):
    user = create_test_user(client)
    tokens = login_user(client, user)

    response = client.post(
        INVESTIGATION_PREFIX,
        headers=auth_headers(tokens["access_token"]),
        json={
            "title": {
                "malicious": "object"
            },
            "description": "Invalid structured input",
        },
    )

    assert response.status_code == 422
    
def test_investigation_null_title_returns_422(
    client,
):
    user = create_test_user(client)
    tokens = login_user(client, user)

    response = client.post(
        INVESTIGATION_PREFIX,
        headers=auth_headers(tokens["access_token"]),
        json={
            "title": None,
            "description": "Invalid null title",
        },
    )

    assert response.status_code == 422
    
def test_investigation_limit_zero_returns_422(client):
    user = create_test_user(client)
    tokens = login_user(client, user)

    response = client.get(
        f"{INVESTIGATION_PREFIX}?limit=0",
        headers=auth_headers(tokens["access_token"]),
    )

    assert response.status_code == 422


def test_investigation_limit_above_maximum_returns_422(client):
    user = create_test_user(client)
    tokens = login_user(client, user)

    response = client.get(
        f"{INVESTIGATION_PREFIX}?limit=101",
        headers=auth_headers(tokens["access_token"]),
    )

    assert response.status_code == 422


def test_investigation_negative_skip_returns_422(client):
    user = create_test_user(client)
    tokens = login_user(client, user)

    response = client.get(
        f"{INVESTIGATION_PREFIX}?skip=-1",
        headers=auth_headers(tokens["access_token"]),
    )

    assert response.status_code == 422
    
def test_invalid_investigation_status_returns_422(client):
    user = create_test_user(client)
    tokens = login_user(client, user)

    response = client.get(
        f"{INVESTIGATION_PREFIX}?status_filter=INVALID_STATUS",
        headers=auth_headers(tokens["access_token"]),
    )

    assert response.status_code == 422
    
def test_other_users_investigation_is_hidden_as_404(
    client,
):
    user_a = create_test_user(client)
    user_b = create_test_user(client)

    tokens_a = login_user(client, user_a)
    tokens_b = login_user(client, user_b)

    investigation_b = create_investigation(
        client,
        tokens_b["access_token"],
        "Private Investigation",
    )

    response = client.get(
        f"{INVESTIGATION_PREFIX}/{investigation_b['id']}",
        headers=auth_headers(
            tokens_a["access_token"]
        ),
    )

    assert response.status_code == 404

    assert response.json()["detail"] == (
        "Investigation not found"
    )