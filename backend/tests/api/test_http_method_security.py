from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_rejects_unsupported_post_method():
    response = client.post("/health")

    assert response.status_code == 405


def test_root_rejects_unsupported_post_method():
    response = client.post("/")

    assert response.status_code == 405


def test_health_rejects_unsupported_delete_method():
    response = client.delete("/health")

    assert response.status_code == 405


def test_health_rejects_unsupported_patch_method():
    response = client.patch("/health")

    assert response.status_code == 405


def test_health_rejects_trace_method():
    response = client.request(
        "TRACE",
        "/health",
    )

    assert response.status_code in (405, 501)


def test_unknown_endpoint_does_not_accept_trace():
    response = client.request(
        "TRACE",
        "/this-endpoint-does-not-exist",
    )

    assert response.status_code in (404, 405, 501)
    
def test_method_error_does_not_expose_internal_details():
    response = client.post("/health")

    assert response.status_code == 405

    detail = response.text.lower()

    assert "traceback" not in detail
    assert "exception" not in detail
    assert "secret_key" not in detail
    assert "database" not in detail
    assert "sqlalchemy" not in detail