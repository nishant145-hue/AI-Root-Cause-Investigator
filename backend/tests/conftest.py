import os

os.environ["TESTING"] = "true"

import sys
from pathlib import Path

import pytest
from app.database.session import engine
from app.main import app as fastapi_app
from app.models.user import User
from app.parsers.json_parser import JSONParser
from app.parsers.log_parser import LogParser
from app.parsers.txt_parser import TXTParser
from app.parsers.yaml_parser import YAMLParser
from fastapi.testclient import TestClient
from sqlmodel import Session, select

sys.path.append(str(Path(__file__).resolve().parents[1]))

# -------------------------------------------------------------------
# FastAPI Fixtures
# -------------------------------------------------------------------

@pytest.fixture(scope="session")
def app():
    return fastapi_app


@pytest.fixture(scope="session")
def client(app):
    return TestClient(app)

@pytest.fixture
def db_session():
    """
    Creates a SQLModel database session for tests.
    """
    with Session(engine) as session:
        yield session

# -------------------------------------------------------------------
# Sample Logs
# -------------------------------------------------------------------

@pytest.fixture
def sample_logs_dir() -> Path:
    """
    Returns the path to the sample log files.
    """
    return Path(__file__).parent / "sample_logs"


# -------------------------------------------------------------------
# Parser Fixtures
# -------------------------------------------------------------------

@pytest.fixture
def json_parser():
    return JSONParser()


@pytest.fixture
def yaml_parser():
    return YAMLParser()


@pytest.fixture
def txt_parser():
    return TXTParser()


@pytest.fixture
def log_parser():
    return LogParser()


# -------------------------------------------------------------------
# Authentication Fixture
# -------------------------------------------------------------------

@pytest.fixture
def auth_headers(client):
    """
    Registers a test user if needed, logs in,
    and returns fresh Authorization headers
    for each test.
    """

    email = "pytest@example.com"
    password = "Password123!"

    register_data = {
        "username": "pytestuser",
        "email": email,
        "password": password,
        "full_name": "Pytest User",
    }

    client.post(
        "/api/v1/auth/register",
        json=register_data,
    )

    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": email,
            "password": password,
        },
    )

    assert response.status_code == 200, response.text

    token = response.json()["access_token"]

    return {
        "Authorization": f"Bearer {token}"
    }

@pytest.fixture
def test_user(db_session, auth_headers):
    """
    Return the authenticated pytest user used by dashboard tests.
    """

    user = db_session.exec(
        select(User).where(
            User.email == "pytest@example.com"
        )
    ).first()

    assert user is not None

    return user

@pytest.fixture
def admin_headers(client, db_session):
    """
    Register/login a dedicated admin test user.
    """

    email = "pytest-admin@example.com"
    password = "Password123!"

    register_data = {
        "username": "pytestadmin",
        "email": email,
        "password": password,
        "full_name": "Pytest Admin",
    }

    client.post(
        "/api/v1/auth/register",
        json=register_data,
    )

    user = db_session.exec(
        select(User).where(
            User.email == email
        )
    ).first()

    assert user is not None

    user.role = "admin"

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": email,
            "password": password,
        },
    )

    assert response.status_code == 200

    token = response.json()["access_token"]

    return {
        "Authorization": f"Bearer {token}"
    }
