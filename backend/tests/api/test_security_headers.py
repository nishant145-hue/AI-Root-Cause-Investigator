from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_has_x_content_type_options():
    response = client.get("/health")

    assert response.status_code == 200

    assert (
        response.headers.get("x-content-type-options")
        == "nosniff"
    )


def test_health_has_x_frame_options():
    response = client.get("/health")

    assert response.status_code == 200

    assert (
        response.headers.get("x-frame-options")
        == "DENY"
    )


def test_health_has_referrer_policy():
    response = client.get("/health")

    assert response.status_code == 200

    assert (
        response.headers.get("referrer-policy")
        == "strict-origin-when-cross-origin"
    )


def test_health_has_content_security_policy():
    response = client.get("/health")

    assert response.status_code == 200

    assert (
        "default-src 'self'"
        in response.headers.get(
            "content-security-policy",
            "",
        )
    )


def test_security_headers_are_present_on_api_response():
    response = client.get("/")

    assert response.status_code == 200

    headers = response.headers

    assert headers.get(
        "x-content-type-options"
    ) == "nosniff"

    assert headers.get(
        "x-frame-options"
    ) == "DENY"

    assert headers.get(
        "referrer-policy"
    ) == "strict-origin-when-cross-origin"


def test_security_headers_are_present_on_404():
    response = client.get(
        "/this-endpoint-does-not-exist"
    )

    assert response.status_code == 404

    assert response.headers.get(
        "x-content-type-options"
    ) == "nosniff"

    assert response.headers.get(
        "x-frame-options"
    ) == "DENY"
    
def test_csp_has_required_security_directives():
    response = client.get("/health")

    assert response.status_code == 200

    csp = response.headers.get(
        "content-security-policy",
        "",
    )

    assert "default-src 'self'" in csp
    assert "frame-ancestors 'none'" in csp
    assert "base-uri 'self'" in csp
    assert "form-action 'self'" in csp


def test_security_headers_are_present_on_api_404():
    response = client.get(
        "/api/v1/this-endpoint-does-not-exist"
    )

    assert response.status_code == 404

    assert response.headers.get(
        "x-content-type-options"
    ) == "nosniff"

    assert response.headers.get(
        "x-frame-options"
    ) == "DENY"

    assert response.headers.get(
        "referrer-policy"
    ) == "strict-origin-when-cross-origin"

    assert "default-src 'self'" in response.headers.get(
        "content-security-policy",
        "",
    )