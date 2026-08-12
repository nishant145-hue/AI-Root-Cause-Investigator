import uuid

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_response_contains_request_id():
    response = client.get("/health")

    assert response.status_code == 200

    request_id = response.headers.get("X-Request-ID")

    assert request_id is not None
    assert request_id != ""


def test_generated_request_id_is_valid_uuid():
    response = client.get("/health")

    assert response.status_code == 200

    request_id = response.headers.get("X-Request-ID")

    assert request_id is not None

    # Should not raise ValueError
    parsed = uuid.UUID(request_id)

    assert str(parsed) == request_id


def test_supplied_request_id_is_preserved():
    request_id = "test-request-123"

    response = client.get(
        "/health",
        headers={
            "X-Request-ID": request_id,
        },
    )

    assert response.status_code == 200
    assert response.headers.get("X-Request-ID") == request_id


def test_missing_request_id_generates_new_id():
    response = client.get("/health")

    assert response.status_code == 200

    request_id = response.headers.get("X-Request-ID")

    assert request_id is not None

    uuid.UUID(request_id)


def test_different_requests_get_different_request_ids():
    response_1 = client.get("/health")
    response_2 = client.get("/health")

    request_id_1 = response_1.headers.get("X-Request-ID")
    request_id_2 = response_2.headers.get("X-Request-ID")

    assert request_id_1 is not None
    assert request_id_2 is not None
    assert request_id_1 != request_id_2


def test_oversized_request_id_is_replaced():
    oversized_request_id = "x" * 129

    response = client.get(
        "/health",
        headers={
            "X-Request-ID": oversized_request_id,
        },
    )

    assert response.status_code == 200

    request_id = response.headers.get("X-Request-ID")

    assert request_id is not None
    assert request_id != oversized_request_id

    # Middleware should generate a UUID instead.
    uuid.UUID(request_id)


def test_request_id_is_present_on_404():
    response = client.get(
        "/this-endpoint-does-not-exist",
    )

    assert response.status_code == 404

    request_id = response.headers.get("X-Request-ID")

    assert request_id is not None
    uuid.UUID(request_id)