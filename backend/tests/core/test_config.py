from app.core.config import Settings


def test_production_configuration_is_valid():
    settings = Settings(
        SECRET_KEY="a" * 64,
        DATABASE_URL="postgresql://example",
        GROQ_API_KEY="test-groq-key",
        TESTING=False,
    )

    settings.validate_production()


def test_testing_configuration_skips_production_validation():
    settings = Settings(
        SECRET_KEY="",
        DATABASE_URL="",
        GROQ_API_KEY="",
        TESTING=True,
    )

    settings.validate_production()


def test_short_secret_key_is_rejected():
    settings = Settings(
        SECRET_KEY="short",
        DATABASE_URL="postgresql://example",
        GROQ_API_KEY="test-groq-key",
        TESTING=False,
    )

    try:
        settings.validate_production()
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "32 characters" in str(exc)


def test_missing_database_url_is_rejected():
    settings = Settings(
        SECRET_KEY="a" * 64,
        DATABASE_URL="",
        GROQ_API_KEY="test-groq-key",
        TESTING=False,
    )

    try:
        settings.validate_production()
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "DATABASE_URL" in str(exc)


def test_missing_groq_api_key_is_rejected():
    settings = Settings(
        SECRET_KEY="a" * 64,
        DATABASE_URL="postgresql://example",
        GROQ_API_KEY="",
        TESTING=False,
    )

    try:
        settings.validate_production()
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "GROQ_API_KEY" in str(exc)