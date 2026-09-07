from app.models.investigation import Investigation


def test_investigation_analytics_returns_persisted_data(
    client,
    db_session,
    test_user,
    auth_headers,
):
    investigation = Investigation(
        title="Analytics Test",
        description="Test investigation",
        user_id=test_user.id,
        execution_analytics={
            "execution": {
                "total_executions": 5,
                "successful_executions": 4,
                "failed_executions": 1,
            },
            "failure_retry": {
                "retry_count": 1,
            },
            "bottlenecks": [
                "investigator",
            ],
        },
    )

    db_session.add(investigation)
    db_session.commit()
    db_session.refresh(investigation)

    response = client.get(
        f"/api/v1/investigations/"
        f"{investigation.id}/analytics",
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["investigation_id"] == investigation.id

    assert (
        data["analytics"]["execution"][
            "total_executions"
        ]
        == 5
    )

    assert (
        data["analytics"]["failure_retry"][
            "retry_count"
        ]
        == 1
    )

def test_investigation_analytics_dashboard(
    client,
    db_session,
    test_user,
    auth_headers,
):
    investigation = Investigation(
        title="Dashboard Analytics Test",
        description="Dashboard test",
        user_id=test_user.id,
        execution_analytics={
            "timeline": [
                {
                    "agent": "investigator",
                    "action": "search_logs",
                    "status": "COMPLETED",
                    "duration_ms": 100.0,
                    "attempt": 1,
                },
                {
                    "agent": "reasoner",
                    "action": "generate_hypothesis",
                    "status": "COMPLETED",
                    "duration_ms": 200.0,
                    "attempt": 1,
                },
                {
                    "agent": "validator",
                    "action": "validate",
                    "status": "FAILED",
                    "duration_ms": 50.0,
                    "attempt": 2,
                },
            ],
        },
    )

    db_session.add(investigation)
    db_session.commit()
    db_session.refresh(investigation)

    response = client.get(
        f"/api/v1/investigations/"
        f"{investigation.id}/analytics/dashboard",
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert (
        data["investigation_id"]
        == investigation.id
    )

    assert (
        data["overview"]["total_executions"]
        == 3
    )

    assert (
        data["overview"]["successful_executions"]
        == 2
    )

    assert (
        data["overview"]["failed_executions"]
        == 1
    )

    assert (
        data["overview"]["total_duration_ms"]
        == 350.0
    )

    assert (
        data["overview"]["retry_count"]
        == 1
    )

    assert (
        len(data["agent_performance"])
        == 3
    )

    assert (
        len(data["timeline"])
        == 3
    )

def test_investigation_analytics_dashboard_requires_auth(
    client,
    db_session,
    test_user,
):
    investigation = Investigation(
        title="Dashboard Auth Test",
        description="Authentication test",
        user_id=test_user.id,
    )

    db_session.add(investigation)
    db_session.commit()
    db_session.refresh(investigation)

    response = client.get(
        f"/api/v1/investigations/"
        f"{investigation.id}/analytics/dashboard"
    )

    assert response.status_code == 401

def test_user_cannot_access_another_users_dashboard(
    client,
    db_session,
):
    from uuid import uuid4

    def create_user():
        suffix = uuid4().hex[:10]

        user = {
            "username": f"dashboard_{suffix}",
            "email": f"dashboard_{suffix}@example.com",
            "password": "Password123!",
            "full_name": "Dashboard User",
        }

        response = client.post(
            "/api/v1/auth/register",
            json=user,
        )

        assert response.status_code == 201

        login = client.post(
            "/api/v1/auth/login",
            data={
                "username": user["email"],
                "password": user["password"],
            },
        )

        assert login.status_code == 200

        return user, login.json()["access_token"]

    user_a, token_a = create_user()
    user_b, token_b = create_user()

    me_b = client.get(
        "/api/v1/auth/me",
        headers={
            "Authorization": f"Bearer {token_b}"
        },
    )

    assert me_b.status_code == 200

    investigation = Investigation(
        title="Private Dashboard",
        description="Private analytics",
        user_id=me_b.json()["id"],
        execution_analytics={
            "timeline": [],
        },
    )

    db_session.add(investigation)
    db_session.commit()
    db_session.refresh(investigation)

    response = client.get(
        f"/api/v1/investigations/"
        f"{investigation.id}/analytics/dashboard",
        headers={
            "Authorization": f"Bearer {token_a}"
        },
    )

    assert response.status_code in (403, 404)

def test_dashboard_handles_missing_analytics(
    client,
    db_session,
    test_user,
    auth_headers,
):
    investigation = Investigation(
        title="Empty Dashboard Analytics",
        description="No analytics yet",
        user_id=test_user.id,
        execution_analytics=None,
    )

    db_session.add(investigation)
    db_session.commit()
    db_session.refresh(investigation)

    response = client.get(
        f"/api/v1/investigations/"
        f"{investigation.id}/analytics/dashboard",
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert (
        data["investigation_id"]
        == investigation.id
    )

    assert (
        data["overview"]["total_executions"]
        == 0
    )

    assert data["agent_performance"] == []

    assert data["bottlenecks"] == []

    assert data["timeline"] == []
