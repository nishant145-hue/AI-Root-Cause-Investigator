import uuid

from fastapi import APIRouter
from fastapi.testclient import TestClient

from app.main import app


def test_unexpected_api_exception_does_not_expose_internal_details():
    router = APIRouter()

    secret = (
        "INTERNAL_DATABASE_PASSWORD=SuperSecret123 "
        "postgresql://admin:password@internal-db "
        "C:\\production\\private\\config.env"
    )

    @router.get("/__security_test_internal_error")
    def internal_error():
        raise RuntimeError(secret)

    app.include_router(router)

    client = TestClient(
        app,
        raise_server_exceptions=False,
    )

    try:
        response = client.get(
            "/__security_test_internal_error"
        )

        assert response.status_code == 500

        detail = response.text.lower()

        assert "supersecret123" not in detail
        assert "postgresql://" not in detail
        assert "internal-db" not in detail
        assert "config.env" not in detail
        assert "traceback" not in detail
        assert "runtimeerror" not in detail

        assert response.json() == {
            "detail": "Internal server error."
        }

    finally:
        app.router.routes = [
            route
            for route in app.router.routes
            if getattr(route, "path", None)
            != "/__security_test_internal_error"
        ]