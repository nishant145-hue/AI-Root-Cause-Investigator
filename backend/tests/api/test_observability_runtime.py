from tests.api.test_authorization_ownership import (
    auth_headers,
    create_test_user,
    login_user,
)


RUNTIME_ENDPOINT = "/api/v1/observability/runtime"


def _get_runtime_snapshot(client):
    user = create_test_user(client)
    tokens = login_user(client, user)

    response = client.get(
        RUNTIME_ENDPOINT,
        headers=auth_headers(tokens["access_token"]),
    )

    assert response.status_code == 200

    return response.json()


def test_runtime_observability_requires_authentication(client):
    response = client.get(RUNTIME_ENDPOINT)

    assert response.status_code == 401


def test_runtime_observability_returns_expected_sections(client):
    data = _get_runtime_snapshot(client)

    assert data["version"] == "1.0"

    assert "execution" in data
    assert "resource" in data
    assert "failures" in data

    assert isinstance(data["execution"], dict)
    assert isinstance(data["resource"], dict)
    assert isinstance(data["failures"], dict)


def test_runtime_observability_does_not_include_investigation_without_id(
    client,
):
    data = _get_runtime_snapshot(client)

    assert "investigation" not in data


def test_runtime_observability_execution_snapshot_is_safe(client):
    data = _get_runtime_snapshot(client)

    execution = data["execution"]

    assert isinstance(execution, dict)

    for key, value in execution.items():
        assert value is not None


def test_runtime_observability_resource_snapshot_is_safe(client):
    data = _get_runtime_snapshot(client)

    resource = data["resource"]

    assert isinstance(resource, dict)

    for key, value in resource.items():
        assert value is not None


def test_runtime_observability_failure_snapshot_is_safe(client):
    data = _get_runtime_snapshot(client)

    failures = data["failures"]

    assert isinstance(failures, dict)

    for key, value in failures.items():
        assert value is not None


def test_runtime_observability_does_not_expose_internal_details(
    client,
):
    data = _get_runtime_snapshot(client)

    body = str(data).lower()

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


def test_runtime_observability_available_to_multiple_users(client):
    user_a = create_test_user(client)
    user_b = create_test_user(client)

    tokens_a = login_user(client, user_a)
    tokens_b = login_user(client, user_b)

    response_a = client.get(
        RUNTIME_ENDPOINT,
        headers=auth_headers(tokens_a["access_token"]),
    )

    response_b = client.get(
        RUNTIME_ENDPOINT,
        headers=auth_headers(tokens_b["access_token"]),
    )

    assert response_a.status_code == 200
    assert response_b.status_code == 200

    assert response_a.json()["version"] == "1.0"
    assert response_b.json()["version"] == "1.0"
