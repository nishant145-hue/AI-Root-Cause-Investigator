from uuid import uuid4


AUTH_PREFIX = "/api/v1/auth"


def unique_suffix() -> str:
    return uuid4().hex[:10]


def register_payload():
    suffix = unique_suffix()

    return {
        "username": f"validation_{suffix}",
        "email": f"validation_{suffix}@example.com",
        "password": "Password123!",
        "full_name": "Validation Test User",
    }


def test_registration_rejects_short_username(client):
    payload = register_payload()
    payload["username"] = "ab"

    response = client.post(
        f"{AUTH_PREFIX}/register",
        json=payload,
    )

    assert response.status_code == 422


def test_registration_rejects_long_username(client):
    payload = register_payload()
    payload["username"] = "a" * 51

    response = client.post(
        f"{AUTH_PREFIX}/register",
        json=payload,
    )

    assert response.status_code == 422


def test_registration_rejects_invalid_username_characters(client):
    payload = register_payload()
    payload["username"] = "user name"

    response = client.post(
        f"{AUTH_PREFIX}/register",
        json=payload,
    )

    assert response.status_code == 422


def test_registration_rejects_username_control_character(client):
    payload = register_payload()
    payload["username"] = "valid\nusername"

    response = client.post(
        f"{AUTH_PREFIX}/register",
        json=payload,
    )

    assert response.status_code == 422


def test_registration_rejects_short_password(client):
    payload = register_payload()
    payload["password"] = "short"

    response = client.post(
        f"{AUTH_PREFIX}/register",
        json=payload,
    )

    assert response.status_code == 422


def test_registration_rejects_long_password(client):
    payload = register_payload()
    payload["password"] = "A" * 129

    response = client.post(
        f"{AUTH_PREFIX}/register",
        json=payload,
    )

    assert response.status_code == 422


def test_registration_rejects_password_control_character(client):
    payload = register_payload()
    payload["password"] = "Password123!\n"

    response = client.post(
        f"{AUTH_PREFIX}/register",
        json=payload,
    )

    assert response.status_code == 422


def test_registration_rejects_long_full_name(client):
    payload = register_payload()
    payload["full_name"] = "A" * 256

    response = client.post(
        f"{AUTH_PREFIX}/register",
        json=payload,
    )

    assert response.status_code == 422


def test_registration_rejects_control_character_in_full_name(client):
    payload = register_payload()
    payload["full_name"] = "John\nDoe"

    response = client.post(
        f"{AUTH_PREFIX}/register",
        json=payload,
    )

    assert response.status_code == 422


def test_registration_accepts_valid_username_and_name(client):
    payload = register_payload()

    response = client.post(
        f"{AUTH_PREFIX}/register",
        json=payload,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["username"] == payload["username"]
    assert data["email"] == payload["email"]
    assert data["full_name"] == payload["full_name"]

    # Sensitive fields must never be returned.
    assert "password" not in data
    assert "hashed_password" not in data
    
def test_login_rejects_empty_username(client):
    response = client.post(
        f"{AUTH_PREFIX}/login",
        data={
            "username": "",
            "password": "Password123!",
        },
    )

    assert response.status_code in {400, 401, 422}


def test_login_rejects_empty_password(client):
    response = client.post(
        f"{AUTH_PREFIX}/login",
        data={
            "username": "nonexistent@example.com",
            "password": "",
        },
    )

    assert response.status_code in {400, 401, 422}


def test_login_rejects_oversized_username(client):
    response = client.post(
        f"{AUTH_PREFIX}/login",
        data={
            "username": "a" * 1000,
            "password": "Password123!",
        },
    )

    assert response.status_code in {400, 401, 422}


def test_login_rejects_oversized_password(client):
    response = client.post(
        f"{AUTH_PREFIX}/login",
        data={
            "username": "nonexistent@example.com",
            "password": "A" * 1000,
        },
    )

    assert response.status_code in {400, 401, 422}


def test_login_does_not_disclose_user_existence(client):
    unknown_user = client.post(
        f"{AUTH_PREFIX}/login",
        data={
            "username": "does-not-exist@example.com",
            "password": "WrongPassword123!",
        },
    )

    assert unknown_user.status_code == 401

    assert unknown_user.json()["detail"] == (
        "Invalid email or password"
    )


def test_login_does_not_disclose_invalid_password_details(client):
    suffix = unique_suffix()

    payload = {
        "username": f"login_validation_{suffix}",
        "email": f"login_validation_{suffix}@example.com",
        "password": "CorrectPassword123!",
        "full_name": "Login Validation User",
    }

    register_response = client.post(
        f"{AUTH_PREFIX}/register",
        json=payload,
    )

    assert register_response.status_code == 201

    login_response = client.post(
        f"{AUTH_PREFIX}/login",
        data={
            "username": payload["email"],
            "password": "WrongPassword123!",
        },
    )

    assert login_response.status_code == 401

    detail = login_response.json()["detail"]

    assert detail == "Invalid email or password"

    assert payload["email"] not in detail
    assert "WrongPassword123!" not in detail
    assert "CorrectPassword123!" not in detail
    assert "bcrypt" not in detail.lower()
    assert "hash" not in detail.lower()
    assert "bcrypt" not in detail.lower()
    assert "hash" not in detail.lower()
    
def test_run_investigation_rejects_zero_log_file_id(client):
    payload = register_payload()

    register_response = client.post(
        f"{AUTH_PREFIX}/register",
        json=payload,
    )

    assert register_response.status_code == 201

    login_response = client.post(
        f"{AUTH_PREFIX}/login",
        data={
            "username": payload["email"],
            "password": payload["password"],
        },
    )

    assert login_response.status_code == 200

    headers = {
        "Authorization": (
            f"Bearer {login_response.json()['access_token']}"
        )
    }

    investigation_response = client.post(
        "/api/v1/investigations",
        json={
            "title": f"Validation {unique_suffix()}",
            "description": "Validation test",
        },
        headers=headers,
    )

    assert investigation_response.status_code == 201

    investigation_id = investigation_response.json()["id"]

    response = client.post(
        f"/api/v1/investigations/{investigation_id}/run",
        json={"log_file_id": 0},
        headers=headers,
    )

    assert response.status_code == 422


def test_run_investigation_rejects_negative_log_file_id(client):
    payload = register_payload()

    register_response = client.post(
        f"{AUTH_PREFIX}/register",
        json=payload,
    )

    assert register_response.status_code == 201

    login_response = client.post(
        f"{AUTH_PREFIX}/login",
        data={
            "username": payload["email"],
            "password": payload["password"],
        },
    )

    assert login_response.status_code == 200

    headers = {
        "Authorization": (
            f"Bearer {login_response.json()['access_token']}"
        )
    }

    investigation_response = client.post(
        "/api/v1/investigations",
        json={
            "title": f"Validation {unique_suffix()}",
            "description": "Validation test",
        },
        headers=headers,
    )

    assert investigation_response.status_code == 201

    investigation_id = investigation_response.json()["id"]

    response = client.post(
        f"/api/v1/investigations/{investigation_id}/run",
        json={"log_file_id": -1},
        headers=headers,
    )

    assert response.status_code == 422


def test_run_investigation_rejects_missing_log_file_id(client):
    payload = register_payload()

    register_response = client.post(
        f"{AUTH_PREFIX}/register",
        json=payload,
    )

    assert register_response.status_code == 201

    login_response = client.post(
        f"{AUTH_PREFIX}/login",
        data={
            "username": payload["email"],
            "password": payload["password"],
        },
    )

    assert login_response.status_code == 200

    headers = {
        "Authorization": (
            f"Bearer {login_response.json()['access_token']}"
        )
    }

    investigation_response = client.post(
        "/api/v1/investigations",
        json={
            "title": f"Validation {unique_suffix()}",
        },
        headers=headers,
    )

    assert investigation_response.status_code == 201

    investigation_id = investigation_response.json()["id"]

    response = client.post(
        f"/api/v1/investigations/{investigation_id}/run",
        json={},
        headers=headers,
    )

    assert response.status_code == 422


def test_run_investigation_rejects_non_integer_log_file_id(client):
    payload = register_payload()

    register_response = client.post(
        f"{AUTH_PREFIX}/register",
        json=payload,
    )

    assert register_response.status_code == 201

    login_response = client.post(
        f"{AUTH_PREFIX}/login",
        data={
            "username": payload["email"],
            "password": payload["password"],
        },
    )

    assert login_response.status_code == 200

    headers = {
        "Authorization": (
            f"Bearer {login_response.json()['access_token']}"
        )
    }

    investigation_response = client.post(
        "/api/v1/investigations",
        json={
            "title": f"Validation {unique_suffix()}",
        },
        headers=headers,
    )

    assert investigation_response.status_code == 201

    investigation_id = investigation_response.json()["id"]

    response = client.post(
        f"/api/v1/investigations/{investigation_id}/run",
        json={"log_file_id": "not-an-id"},
        headers=headers,
    )

    assert response.status_code == 422
    
def test_dashboard_recent_rejects_zero_limit(
    client,
    auth_headers,
):
    response = client.get(
        "/api/v1/dashboard/recent?limit=0",
        headers=auth_headers,
    )

    assert response.status_code == 422


def test_dashboard_recent_rejects_negative_limit(
    client,
    auth_headers,
):
    response = client.get(
        "/api/v1/dashboard/recent?limit=-1",
        headers=auth_headers,
    )

    assert response.status_code == 422


def test_dashboard_recent_rejects_excessive_limit(
    client,
    auth_headers,
):
    response = client.get(
        "/api/v1/dashboard/recent?limit=101",
        headers=auth_headers,
    )

    assert response.status_code == 422


def test_dashboard_recent_rejects_negative_offset(
    client,
    auth_headers,
):
    response = client.get(
        "/api/v1/dashboard/recent?offset=-1",
        headers=auth_headers,
    )

    assert response.status_code == 422
    
def test_negative_investigation_id_returns_422(
    client,
    auth_headers,
):
    response = client.get(
        "/api/v1/investigations/-1",
        headers=auth_headers,
    )

    assert response.status_code == 422


def test_zero_investigation_id_returns_422(
    client,
    auth_headers,
):
    response = client.get(
        "/api/v1/investigations/0",
        headers=auth_headers,
    )

    assert response.status_code == 422


def test_negative_investigation_id_returns_422(
    client,
    auth_headers,
):
    response = client.get(
        "/api/v1/investigations/-1",
        headers=auth_headers,
    )

    assert response.status_code == 422


def test_zero_investigation_id_returns_422(
    client,
    auth_headers,
):
    response = client.get(
        "/api/v1/investigations/0",
        headers=auth_headers,
    )

    assert response.status_code == 422