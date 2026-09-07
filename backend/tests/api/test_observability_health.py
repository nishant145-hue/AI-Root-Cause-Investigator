from tests.api.test_authorization_ownership import (
    auth_headers,
    create_test_user,
    login_user,
)


OBSERVABILITY_HEALTH = "/api/v1/observability/health"


def test_observability_health_requires_authentication(client):
    response = client.get(OBSERVABILITY_HEALTH)

    assert response.status_code == 401


def test_observability_health_returns_runtime_snapshot(client):
    user = create_test_user(client)
    tokens = login_user(client, user)

    response = client.get(
        OBSERVABILITY_HEALTH,
        headers=auth_headers(tokens["access_token"]),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] in {
        "HEALTHY",
        "DEGRADED",
        "SATURATED",
        "SHUTTING_DOWN",
    }

    assert "shutdown" in data
    assert "execution" in data
    assert "investigations" in data
    assert "failures" in data


def test_observability_health_shutdown_contract(client):
    user = create_test_user(client)
    tokens = login_user(client, user)

    response = client.get(
        OBSERVABILITY_HEALTH,
        headers=auth_headers(tokens["access_token"]),
    )

    assert response.status_code == 200

    shutdown = response.json()["shutdown"]

    assert "state" in shutdown
    assert "closed" in shutdown

    assert shutdown["state"] in {
        "RUNNING",
        "SHUTTING_DOWN",
    }

    assert isinstance(shutdown["closed"], bool)


def test_observability_health_execution_contract(client):
    user = create_test_user(client)
    tokens = login_user(client, user)

    response = client.get(
        OBSERVABILITY_HEALTH,
        headers=auth_headers(tokens["access_token"]),
    )

    assert response.status_code == 200

    execution = response.json()["execution"]

    required_fields = {
        "active",
        "limit",
        "available",
        "queued",
        "queue_limit",
        "queue_available",
    }

    assert required_fields.issubset(execution.keys())

    for field in required_fields:
        assert isinstance(execution[field], int)
        assert execution[field] >= 0


def test_observability_health_investigation_contract(client):
    user = create_test_user(client)
    tokens = login_user(client, user)

    response = client.get(
        OBSERVABILITY_HEALTH,
        headers=auth_headers(tokens["access_token"]),
    )

    assert response.status_code == 200

    investigations = response.json()["investigations"]

    required_fields = {
        "tracked",
        "running",
        "completed_tasks",
        "failed_tasks",
    }

    assert required_fields.issubset(investigations.keys())

    for field in required_fields:
        assert isinstance(investigations[field], int)
        assert investigations[field] >= 0


def test_observability_health_does_not_expose_internal_details(client):
    user = create_test_user(client)
    tokens = login_user(client, user)

    response = client.get(
        OBSERVABILITY_HEALTH,
        headers=auth_headers(tokens["access_token"]),
    )

    assert response.status_code == 200

    body = response.text.lower()

    forbidden_terms = {
        "traceback",
        "sqlalchemy",
        "postgresql",
        "password",
        "secret_key",
        "database_url",
    }

    for term in forbidden_terms:
        assert term not in body
