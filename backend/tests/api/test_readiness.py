from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_readiness_returns_200_when_database_is_available():
    response = client.get("/ready")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ready"
    assert data["service"] == "AI Root Cause Investigator"
    assert "version" in data

    assert data["dependencies"]["database"] == "healthy"


def test_readiness_has_request_id():
    response = client.get("/ready")

    assert response.status_code == 200

    request_id = response.headers.get("x-request-id")

    assert request_id is not None
    assert len(request_id) > 0


def test_readiness_has_security_headers():
    response = client.get("/ready")

    assert response.status_code == 200

    assert (
        response.headers.get("x-content-type-options")
        == "nosniff"
    )

    assert (
        response.headers.get("x-frame-options")
        == "DENY"
    )

    assert (
        response.headers.get("referrer-policy")
        == "strict-origin-when-cross-origin"
    )


def test_readiness_does_not_expose_database_details():
    response = client.get("/ready")

    assert response.status_code == 200

    body = response.text.lower()

    assert "postgresql://" not in body
    assert "password" not in body
    assert "database_url" not in body
    assert "traceback" not in body