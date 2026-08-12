from pathlib import Path
from uuid import uuid4

from app.utils.file_utils import UPLOAD_DIR


def test_uploaded_filename_is_not_used_as_storage_filename(
    client,
    auth_headers,
    monkeypatch,
):
    from app.services.upload_service import (
        LogProcessingService,
        ParsedLogService,
    )

    monkeypatch.setattr(
        LogProcessingService,
        "process",
        lambda path: [],
    )

    monkeypatch.setattr(
        ParsedLogService,
        "save_logs",
        lambda **kwargs: None,
    )

    original_filename = "../../malicious.log"

    response = client.post(
        "/api/v1/uploads",
        headers=auth_headers,
        files={
            "file": (
                original_filename,
                b"unique-storage-security-" + uuid4().hex.encode(),
                "text/plain",
            )
        },
    )

    assert response.status_code == 200

    data = response.json()

    saved_as = data["saved_as"]
    file_path = Path(data["file_path"])

    # Client-controlled filename must not become the storage filename.
    assert saved_as != original_filename
    assert ".." not in saved_as

    # Storage must remain inside UPLOAD_DIR.
    upload_root = UPLOAD_DIR.resolve()
    resolved_file = file_path.resolve()

    assert resolved_file.parent == upload_root

    # Physical file should exist after successful upload.
    assert resolved_file.exists()

    # Cleanup test artifact.
    if resolved_file.exists():
        resolved_file.unlink()


def test_uploaded_file_uses_generated_storage_filename(
    client,
    auth_headers,
    monkeypatch,
):
    from app.services.upload_service import (
        LogProcessingService,
        ParsedLogService,
    )

    monkeypatch.setattr(
        LogProcessingService,
        "process",
        lambda path: [],
    )

    monkeypatch.setattr(
        ParsedLogService,
        "save_logs",
        lambda **kwargs: None,
    )

    response = client.post(
        "/api/v1/uploads",
        headers=auth_headers,
        files={
            "file": (
                "server-production.log",
                b"unique-generated-name-" + uuid4().hex.encode(),
                "text/plain",
            )
        },
    )

    assert response.status_code == 200

    data = response.json()

    saved_as = data["saved_as"]

    # UUID + .log
    assert saved_as.endswith(".log")
    assert saved_as != "server-production.log"

    # The generated name should not contain path separators.
    assert "/" not in saved_as
    assert "\\" not in saved_as
    assert ".." not in saved_as

    file_path = Path(data["file_path"])

    if file_path.exists():
        file_path.unlink()

from pathlib import Path
from uuid import uuid4

from app.utils.file_utils import UPLOAD_DIR


def test_uploaded_filename_is_not_used_as_storage_filename(
    client,
    auth_headers,
    monkeypatch,
):
    from app.services.upload_service import (
        LogProcessingService,
        ParsedLogService,
    )

    monkeypatch.setattr(
        LogProcessingService,
        "process",
        lambda path: [],
    )

    monkeypatch.setattr(
        ParsedLogService,
        "save_logs",
        lambda **kwargs: None,
    )

    original_filename = "../../malicious.log"

    response = client.post(
        "/api/v1/uploads",
        headers=auth_headers,
        files={
            "file": (
                original_filename,
                b"unique-storage-security-" + uuid4().hex.encode(),
                "text/plain",
            )
        },
    )

    assert response.status_code == 200

    data = response.json()

    saved_as = data["saved_as"]
    file_path = Path(data["file_path"])

    # Client-controlled filename must not become the storage filename.
    assert saved_as != original_filename
    assert ".." not in saved_as

    # Storage must remain inside UPLOAD_DIR.
    upload_root = UPLOAD_DIR.resolve()
    resolved_file = file_path.resolve()

    assert resolved_file.parent == upload_root

    # Physical file should exist after successful upload.
    assert resolved_file.exists()

    # Cleanup test artifact.
    if resolved_file.exists():
        resolved_file.unlink()


def test_uploaded_file_uses_generated_storage_filename(
    client,
    auth_headers,
    monkeypatch,
):
    from app.services.upload_service import (
        LogProcessingService,
        ParsedLogService,
    )

    monkeypatch.setattr(
        LogProcessingService,
        "process",
        lambda path: [],
    )

    monkeypatch.setattr(
        ParsedLogService,
        "save_logs",
        lambda **kwargs: None,
    )

    response = client.post(
        "/api/v1/uploads",
        headers=auth_headers,
        files={
            "file": (
                "server-production.log",
                b"unique-generated-name-" + uuid4().hex.encode(),
                "text/plain",
            )
        },
    )

    assert response.status_code == 200

    data = response.json()

    saved_as = data["saved_as"]

    # UUID + .log
    assert saved_as.endswith(".log")
    assert saved_as != "server-production.log"

    # The generated name should not contain path separators.
    assert "/" not in saved_as
    assert "\\" not in saved_as
    assert ".." not in saved_as

    file_path = Path(data["file_path"])

    if file_path.exists():
        file_path.unlink()


def test_upload_processing_failure_removes_physical_file(
    client,
    auth_headers,
    monkeypatch,
):
    from app.services.upload_service import LogProcessingService

    def fail_processing(path):
        raise RuntimeError("simulated processing failure")

    monkeypatch.setattr(
        LogProcessingService,
        "process",
        fail_processing,
    )

    response = client.post(
        "/api/v1/uploads",
        headers=auth_headers,
        files={
            "file": (
                "processing-failure.log",
                b"unique-processing-failure-" + uuid4().hex.encode(),
                "text/plain",
            )
        },
    )

    assert response.status_code == 500

    # The service should remove the physical file after
    # an unexpected processing failure.
    upload_root = UPLOAD_DIR.resolve()

    matching_files = list(
        upload_root.glob("*")
    )

    # No file generated by this request should remain.
    assert not any(
        "processing-failure" in file.name
        for file in matching_files
    )


def test_upload_parser_failure_removes_physical_file(
    client,
    auth_headers,
    monkeypatch,
):
    from app.exceptions.parser_exceptions import ParserError
    from app.services.upload_service import LogProcessingService

    def fail_processing(path):
        raise ParserError("simulated parser failure")

    monkeypatch.setattr(
        LogProcessingService,
        "process",
        fail_processing,
    )

    response = client.post(
        "/api/v1/uploads",
        headers=auth_headers,
        files={
            "file": (
                "parser-failure.log",
                b"unique-parser-failure-" + uuid4().hex.encode(),
                "text/plain",
            )
        },
    )

    assert response.status_code == 400

def test_upload_parser_failure_removes_physical_file(
    client,
    auth_headers,
    monkeypatch,
):
    from app.exceptions.parser_exceptions import ParserError
    from app.services.upload_service import LogProcessingService

    def fail_processing(path):
        raise ParserError("simulated parser failure")

    monkeypatch.setattr(
        LogProcessingService,
        "process",
        fail_processing,
    )

    response = client.post(
        "/api/v1/uploads",
        headers=auth_headers,
        files={
            "file": (
                "parser-failure.log",
                b"unique-parser-failure-" + uuid4().hex.encode(),
                "text/plain",
            )
        },
    )

    assert response.status_code == 400