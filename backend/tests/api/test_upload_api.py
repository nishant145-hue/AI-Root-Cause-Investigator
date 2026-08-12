import io
import uuid
from uuid import uuid4

import pytest
from app.core.config import settings
from app.main import app
from app.utils.upload_validation import (
    validate_file_size,
)
from fastapi import HTTPException
from fastapi.testclient import TestClient

client = TestClient(app)


def test_upload_valid_json(auth_headers):

    payload = f"""
    {{
        "timestamp":"2026-08-04T10:00:00",
        "level":"ERROR",
        "message":"Database timeout {uuid.uuid4()}"
    }}
    """.encode()

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

    payload = f'{{"timestamp":"{uuid.uuid4()}",'.encode()

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

    payload = f"""
    {{
        "timestamp":"2026-08-04T10:00:00",
        "level":"INFO",
        "message":"Started {uuid.uuid4()}"
    }}
    """.encode()

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
    assert response2.json()["detail"] == "This file has already been uploaded."


def test_upload_response_structure(auth_headers):

    payload = f"""
    {{
        "timestamp":"2026-08-04T10:00:00",
        "level":"ERROR",
        "message":"Timeout {uuid.uuid4()}"
    }}
    """.encode()

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

    assert response.status_code == 200

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

def test_upload_empty_file_returns_400(auth_headers):
    response = client.post(
        "/api/v1/uploads",
        headers=auth_headers,
        files={
            "file": (
                "empty.log",
                io.BytesIO(b""),
                "text/plain",
            )
        },
    )

    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()

def test_upload_php_file_returns_415(auth_headers):
    response = client.post(
        "/api/v1/uploads",
        headers=auth_headers,
        files={
            "file": (
                "malicious.php",
                io.BytesIO(b"<?php echo 'test'; ?>"),
                "application/x-php",
            )
        },
    )

    assert response.status_code == 415

def test_upload_shell_script_returns_415(auth_headers):
    response = client.post(
        "/api/v1/uploads",
        headers=auth_headers,
        files={
            "file": (
                "malicious.sh",
                io.BytesIO(b"#!/bin/sh\necho test"),
                "text/x-shellscript",
            )
        },
    )

    assert response.status_code == 415

def test_upload_double_extension_uses_final_extension(
    auth_headers,
):
    payload = (
        b"INFO double extension security test "
        + uuid.uuid4().hex.encode()
    )

    response = client.post(
        "/api/v1/uploads",
        headers=auth_headers,
        files={
            "file": (
                "something.php.log",
                io.BytesIO(payload),
                "text/plain",
            )
        },
    )

    assert response.status_code in (200, 400)

    if response.status_code == 200:
        data = response.json()

        assert ".." not in data["saved_as"]
        assert ".." not in data["file_path"]

def test_upload_oversized_file_returns_413(auth_headers):
    oversized_payload = b"x" * (
        settings.MAX_UPLOAD_SIZE + 1
    )

    response = client.post(
        "/api/v1/uploads",
        headers=auth_headers,
        files={
            "file": (
                "oversized.log",
                io.BytesIO(oversized_payload),
                "text/plain",
            )
        },
    )

    assert response.status_code == 413

def test_upload_path_traversal_filename_is_safe(auth_headers):
    payload = (
    b"INFO path traversal security test "
    + uuid.uuid4().hex.encode()
)

    response = client.post(
        "/api/v1/uploads",
        headers=auth_headers,
        files={
            "file": (
                "../../evil.log",
                io.BytesIO(payload),
                "text/plain",
            )
        },
    )

    assert response.status_code in (200, 400)

    if response.status_code == 200:
        data = response.json()

        assert ".." not in data["saved_as"]
        assert ".." not in data["file_path"]

def test_upload_extremely_long_filename_is_handled_safely(
    auth_headers,
):
    filename = ("a" * 500) + ".log"

    response = client.post(
        "/api/v1/uploads",
        headers=auth_headers,
        files={
            "file": (
                filename,
                io.BytesIO(b"INFO safe log message"),
                "text/plain",
            )
        },
    )

    assert response.status_code != 500

def test_upload_unicode_filename_is_handled_safely(
    auth_headers,
):
    response = client.post(
        "/api/v1/uploads",
        headers=auth_headers,
        files={
            "file": (
                "server-logs-à¤­à¤¾à¤°à¤¤.log",
                io.BytesIO(b"INFO safe log message"),
                "text/plain",
            )
        },
    )

    assert response.status_code != 500


def test_upload_missing_filename_is_rejected(
    auth_headers,
):
    response = client.post(
        "/api/v1/uploads",
        headers=auth_headers,
        files={
            "file": (
                None,
                io.BytesIO(b"INFO missing filename test"),
                "text/plain",
            )
        },
    )

    assert response.status_code in (400, 422)

def test_upload_exactly_at_maximum_size_returns_success(
    client,
    auth_headers,
):
    unique_marker = f"boundary-{uuid4()}\n".encode()

    payload = (
        unique_marker
        + b"x" * (
            settings.MAX_UPLOAD_SIZE
            - len(unique_marker)
        )
    )

    assert len(payload) == settings.MAX_UPLOAD_SIZE

    response = client.post(
        "/api/v1/uploads",
        headers=auth_headers,
        files={
            "file": (
                "maximum.log",
                io.BytesIO(payload),
                "text/plain",
            )
        },
    )

    assert response.status_code in (200, 201)

def test_upload_one_byte_over_maximum_size_returns_413(
    client,
    auth_headers,
):
    payload = b"x" * (
        settings.MAX_UPLOAD_SIZE + 1
    )

    response = client.post(
        "/api/v1/uploads",
        headers=auth_headers,
        files={
            "file": (
                "oversized.log",
                io.BytesIO(payload),
                "text/plain",
            )
        },
    )

    assert response.status_code == 413

def test_file_size_at_limit_is_allowed():
    validate_file_size(
        settings.MAX_UPLOAD_SIZE
    )


def test_file_size_above_limit_is_rejected():
    with pytest.raises(HTTPException) as exc_info:
        validate_file_size(
            settings.MAX_UPLOAD_SIZE + 1
        )

    assert (
        exc_info.value.status_code
        == 413
    )
