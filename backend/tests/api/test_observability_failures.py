from tests.api.test_authorization_ownership import (
    auth_headers,
    create_test_user,
    login_user,
)


FAILURES_ENDPOINT = "/api/v1/observability/failures"


def _get_failure_telemetry(client):
    user = create_test_user(client)
    tokens = login_user(client, user)

    response = client.get(
        FAILURES_ENDPOINT,
        headers=auth_headers(tokens["access_token"]),
    )

    assert response.status_code == 200

    return response.json()


def test_failure_observability_requires_authentication(client):
    response = client.get(FAILURES_ENDPOINT)

    assert response.status_code == 401


def test_failure_observability_returns_expected_contract(client):
    data = _get_failure_telemetry(client)

    assert "failures" in data
    assert "aggregate" in data

    telemetry = data["failures"]

    assert isinstance(telemetry, dict)

    assert "failure_count" in telemetry
    assert "retry_count" in telemetry
    assert "timeout_count" in telemetry
    assert "failures" in telemetry

    assert isinstance(telemetry["failure_count"], int)
    assert isinstance(telemetry["retry_count"], int)
    assert isinstance(telemetry["timeout_count"], int)
    assert isinstance(telemetry["failures"], list)

    assert isinstance(data["aggregate"], dict)


def test_failure_observability_empty_state_is_safe(client):
    data = _get_failure_telemetry(client)

    telemetry = data["failures"]

    assert telemetry["failure_count"] >= 0
    assert telemetry["retry_count"] >= 0
    assert telemetry["timeout_count"] >= 0

    assert isinstance(telemetry["failures"], list)
    assert isinstance(data["aggregate"], dict)


def test_failure_observability_does_not_expose_internal_details(
    client,
):
    data = _get_failure_telemetry(client)

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


def test_failure_observability_available_to_authenticated_users(
    client,
):
    user_a = create_test_user(client)
    user_b = create_test_user(client)

    tokens_a = login_user(client, user_a)
    tokens_b = login_user(client, user_b)

    response_a = client.get(
        FAILURES_ENDPOINT,
        headers=auth_headers(tokens_a["access_token"]),
    )

    response_b = client.get(
        FAILURES_ENDPOINT,
        headers=auth_headers(tokens_b["access_token"]),
    )

    assert response_a.status_code == 200
    assert response_b.status_code == 200

    data_a = response_a.json()
    data_b = response_b.json()

    assert "failures" in data_a
    assert "aggregate" in data_a

    assert "failures" in data_b
    assert "aggregate" in data_b
