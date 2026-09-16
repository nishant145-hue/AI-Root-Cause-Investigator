from app.models.investigation import Investigation
from sqlmodel import Session

from tests.api.test_authorization_ownership import (
    INVESTIGATION_PREFIX,
    auth_headers,
    create_investigation,
    create_test_user,
    login_user,
)


def test_analytics_dashboard_returns_critical_path(
    client,
    db_session: Session,
):
    user = create_test_user(client)
    tokens = login_user(client, user)

    investigation = create_investigation(
        client,
        tokens["access_token"],
        "Critical Path Analytics Test",
    )

    db_investigation = db_session.get(
        Investigation,
        investigation["id"],
    )

    assert db_investigation is not None

    db_investigation.execution_analytics = {
        "execution": {
            "total_executions": 3,
            "successful_executions": 3,
            "failed_executions": 0,
            "total_duration_ms": 150.0,
            "retry_count": 0,
        },
        "agent_performance": {},
        "bottlenecks": [],
        "failure_retry": {
            "total_failures": 0,
            "total_retries": 0,
            "failures_by_agent": {},
            "retries_by_agent": {},
        },
        "efficiency": {
            "score": 100.0,
            "success_rate": 1.0,
            "failure_rate": 0.0,
            "bottleneck_count": 0,
        },
        "critical_path": {
            "critical_path_ms": 125.50,
            "executions": [
                "execution-root",
                "execution-child",
            ],
        },
    }

    db_session.add(db_investigation)
    db_session.commit()

    response = client.get(
        f"{INVESTIGATION_PREFIX}/"
        f"{investigation['id']}/analytics/dashboard",
        headers=auth_headers(
            tokens["access_token"]
        ),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["investigation_id"] == investigation["id"]

    assert data["critical_path"]["critical_path_ms"] == 125.50
    assert data["critical_path"]["executions"] == [
        "execution-root",
        "execution-child",
    ]

def test_user_cannot_access_another_users_analytics_dashboard(client):
    user_a = create_test_user(client)
    user_b = create_test_user(client)

    tokens_a = login_user(client, user_a)
    tokens_b = login_user(client, user_b)

    investigation_a = create_investigation(
        client,
        tokens_a["access_token"],
        "Private Analytics Investigation",
    )

    response = client.get(
        f"{INVESTIGATION_PREFIX}/"
        f"{investigation_a['id']}/analytics/dashboard",
        headers=auth_headers(
            tokens_b["access_token"]
        ),
    )

    assert response.status_code in (403, 404)
