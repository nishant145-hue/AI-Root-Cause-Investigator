from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_allowed_frontend_origin_gets_cors_header():
    response = client.get(
        "/health",
        headers={
            "Origin": "http://localhost:5173",
        },
    )

    assert response.status_code == 200

    assert (
        response.headers.get("access-control-allow-origin")
        == "http://localhost:5173"
    )


def test_second_allowed_frontend_origin_gets_cors_header():
    response = client.get(
        "/health",
        headers={
            "Origin": "http://localhost:3000",
        },
    )

    assert response.status_code == 200

    assert (
        response.headers.get("access-control-allow-origin")
        == "http://localhost:3000"
    )


def test_untrusted_origin_does_not_get_cors_permission():
    response = client.get(
        "/health",
        headers={
            "Origin": "https://evil.example.com",
        },
    )

    assert response.status_code == 200

    assert (
        response.headers.get("access-control-allow-origin")
        != "https://evil.example.com"
    )


def test_cors_does_not_use_wildcard_origin():
    response = client.get(
        "/health",
        headers={
            "Origin": "https://evil.example.com",
        },
    )

    assert (
        response.headers.get("access-control-allow-origin")
        != "*"
    )


def test_preflight_rejects_untrusted_origin():
    response = client.options(
        "/api/v1/auth/me",
        headers={
            "Origin": "https://evil.example.com",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 400


def test_preflight_allows_configured_origin():
    response = client.options(
        "/api/v1/auth/me",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200

    assert (
        response.headers.get("access-control-allow-origin")
        == "http://localhost:5173"
    )


def test_untrusted_origin_does_not_receive_cors_access():
    response = client.options(
        "/api/v1/auth/me",
        headers={
            "Origin": "https://evil.example.com",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 400

    assert (
        response.headers.get(
            "access-control-allow-origin"
        )
        != "https://evil.example.com"
    )
    
def test_preflight_allows_supported_api_methods():
    methods = [
        "GET",
        "POST",
        "PUT",
        "PATCH",
        "DELETE",
    ]

    for method in methods:
        response = client.options(
            "/api/v1/auth/me",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": method,
            },
        )

        assert response.status_code == 200, method

        assert (
            response.headers.get(
                "access-control-allow-origin"
            )
            == "http://localhost:5173"
        )


def test_preflight_does_not_allow_unsupported_method():
    response = client.options(
        "/api/v1/auth/me",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "TRACE",
        },
    )

    assert response.status_code == 400


def test_preflight_allows_authorization_header():
    response = client.options(
        "/api/v1/auth/me",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Authorization",
        },
    )

    assert response.status_code == 200

    allowed_headers = response.headers.get(
        "access-control-allow-headers",
        "",
    ).lower()

    assert "authorization" in allowed_headers


def test_preflight_allows_content_type_header():
    response = client.options(
        "/api/v1/auth/me",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type",
        },
    )

    assert response.status_code == 200


def test_preflight_rejects_unapproved_request_header():
    response = client.options(
        "/api/v1/auth/me",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "X-Internal-Secret",
        },
    )

    assert response.status_code == 400


def test_cors_credentials_are_enabled_for_trusted_origin():
    response = client.options(
        "/api/v1/auth/me",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200

    assert (
        response.headers.get(
            "access-control-allow-credentials"
        )
        == "true"
    )