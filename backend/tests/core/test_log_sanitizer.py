from app.core.log_sanitizer import sanitize_log_message


def test_password_is_redacted():
    message = "Login failed password=SuperSecret123!"

    result = sanitize_log_message(message)

    assert "SuperSecret123!" not in result
    assert "[REDACTED]" in result


def test_api_key_is_redacted():
    message = "api_key=super-secret-api-key"

    result = sanitize_log_message(message)

    assert "super-secret-api-key" not in result
    assert "[REDACTED]" in result


def test_secret_key_is_redacted():
    message = "SECRET_KEY=my-production-secret"

    result = sanitize_log_message(message)

    assert "my-production-secret" not in result
    assert "[REDACTED]" in result


def test_database_password_is_redacted():
    message = (
        "postgresql://admin:very-secret-password@internal-db"
    )

    result = sanitize_log_message(message)

    assert "very-secret-password" not in result
    assert "[REDACTED]" in result


def test_bearer_token_is_redacted():
    message = (
        "Authorization: Bearer "
        "eyJhbGciOiJIUzI1NiJ9.test.payload"
    )

    result = sanitize_log_message(message)

    assert "eyJhbGciOiJIUzI1NiJ9" not in result
    assert "[REDACTED]" in result


def test_jwt_is_redacted():
    token = (
        "eyJhbGciOiJIUzI1NiJ9."
        "eyJzdWIiOiIxMjMifQ."
        "signature"
    )

    result = sanitize_log_message(
        f"token={token}"
    )

    assert token not in result
    assert "[REDACTED_JWT]" in result


def test_normal_message_is_preserved():
    message = (
        "AI investigation completed successfully. "
        "Investigation ID=42"
    )

    result = sanitize_log_message(message)

    assert result == message