import sys
from pathlib import Path

import pytest
from app.main import app
from app.parsers.json_parser import JSONParser
from app.parsers.log_parser import LogParser
from app.parsers.txt_parser import TXTParser
from app.parsers.yaml_parser import YAMLParser
from fastapi.testclient import TestClient

sys.path.append(str(Path(__file__).resolve().parents[1]))

client = TestClient(app)

@pytest.fixture
def sample_logs_dir() -> Path:
    """
    Returns the path to the sample log files.
    """
    return Path(__file__).parent / "sample_logs"


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

@pytest.fixture(scope="session")
def auth_headers():

    email = "pytest@example.com"

    password = "Password123!"

    register_data = {
        "username": "pytestuser",
        "email": email,
        "password": password,
        "full_name": "Pytest User",
    }

    # Register user (ignore if already exists)
    client.post(
        "/api/v1/auth/register",
        json=register_data,
    )

    # Login
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