def test_malformed_json_returns_safe_422(client, auth_headers):
    response = client.post(
        "/api/v1/investigations",
        headers={
            **auth_headers,
            "Content-Type": "application/json",
        },
        content='{"title": ',
    )

    assert response.status_code == 422

    body = response.json()

    assert "detail" in body
    assert "traceback" not in response.text.lower()
    assert "secret_key" not in response.text.lower()
    assert "database" not in response.text.lower()
    
def test_validation_error_does_not_echo_sensitive_input(
    client,
    auth_headers,
):
    secret = "SUPER_SECRET_PASSWORD_123"

    response = client.post(
        "/api/v1/investigations",
        headers=auth_headers,
        json={
            "title": 123,
            "description": secret,
        },
    )

    assert response.status_code == 422

    assert secret not in response.text
    
def test_wrong_body_type_returns_safe_422(
    client,
    auth_headers,
):
    response = client.post(
        "/api/v1/investigations",
        headers=auth_headers,
        json=[],
    )

    assert response.status_code == 422

    assert "traceback" not in response.text.lower()
    assert "sqlalchemy" not in response.text.lower()