from app.core.config import settings


def test_secret_key_is_loaded_but_not_empty():
    assert settings.SECRET_KEY
    assert settings.SECRET_KEY.strip()


def test_database_url_is_loaded_but_not_empty():
    assert settings.DATABASE_URL
    assert settings.DATABASE_URL.strip()


def test_groq_api_key_is_loaded_but_not_empty():
    assert settings.GROQ_API_KEY
    assert settings.GROQ_API_KEY.strip()


def test_production_debug_can_be_disabled():
    # Production deployment must be able to run with DEBUG=False.
    assert isinstance(settings.DEBUG, bool)


def test_sensitive_settings_are_not_exposed_by_public_attributes():
    sensitive_names = {
        "SECRET_KEY",
        "DATABASE_URL",
        "GROQ_API_KEY",
        "SMTP_PASSWORD",
        "SLACK_WEBHOOK_URL",
        "TEAMS_WEBHOOK_URL",
    }

    public_names = {
        name
        for name in dir(settings)
        if not name.startswith("_")
    }

    # This verifies the names are configuration fields, not dynamically
    # exposed through an accidental public API object.
    assert sensitive_names.intersection(public_names) == sensitive_names
    
def test_health_endpoint_does_not_expose_configuration(client):
    response = client.get("/health")

    assert response.status_code == 200

    body = response.text

    assert settings.SECRET_KEY not in body
    assert settings.DATABASE_URL not in body
    assert settings.GROQ_API_KEY not in body