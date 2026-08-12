from pathlib import Path
from uuid import uuid4

from sqlmodel import select

from app.exceptions.parser_exceptions import ParserError
from app.models.log_file import LogFile
from app.services.upload_service import LogProcessingService


def test_parser_failure_does_not_leave_orphan_log_file(
    client,
    auth_headers,
    db_session,
    monkeypatch,
):
    payload = (
        b"parser-integrity-test-"
        + uuid4().hex.encode()
    )

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
                "parser-integrity.log",
                payload,
                "text/plain",
            )
        },
    )

    assert response.status_code == 400

    # Verify whether the DB record remains.
    file_hash = __import__(
        "app.utils.hash_utils",
        fromlist=["generate_sha256"],
    ).generate_sha256(payload)

    statement = select(LogFile).where(
        LogFile.sha256_hash == file_hash
    )

    log_file = db_session.exec(statement).first()

    # Security/integrity requirement:
    # failed processing must not leave an orphan record.
    assert log_file is None
    
def test_processing_failure_does_not_leave_orphan_log_file(
    client,
    auth_headers,
    db_session,
    monkeypatch,
):
    payload = (
        b"processing-integrity-test-"
        + uuid4().hex.encode()
    )

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
                "processing-integrity.log",
                payload,
                "text/plain",
            )
        },
    )

    assert response.status_code == 500

    from app.utils.hash_utils import generate_sha256

    file_hash = generate_sha256(payload)

    statement = select(LogFile).where(
        LogFile.sha256_hash == file_hash
    )

    log_file = db_session.exec(statement).first()

    assert log_file is None