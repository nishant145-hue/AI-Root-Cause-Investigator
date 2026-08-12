from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[2]


def test_dockerfile_exists():
    dockerfile = BACKEND_ROOT / "Dockerfile"

    assert dockerfile.exists()


def test_dockerignore_exists():
    dockerignore = BACKEND_ROOT / ".dockerignore"

    assert dockerignore.exists()


def test_start_script_exists():
    start_script = BACKEND_ROOT / "start.sh"

    assert start_script.exists()


def test_start_script_runs_migrations():
    content = (
        BACKEND_ROOT / "start.sh"
    ).read_text(encoding="utf-8")

    assert "alembic upgrade head" in content


def test_start_script_uses_exec():
    content = (
        BACKEND_ROOT / "start.sh"
    ).read_text(encoding="utf-8")

    assert "exec uvicorn" in content


def test_start_script_requires_database_url():
    content = (
        BACKEND_ROOT / "start.sh"
    ).read_text(encoding="utf-8")

    assert 'DATABASE_URL:?DATABASE_URL' in content


def test_start_script_requires_secret_key():
    content = (
        BACKEND_ROOT / "start.sh"
    ).read_text(encoding="utf-8")

    assert 'SECRET_KEY:?SECRET_KEY' in content


def test_start_script_requires_groq_api_key():
    content = (
        BACKEND_ROOT / "start.sh"
    ).read_text(encoding="utf-8")

    assert 'GROQ_API_KEY:?GROQ_API_KEY' in content


def test_dockerfile_contains_healthcheck():
    content = (
        BACKEND_ROOT / "Dockerfile"
    ).read_text(encoding="utf-8")

    assert "HEALTHCHECK" in content
    assert "/health" in content


def test_dockerfile_does_not_contain_secrets():
    content = (
        BACKEND_ROOT / "Dockerfile"
    ).read_text(encoding="utf-8")

    assert "GROQ_API_KEY=" not in content
    assert "SECRET_KEY=" not in content
    assert "DATABASE_URL=" not in content