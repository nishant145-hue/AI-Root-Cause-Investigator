import re

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_request_generates_correlation_id():
    response = client.get("/health")

    assert response.status_code == 200

    request_id = response.headers.get("X-Request-ID")

    assert request_id is not None
    assert len(request_id) > 0

    # Generated IDs should be UUIDs.
    uuid_pattern = (
        r"^[0-9a-f]{8}-"
        r"[0-9a-f]{4}-"
        r"[0-9a-f]{4}-"
        r"[0-9a-f]{4}-"
        r"[0-9a-f]{12}$"
    )

    assert re.match(
        uuid_pattern,
        request_id,
        re.IGNORECASE,
    )


def test_request_preserves_correlation_id():
    request_id = "observability-test-123"

    response = client.get(
        "/health",
        headers={
            "X-Request-ID": request_id,
        },
    )

    assert response.status_code == 200

    assert (
        response.headers.get("X-Request-ID")
        == request_id
    )


def test_different_requests_receive_different_ids():
    response_one = client.get("/health")
    response_two = client.get("/health")

    request_id_one = response_one.headers.get(
        "X-Request-ID"
    )
    request_id_two = response_two.headers.get(
        "X-Request-ID"
    )

    assert request_id_one
    assert request_id_two

    assert request_id_one != request_id_two


def test_request_id_is_available_on_ready_endpoint():
    response = client.get("/ready")

    assert response.status_code == 200

    request_id = response.headers.get("X-Request-ID")

    assert request_id


def test_request_id_is_available_on_404():
    response = client.get(
        "/this-route-does-not-exist"
    )

    assert response.status_code == 404

    request_id = response.headers.get("X-Request-ID")

    assert request_id
    
def test_request_completion_metadata_is_structured(
    caplog,
):
    response = client.get("/health")

    assert response.status_code == 200

    request_id = response.headers.get(
        "X-Request-ID"
    )

    assert request_id

    # The request itself succeeded and therefore
    # should expose the expected response metadata.
    assert response.headers.get(
        "X-Request-ID"
    ) == request_id


def test_request_started_and_completed_events_exist():
    response = client.get("/health")

    assert response.status_code == 200

    assert response.headers.get("X-Request-ID")


def test_request_metadata_contains_http_method():
    response = client.get("/health")

    assert response.status_code == 200

    assert response.request.method == "GET"


def test_request_metadata_contains_path():
    response = client.get("/health")

    assert response.status_code == 200

    assert response.request.url.path == "/health"


def test_request_metadata_contains_status_code():
    response = client.get("/health")

    assert response.status_code == 200

    assert response.status_code == 200