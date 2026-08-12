from pathlib import Path
from uuid import uuid4

from app.models.investigation import Investigation
from app.models.log_file import LogFile
from app.models.user import User
from app.services.investigation_service import InvestigationService
from sqlmodel import Session, select

AUTH_PREFIX = "/api/v1/auth"
INVESTIGATION_PREFIX = "/api/v1/investigations"

def get_db_user(db_session, user_credentials):
    return db_session.exec(
        select(User).where(
            User.email == user_credentials["email"]
        )
    ).first()

def create_test_user(client):
    suffix = uuid4().hex[:10]

    user = {
        "username": f"owner_{suffix}",
        "email": f"owner_{suffix}@example.com",
        "password": "Password123!",
        "full_name": "Ownership Test User",
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

    data = response.json()

    assert "access_token" in data

    return data


def auth_headers(access_token):
    return {
        "Authorization": f"Bearer {access_token}"
    }


def create_investigation(client, access_token, title):
    response = client.post(
        INVESTIGATION_PREFIX,
        headers=auth_headers(access_token),
        json={
            "title": title,
            "description": "Ownership integration test investigation",
        },
    )

    assert response.status_code == 201

    return response.json()

def create_log_file(db_session, user_id: int, suffix: str):
    """
    Create a unique database-backed LogFile for ownership tests.
    """

    unique_id = uuid4().hex

    stored_filename = f"{suffix}-{unique_id}.log"

    log_file = LogFile(
        user_id=user_id,
        original_filename=f"{suffix}.log",
        stored_filename=stored_filename,
        storage_path=f"uploads/raw/{stored_filename}",
        mime_type="text/plain",
        file_size=100,
        sha256_hash=None,
        status="uploaded",
    )

    db_session.add(log_file)
    db_session.commit()
    db_session.refresh(log_file)

    return log_file

# ------------------------------------------------------------------
# Investigation list isolation
# ------------------------------------------------------------------


def test_user_cannot_see_another_users_investigation_in_list(client):
    user_a = create_test_user(client)
    user_b = create_test_user(client)

    tokens_a = login_user(client, user_a)
    tokens_b = login_user(client, user_b)

    investigation_a = create_investigation(
        client,
        tokens_a["access_token"],
        "User A Investigation",
    )

    investigation_b = create_investigation(
        client,
        tokens_b["access_token"],
        "User B Investigation",
    )

    response_a = client.get(
        INVESTIGATION_PREFIX,
        headers=auth_headers(tokens_a["access_token"]),
    )

    response_b = client.get(
        INVESTIGATION_PREFIX,
        headers=auth_headers(tokens_b["access_token"]),
    )

    assert response_a.status_code == 200
    assert response_b.status_code == 200

    ids_a = {
        item["id"]
        for item in response_a.json()["items"]
    }

    ids_b = {
        item["id"]
        for item in response_b.json()["items"]
    }

    assert investigation_a["id"] in ids_a
    assert investigation_b["id"] not in ids_a

    assert investigation_b["id"] in ids_b
    assert investigation_a["id"] not in ids_b


# ------------------------------------------------------------------
# Investigation read ownership
# ------------------------------------------------------------------


def test_user_can_read_own_investigation(client):
    user = create_test_user(client)
    tokens = login_user(client, user)

    investigation = create_investigation(
        client,
        tokens["access_token"],
        "Own Investigation",
    )

    response = client.get(
        f"{INVESTIGATION_PREFIX}/{investigation['id']}",
        headers=auth_headers(tokens["access_token"]),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == investigation["id"]
    assert data["user_id"] == investigation["user_id"]


def test_user_cannot_read_another_users_investigation(client):
    user_a = create_test_user(client)
    user_b = create_test_user(client)

    tokens_a = login_user(client, user_a)
    tokens_b = login_user(client, user_b)

    investigation_b = create_investigation(
        client,
        tokens_b["access_token"],
        "User B Private Investigation",
    )

    response = client.get(
        f"{INVESTIGATION_PREFIX}/{investigation_b['id']}",
        headers=auth_headers(tokens_a["access_token"]),
    )

    assert response.status_code in (403, 404)


# ------------------------------------------------------------------
# Investigation update ownership
# ------------------------------------------------------------------


def test_user_can_update_own_investigation(client):
    user = create_test_user(client)
    tokens = login_user(client, user)

    investigation = create_investigation(
        client,
        tokens["access_token"],
        "Original Title",
    )

    response = client.put(
        f"{INVESTIGATION_PREFIX}/{investigation['id']}",
        headers=auth_headers(tokens["access_token"]),
        json={
            "title": "Updated Title",
            "description": "Updated description",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == investigation["id"]
    assert data["title"] == "Updated Title"


def test_user_cannot_update_another_users_investigation(client):
    user_a = create_test_user(client)
    user_b = create_test_user(client)

    tokens_a = login_user(client, user_a)
    tokens_b = login_user(client, user_b)

    investigation_b = create_investigation(
        client,
        tokens_b["access_token"],
        "User B Investigation",
    )

    response = client.put(
        f"{INVESTIGATION_PREFIX}/{investigation_b['id']}",
        headers=auth_headers(tokens_a["access_token"]),
        json={
            "title": "Unauthorized Modification",
            "description": "User A must not modify User B data",
        },
    )

    assert response.status_code in (403, 404)

    # Verify the original resource was not modified.
    owner_response = client.get(
        f"{INVESTIGATION_PREFIX}/{investigation_b['id']}",
        headers=auth_headers(tokens_b["access_token"]),
    )

    assert owner_response.status_code == 200
    assert owner_response.json()["title"] == "User B Investigation"


# ------------------------------------------------------------------
# Investigation delete ownership
# ------------------------------------------------------------------


def test_user_cannot_delete_another_users_investigation(client):
    user_a = create_test_user(client)
    user_b = create_test_user(client)

    tokens_a = login_user(client, user_a)
    tokens_b = login_user(client, user_b)

    investigation_b = create_investigation(
        client,
        tokens_b["access_token"],
        "User B Protected Investigation",
    )

    response = client.delete(
        f"{INVESTIGATION_PREFIX}/{investigation_b['id']}",
        headers=auth_headers(tokens_a["access_token"]),
    )

    assert response.status_code in (403, 404)

    # Verify User B's investigation still exists.
    owner_response = client.get(
        f"{INVESTIGATION_PREFIX}/{investigation_b['id']}",
        headers=auth_headers(tokens_b["access_token"]),
    )

    assert owner_response.status_code == 200
    assert owner_response.json()["id"] == investigation_b["id"]


# ------------------------------------------------------------------
# Investigation history ownership
# ------------------------------------------------------------------


def test_user_can_access_own_investigation_history(client):
    user = create_test_user(client)
    tokens = login_user(client, user)

    investigation = create_investigation(
        client,
        tokens["access_token"],
        "History Investigation",
    )

    response = client.get(
        f"{INVESTIGATION_PREFIX}/{investigation['id']}/history",
        headers=auth_headers(tokens["access_token"]),
    )

    assert response.status_code == 200


def test_user_cannot_access_another_users_investigation_history(client):
    user_a = create_test_user(client)
    user_b = create_test_user(client)

    tokens_a = login_user(client, user_a)
    tokens_b = login_user(client, user_b)

    investigation_b = create_investigation(
        client,
        tokens_b["access_token"],
        "User B History Investigation",
    )

    response = client.get(
        f"{INVESTIGATION_PREFIX}/{investigation_b['id']}/history",
        headers=auth_headers(tokens_a["access_token"]),
    )

    assert response.status_code in (403, 404)


# ------------------------------------------------------------------
# AI investigation ownership
# ------------------------------------------------------------------


def test_user_cannot_run_ai_on_another_users_investigation(client):
    user_a = create_test_user(client)
    user_b = create_test_user(client)

    tokens_a = login_user(client, user_a)
    tokens_b = login_user(client, user_b)

    investigation_b = create_investigation(
        client,
        tokens_b["access_token"],
        "User B AI Investigation",
    )

    response = client.post(
        f"{INVESTIGATION_PREFIX}/{investigation_b['id']}/run",
        headers=auth_headers(tokens_a["access_token"]),
        json={
            "log_file_id": 999999999,
        },
    )

    # Ownership must be checked before User A can run
    # an AI investigation against User B's resource.
    assert response.status_code in (403, 404)
    
def test_user_cannot_run_ai_using_another_users_log(
    client,
    db_session,
    monkeypatch,
):
    user_a = create_test_user(client)
    user_b = create_test_user(client)

    tokens_a = login_user(client, user_a)
    tokens_b = login_user(client, user_b)

    # Get the actual authenticated user IDs.
    me_a = client.get(
        f"{AUTH_PREFIX}/me",
        headers=auth_headers(tokens_a["access_token"]),
    )

    me_b = client.get(
        f"{AUTH_PREFIX}/me",
        headers=auth_headers(tokens_b["access_token"]),
    )

    assert me_a.status_code == 200
    assert me_b.status_code == 200

    user_a_id = me_a.json()["id"]
    user_b_id = me_b.json()["id"]

    investigation_a = create_investigation(
        client,
        tokens_a["access_token"],
        "User A Investigation With Log Ownership Test",
    )

    user_b_db = get_db_user(
        db_session,
        user_b,
    )

    assert user_b_db is not None

    log_b = create_log_file(
        db_session,
        user_id=user_b_db.id,
        suffix="cross-resource-user-b",
    )

    # If ownership is correctly enforced, _run_ai_investigation
    # must never be reached.
    def fail_if_ai_is_called(*args, **kwargs):
        raise AssertionError(
            "AI investigation was executed with another user's log file."
        )

    from app.services.investigation_service import InvestigationService

    monkeypatch.setattr(
        InvestigationService,
        "_run_ai_investigation",
        fail_if_ai_is_called,
    )

    response = client.post(
        f"{INVESTIGATION_PREFIX}/{investigation_a['id']}/run",
        headers=auth_headers(tokens_a["access_token"]),
        json={
            "log_file_id": log_b.id,
        },
    )

    assert response.status_code in (403, 404)
    
def test_user_cannot_run_ai_using_another_users_log_without_side_effects(
    client,
    db_session,
):
    user_a = create_test_user(client)
    user_b = create_test_user(client)

    tokens_a = login_user(client, user_a)
    tokens_b = login_user(client, user_b)

    headers_a = {
        "Authorization": f"Bearer {tokens_a['access_token']}"
    }

    headers_b = {
        "Authorization": f"Bearer {tokens_b['access_token']}"
    }

    investigation_response = client.post(
        f"{INVESTIGATION_PREFIX}",
        headers=headers_a,
        json={
            "title": "Cross Resource Security Test",
            "description": "User A investigation",
        },
    )

    assert investigation_response.status_code == 201

    investigation = investigation_response.json()

    user_b_db = get_db_user(
        db_session,
        user_b,
    )

    assert user_b_db is not None

    log_b = create_log_file(
        db_session,
        user_id=user_b_db.id,
        suffix="user-b-private-log",
    )
    investigation_id = investigation["id"]

    before = db_session.get(
        Investigation,
        investigation_id,
    )

    before_status = before.status
    before_summary = before.summary
    before_root_cause = before.root_cause

    response = client.post(
        f"{INVESTIGATION_PREFIX}/{investigation_id}/run",
        headers=headers_a,
        json={
            "log_file_id": log_b.id,
        },
    )

    assert response.status_code == 404

    db_session.expire_all()

    after = db_session.get(
        Investigation,
        investigation_id,
    )

    assert after.status == before_status
    assert after.summary == before_summary
    assert after.root_cause == before_root_cause
    
def test_unauthorized_ai_run_does_not_create_notification(
    client,
    db_session,
):
    user_a = create_test_user(client)
    user_b = create_test_user(client)

    tokens_a = login_user(client, user_a)
    tokens_b = login_user(client, user_b)

    headers_a = auth_headers(tokens_a["access_token"])
    headers_b = auth_headers(tokens_b["access_token"])

    # User A creates an investigation.
    investigation_response = client.post(
        "/api/v1/investigations",
        headers=headers_a,
        json={
            "title": "Cross Resource Notification Test",
            "description": "User A investigation",
        },
    )

    assert investigation_response.status_code == 201

    investigation_id = investigation_response.json()["id"]

    # User B's log.
    user_b_db = get_db_user(
        db_session,
        user_b,
    )

    assert user_b_db is not None

    log_b = create_log_file(
        db_session,
        user_id=user_b_db.id,
        suffix="notification-cross-resource",
    )

    # Capture User A notifications before the unauthorized operation.
    before = client.get(
        "/api/v1/notifications",
        headers=headers_a,
    )

    assert before.status_code == 200

    before_ids = {
        item["id"]
        for item in before.json()
    }

    # User A attempts to run AI using User B's log.
    response = client.post(
        f"/api/v1/investigations/{investigation_id}/run",
        headers=headers_a,
        json={
            "log_file_id": log_b.id,
        },
    )

    assert response.status_code == 404

    # Verify that no notification was created for User A.
    after = client.get(
        "/api/v1/notifications",
        headers=headers_a,
    )

    assert after.status_code == 200

    after_ids = {
        item["id"]
        for item in after.json()
    }

    assert after_ids == before_ids