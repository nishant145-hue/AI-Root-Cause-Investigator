from uuid import uuid4


AUTH_PREFIX = "/api/v1/auth"
INVESTIGATION_PREFIX = "/api/v1/investigations"


def create_user(client):
    suffix = uuid4().hex[:10]

    user = {
        "username": f"massassign_{suffix}",
        "email": f"massassign_{suffix}@example.com",
        "password": "Password123!",
        "full_name": "Mass Assignment User",
    }

    response = client.post(
        f"{AUTH_PREFIX}/register",
        json=user,
    )

    assert response.status_code == 201

    return user


def login(client, user):
    response = client.post(
        f"{AUTH_PREFIX}/login",
        data={
            "username": user["email"],
            "password": user["password"],
        },
    )

    assert response.status_code == 200

    return response.json()["access_token"]


def headers(token):
    return {
        "Authorization": f"Bearer {token}",
    }


# ------------------------------------------------------------------
# User registration mass-assignment protection
# ------------------------------------------------------------------


def test_registration_cannot_assign_admin_role(client):
    """
    role must never be accepted from a public registration request.
    """

    suffix = uuid4().hex[:10]

    payload = {
        "username": f"roleinject_{suffix}",
        "email": f"roleinject_{suffix}@example.com",
        "password": "Password123!",
        "full_name": "Role Injection Test",
        "role": "admin",
    }

    response = client.post(
        f"{AUTH_PREFIX}/register",
        json=payload,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["role"] == "user"


def test_registration_cannot_set_is_verified(client):
    """
    A client must not be able to mark its account as verified.
    """

    suffix = uuid4().hex[:10]

    payload = {
        "username": f"verifyinject_{suffix}",
        "email": f"verifyinject_{suffix}@example.com",
        "password": "Password123!",
        "full_name": "Verification Injection Test",
        "is_verified": True,
    }

    response = client.post(
        f"{AUTH_PREFIX}/register",
        json=payload,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["is_verified"] is False


def test_registration_cannot_disable_or_control_active_state(client):
    """
    Client-controlled is_active must not override the server default.
    """

    suffix = uuid4().hex[:10]

    payload = {
        "username": f"activeinject_{suffix}",
        "email": f"activeinject_{suffix}@example.com",
        "password": "Password123!",
        "full_name": "Active State Injection Test",
        "is_active": False,
    }

    response = client.post(
        f"{AUTH_PREFIX}/register",
        json=payload,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["is_active"] is True


# ------------------------------------------------------------------
# User ID injection
# ------------------------------------------------------------------


def test_registration_cannot_assign_user_id(client):
    """
    A client must not be able to select its own database user ID.
    """

    suffix = uuid4().hex[:10]

    payload = {
        "username": f"idinject_{suffix}",
        "email": f"idinject_{suffix}@example.com",
        "password": "Password123!",
        "full_name": "User ID Injection Test",
        "id": 999999999,
    }

    response = client.post(
        f"{AUTH_PREFIX}/register",
        json=payload,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["id"] != 999999999


# ------------------------------------------------------------------
# Profile response must not expose writable privileged fields
# ------------------------------------------------------------------


def test_profile_role_is_server_controlled(client):
    """
    The profile endpoint must report the database role rather than
    accepting a client-controlled role.
    """

    user = create_user(client)
    token = login(client, user)

    response = client.get(
        f"{AUTH_PREFIX}/profile",
        headers=headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["role"] == "user"


# ------------------------------------------------------------------
# Multiple privileged fields together
# ------------------------------------------------------------------


def test_registration_rejects_combined_privilege_injection(client):
    """
    Supplying several privileged fields simultaneously must not
    create an elevated account.
    """

    suffix = uuid4().hex[:10]

    payload = {
        "username": f"combined_{suffix}",
        "email": f"combined_{suffix}@example.com",
        "password": "Password123!",
        "full_name": "Combined Injection Test",
        "id": 999999999,
        "role": "admin",
        "is_active": False,
        "is_verified": True,
        "user_id": 999999999,
    }

    response = client.post(
        f"{AUTH_PREFIX}/register",
        json=payload,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["id"] != 999999999
    assert data["role"] == "user"
    assert data["is_active"] is True
    assert data["is_verified"] is False