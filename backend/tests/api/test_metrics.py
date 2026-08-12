from app.core.metrics import metrics


def test_metrics_endpoint_returns_metrics(client, admin_headers):
    metrics.reset()

    response = client.get(
        "/metrics",
        headers=admin_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert "requests" in data
    assert "status_codes" in data
    assert "methods" in data
    assert "paths" in data
    assert "duration_ms" in data


def test_metrics_record_health_request(client):
    metrics.reset()

    response = client.get("/health")

    assert response.status_code == 200

    snapshot = metrics.snapshot()

    assert snapshot["requests"]["total"] >= 1
    assert snapshot["status_codes"].get(200, 0) >= 1
    assert snapshot["methods"].get("GET", 0) >= 1
    assert snapshot["paths"].get("/health", 0) >= 1


def test_metrics_record_request_duration(client):
    metrics.reset()

    client.get("/health")

    snapshot = metrics.snapshot()

    assert snapshot["duration_ms"]["average"] >= 0
    assert snapshot["duration_ms"]["maximum"] >= 0


def test_metrics_record_multiple_requests(client):
    metrics.reset()

    client.get("/health")
    client.get("/health")
    client.get("/ready")

    snapshot = metrics.snapshot()

    assert snapshot["requests"]["total"] >= 3
    assert snapshot["paths"].get("/health", 0) >= 2
    assert snapshot["paths"].get("/ready", 0) >= 1


def test_metrics_reset():
    metrics.reset()

    metrics.record_request(
        method="GET",
        path="/test",
        status_code=200,
        duration_ms=10.0,
    )

    assert metrics.snapshot()["requests"]["total"] == 1

    metrics.reset()

    snapshot = metrics.snapshot()

    assert snapshot["requests"]["total"] == 0
    assert snapshot["requests"]["errors_5xx"] == 0
    assert snapshot["status_codes"] == {}
    assert snapshot["methods"] == {}
    assert snapshot["paths"] == {}
    
def test_metrics_requires_authentication(client):
    response = client.get("/metrics")

    assert response.status_code == 401
    
def test_metrics_requires_admin(client, auth_headers):
    response = client.get(
        "/metrics",
        headers=auth_headers,
    )

    assert response.status_code == 403

    assert response.json() == {
        "detail": "Admin privileges required."
    }
    
def test_admin_can_access_metrics(client, admin_headers):
    response = client.get(
        "/metrics",
        headers=admin_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert "requests" in data
    assert "status_codes" in data
    assert "methods" in data
    assert "paths" in data
    assert "duration_ms" in data
    
def test_metrics_does_not_expose_sensitive_information(
    client,
    admin_headers,
):
    response = client.get(
        "/metrics",
        headers=admin_headers,
    )

    assert response.status_code == 200

    body = response.text.lower()

    forbidden = [
        "password",
        "secret_key",
        "groq_api_key",
        "authorization",
        "bearer",
        "database_url",
        "postgresql://",
    ]

    for value in forbidden:
        assert value not in body