import io

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_upload_valid_json(auth_headers):

    payload = b"""
    {
        "timestamp":"2026-08-04T10:00:00",
        "level":"ERROR",
        "message":"Database timeout"
    }
    """

    response = client.post(
        "/api/v1/uploads",
        headers=auth_headers,
        files={
            "file": (
                "test.json",
                io.BytesIO(payload),
                "application/json",
            )
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["filename"] == "test.json"

    assert data["parsed_logs"] == 1
    
def test_upload_invalid_json(auth_headers):

    payload = b"""
    {
        "timestamp":
    }
    """

    response = client.post(
        "/api/v1/uploads",
        headers=auth_headers,
        files={
            "file": (
                "invalid.json",
                io.BytesIO(payload),
                "application/json",
            )
        },
    )

    assert response.status_code == 400

    assert "Invalid JSON" in response.json()["detail"]
    
def test_upload_unsupported_file(auth_headers):

    response = client.post(
        "/api/v1/uploads",
        headers=auth_headers,
        files={
            "file": (
                "virus.exe",
                io.BytesIO(b"123"),
                "application/octet-stream",
            )
        },
    )

    assert response.status_code == 415
    
def test_duplicate_upload(auth_headers):

    payload = b"""
    {
        "timestamp":"2026-08-04T10:00:00",
        "level":"INFO",
        "message":"Started"
    }
    """

    response1 = client.post(
        "/api/v1/uploads",
        headers=auth_headers,
        files={
            "file": (
                "dup.json",
                io.BytesIO(payload),
                "application/json",
            )
        },
    )

    assert response1.status_code == 200

    response2 = client.post(
        "/api/v1/uploads",
        headers=auth_headers,
        files={
            "file": (
                "dup.json",
                io.BytesIO(payload),
                "application/json",
            )
        },
    )

    assert response2.status_code == 409
    
def test_upload_response_structure(auth_headers):

    payload = b"""
    {
        "timestamp":"2026-08-04T10:00:00",
        "level":"ERROR",
        "message":"Timeout"
    }
    """

    response = client.post(
        "/api/v1/uploads",
        headers=auth_headers,
        files={
            "file": (
                "structure.json",
                io.BytesIO(payload),
                "application/json",
            )
        },
    )

    data = response.json()

    expected = {
        "filename",
        "saved_as",
        "file_path",
        "content_type",
        "size",
        "message",
        "parsed_logs",
    }

    assert expected.issubset(data.keys())
    
