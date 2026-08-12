import io
import uuid

from app.exceptions.ai_exceptions import AIError
from app.exceptions.parser_exceptions import ParserError
from app.models.log_file import LogFile
from app.models.user import User
from app.services.investigation_service import InvestigationService
from app.services.log_processing_service import LogProcessingService
from sqlmodel import select

AUTH_PREFIX = "/api/v1/auth"
INVESTIGATION_PREFIX = "/api/v1/investigations"
UPLOAD_ENDPOINT = "/api/v1/uploads"


def create_test_user(client):
    suffix = uuid.uuid4().hex[:10]

    user = {
        "username": f"disclosure_{suffix}",
        "email": f"disclosure_{suffix}@example.com",
        "password": "Password123!",
        "full_name": "Disclosure Test User",
    }

    response = client.post(
        f"{AUTH_PREFIX}/register",
        json=user,
    )

    assert response.status_code == 201

    return user


def login_user(client, user):
    response = client.post(
        f"{AUTH_PREFIX}/login",
        data={
            "username": user["email"],
            "password": user["password"],
        },
    )

    assert response.status_code == 200

    return response.json()


def auth_headers(access_token):
    return {
        "Authorization": f"Bearer {access_token}",
    }


def create_owned_log_file(
    db_session,
    user_id: int,
):
    unique_id = uuid.uuid4().hex

    stored_filename = (
        f"disclosure-test-{unique_id}.log"
    )

    log_file = LogFile(
        user_id=user_id,
        original_filename="disclosure-test.log",
        stored_filename=stored_filename,
        storage_path=(
            f"uploads/raw/{stored_filename}"
        ),
        mime_type="text/plain",
        file_size=100,
        sha256_hash=None,
        status="uploaded",
    )

    db_session.add(log_file)
    db_session.commit()
    db_session.refresh(log_file)

    return log_file


def test_parser_exception_does_not_leak_internal_details(
    client,
    auth_headers,
    monkeypatch,
):
    secret = (
        "SECRET_DATABASE_PASSWORD=SuperSecret123 "
        "C:\\production\\private\\secret.log "
        "postgresql://internal-db"
    )

    def fail_processing(path):
        raise ParserError(secret)

    monkeypatch.setattr(
        LogProcessingService,
        "process",
        fail_processing,
    )

    payload = (
        b"parser-disclosure-test-"
        + uuid.uuid4().hex.encode()
    )

    response = client.post(
        UPLOAD_ENDPOINT,
        headers=auth_headers,
        files={
            "file": (
                "disclosure-test.log",
                io.BytesIO(payload),
                "text/plain",
            )
        },
    )

    assert response.status_code == 400

    detail = str(
        response.json().get("detail", "")
    )

    assert secret not in detail
    assert "SECRET_DATABASE_PASSWORD" not in detail
    assert "postgresql://" not in detail
    assert "C:\\production" not in detail


def test_ai_error_does_not_leak_internal_details(
    client,
    db_session,
    monkeypatch,
):
    user = create_test_user(client)
    tokens = login_user(client, user)

    headers = auth_headers(
        tokens["access_token"]
    )

    me_response = client.get(
    f"{AUTH_PREFIX}/profile",
    headers=headers,
)

    assert me_response.status_code == 200

    user_data = me_response.json()

    assert user_data["email"] == user["email"]

    user_record = db_session.exec(
        select(User).where(
            User.email == user["email"]
        )
    ).first()

    assert user_record is not None

    user_id = user_record.id
    
    log_file = create_owned_log_file(
        db_session,
        user_id,
    )

    investigation_response = client.post(
        INVESTIGATION_PREFIX,
        headers=headers,
        json={
            "title": (
                "AI Disclosure Test "
                + uuid.uuid4().hex[:8]
            ),
            "description": "Security test",
        },
    )

    assert investigation_response.status_code == 201

    investigation_id = (
        investigation_response.json()["id"]
    )

    secret = (
        "GROQ_API_KEY=super-secret-key "
        "https://internal-ai-server.local "
        "postgresql://admin:password@internal-db"
    )

    def fail_ai(*args, **kwargs):
        raise AIError(secret)

    monkeypatch.setattr(
        InvestigationService,
        "_run_ai_investigation",
        fail_ai,
    )

    response = client.post(
        f"{INVESTIGATION_PREFIX}/"
        f"{investigation_id}/run",
        headers=headers,
        json={
            "log_file_id": log_file.id,
        },
    )

    assert response.status_code in (
        500,
        502,
    )

    detail = str(
        response.json().get("detail", "")
    )

    assert secret not in detail
    assert "GROQ_API_KEY" not in detail
    assert "internal-ai-server.local" not in detail
    assert "postgresql://" not in detail


def test_generic_ai_exception_does_not_leak_internal_details(
    client,
    db_session,
    monkeypatch,
):
    user = create_test_user(client)
    tokens = login_user(client, user)

    headers = auth_headers(
        tokens["access_token"]
    )

    me_response = client.get(
    f"{AUTH_PREFIX}/profile",
    headers=headers,
)

    assert me_response.status_code == 200

    user_data = me_response.json()

    assert user_data["email"] == user["email"]

    user_record = db_session.exec(
        select(User).where(
            User.email == user["email"]
        )
    ).first()

    assert user_record is not None

    user_id = user_record.id

    log_file = create_owned_log_file(
        db_session,
        user_id,
    )

    investigation_response = client.post(
        INVESTIGATION_PREFIX,
        headers=headers,
        json={
            "title": (
                "Generic Exception Disclosure "
                + uuid.uuid4().hex[:8]
            ),
            "description": "Security test",
        },
    )

    assert investigation_response.status_code == 201

    investigation_id = (
        investigation_response.json()["id"]
    )

    secret = (
        "INTERNAL_API_KEY=abc123 "
        "C:\\server\\private\\config.env "
        "database-password=hidden"
    )

    def fail_ai(*args, **kwargs):
        raise RuntimeError(secret)

    monkeypatch.setattr(
        InvestigationService,
        "_run_ai_investigation",
        fail_ai,
    )

    response = client.post(
        f"{INVESTIGATION_PREFIX}/"
        f"{investigation_id}/run",
        headers=headers,
        json={
            "log_file_id": log_file.id,
        },
    )

    assert response.status_code == 500

    detail = str(
        response.json().get("detail", "")
    )

    assert secret not in detail
    assert "INTERNAL_API_KEY" not in detail
    assert "config.env" not in detail
    assert "database-password" not in detail