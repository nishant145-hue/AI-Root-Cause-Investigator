from app.core.log_sanitizer import sanitize_log_message


def test_sensitive_values_are_removed_before_logging():
    sensitive_values = [
        "password=SuperSecret123!",
        "api_key=SUPER_SECRET_123",
        "SECRET_KEY=production-secret",
        "postgresql://admin:password@internal-db",
        "Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.test.signature",
    ]

    for value in sensitive_values:
        sanitized = sanitize_log_message(value)

        assert "SuperSecret123!" not in sanitized
        assert "SUPER_SECRET_123" not in sanitized
        assert "production-secret" not in sanitized
        assert "postgresql://admin:password@internal-db" not in sanitized
        assert "eyJhbGciOiJIUzI1NiJ9" not in sanitized