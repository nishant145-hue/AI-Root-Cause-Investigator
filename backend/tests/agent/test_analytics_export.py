from uuid import uuid4


AUTH_PREFIX = "/api/v1/auth"


def create_test_user(client):
    suffix = uuid4().hex[:10]

    user = {
        "username": f"analytics_export_{suffix}",
        "email": f"analytics_export_{suffix}@example.com",
        "password": "Password123!",
        "full_name": "Analytics Export User",
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


def auth_headers(token):
    return {
        "Authorization": f"Bearer {token}"
    }


def create_investigation(
    client,
    token,
):
    response = client.post(
        "/api/v1/investigations",
        headers=auth_headers(token),
        json={
            "title": "Analytics Export Test",
            "description": "Export test",
        },
    )

    assert response.status_code == 201

    return response.json()


def test_json_export_requires_authentication(client):
    response = client.get(
        "/api/v1/investigations/1/"
        "analytics/export/json"
    )

    assert response.status_code == 401


def test_csv_export_requires_authentication(client):
    response = client.get(
        "/api/v1/investigations/1/"
        "analytics/export/csv"
    )

    assert response.status_code == 401


def test_excel_export_requires_authentication(client):
    response = client.get(
        "/api/v1/investigations/1/"
        "analytics/export/excel"
    )

    assert response.status_code == 401


def test_pdf_export_requires_authentication(client):
    response = client.get(
        "/api/v1/investigations/1/"
        "analytics/export/pdf"
    )

    assert response.status_code == 401


def test_json_analytics_export(client):
    user = create_test_user(client)

    tokens = login_user(
        client,
        user,
    )

    investigation = create_investigation(
        client,
        tokens["access_token"],
    )

    response = client.get(
        f"/api/v1/investigations/"
        f"{investigation['id']}/"
        f"analytics/export/json",
        headers=auth_headers(
            tokens["access_token"]
        ),
    )

    assert response.status_code == 200

    data = response.json()

    assert (
        data["investigation_id"]
        == investigation["id"]
    )


def test_csv_analytics_export(client):
    user = create_test_user(client)

    tokens = login_user(
        client,
        user,
    )

    investigation = create_investigation(
        client,
        tokens["access_token"],
    )

    response = client.get(
        f"/api/v1/investigations/"
        f"{investigation['id']}/"
        f"analytics/export/csv",
        headers=auth_headers(
            tokens["access_token"]
        ),
    )

    assert response.status_code == 200

    assert response.headers[
        "content-type"
    ].startswith("text/csv")

    assert len(response.content) > 0


def test_excel_analytics_export(client):
    user = create_test_user(client)

    tokens = login_user(
        client,
        user,
    )

    investigation = create_investigation(
        client,
        tokens["access_token"],
    )

    response = client.get(
        f"/api/v1/investigations/"
        f"{investigation['id']}/"
        f"analytics/export/excel",
        headers=auth_headers(
            tokens["access_token"]
        ),
    )

    assert response.status_code == 200

    assert response.headers[
        "content-type"
    ].startswith(
        "application/vnd.openxmlformats-officedocument"
    )

    assert len(response.content) > 0


def test_pdf_analytics_export(client):
    user = create_test_user(client)

    tokens = login_user(
        client,
        user,
    )

    investigation = create_investigation(
        client,
        tokens["access_token"],
    )

    response = client.get(
        f"/api/v1/investigations/"
        f"{investigation['id']}/"
        f"analytics/export/pdf",
        headers=auth_headers(
            tokens["access_token"]
        ),
    )

    assert response.status_code == 200

    assert response.headers[
        "content-type"
    ].startswith("application/pdf")

    assert len(response.content) > 0
