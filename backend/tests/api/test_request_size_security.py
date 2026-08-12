from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings


client = TestClient(app)


def test_request_body_within_limit_is_allowed():
    payload = b"x" * 1024

    response = client.post(
        "/api/v1/auth/login",
        content=payload,
        headers={
            "Content-Type": "application/octet-stream",
        },
    )

    assert response.status_code != 413


def test_request_body_exceeding_limit_returns_413():
    payload = b"x" * (
        settings.MAX_REQUEST_BODY_SIZE + 1
    )

    response = client.post(
        "/api/v1/auth/login",
        content=payload,
        headers={
            "Content-Type": "application/octet-stream",
        },
    )

    assert response.status_code == 413


def test_oversized_request_does_not_expose_internal_details():
    payload = b"x" * (
        settings.MAX_REQUEST_BODY_SIZE + 1
    )

    response = client.post(
        "/api/v1/auth/login",
        content=payload,
        headers={
            "Content-Type": "application/octet-stream",
        },
    )

    assert response.status_code == 413

    detail = response.text.lower()

    assert "traceback" not in detail
    assert "exception" not in detail
    assert "secret_key" not in detail
    assert "database" not in detail
    assert "internal" not in detail