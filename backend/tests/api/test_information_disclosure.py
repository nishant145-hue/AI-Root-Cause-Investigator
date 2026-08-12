from uuid import uuid4


def test_invalid_access_token_does_not_expose_jwt_internals(client):
    response = client.get(
        "/api/v1/auth/profile",
        headers={
            "Authorization": "Bearer definitely-invalid-token"
        },
    )

    assert response.status_code == 401

    detail = str(response.json().get("detail", "")).lower()

    assert "traceback" not in detail
    assert "jwt" not in detail
    assert "secret" not in detail
    assert "algorithm" not in detail
    assert "signature" not in detail


def test_unauthenticated_upload_does_not_expose_internal_details(client):
    response = client.post(
        "/api/v1/uploads",
        files={
            "file": (
                "unauthorized.log",
                b"security-test",
                "text/plain",
            )
        },
    )

    assert response.status_code == 401

    detail = str(response.json().get("detail", "")).lower()

    assert "traceback" not in detail
    assert "sqlalchemy" not in detail
    assert "postgres" not in detail
    assert "database" not in detail
    assert "password" not in detail
    assert "secret_key" not in detail


def test_invalid_investigation_id_does_not_expose_database_details(
    client,
    auth_headers,
):
    response = client.get(
        "/api/v1/investigations/not-a-valid-id",
        headers=auth_headers,
    )

    assert response.status_code == 422

    detail = str(response.json().get("detail", "")).lower()

    assert "sqlalchemy" not in detail
    assert "postgres" not in detail
    assert "database" not in detail
    assert "traceback" not in detail


def test_nonexistent_investigation_does_not_expose_database_details(
    client,
    auth_headers,
):
    response = client.get(
        f"/api/v1/investigations/{999999999}",
        headers=auth_headers,
    )

    assert response.status_code in (403, 404)

    detail = str(response.json().get("detail", "")).lower()

    assert "sqlalchemy" not in detail
    assert "postgres" not in detail
    assert "database" not in detail
    assert "traceback" not in detail