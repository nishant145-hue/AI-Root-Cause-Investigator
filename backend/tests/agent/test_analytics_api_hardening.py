from app.models.investigation import Investigation
from app.services.analytics_validation_service import (
    AnalyticsValidationService,
)


def test_dashboard_handles_none_analytics(
    client,
    db_session,
    test_user,
    auth_headers,
):
    investigation = Investigation(
        title="No Analytics",
        description="Missing analytics test",
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

    assert data["investigation_id"] == investigation.id
    assert data["overview"]["total_executions"] == 0
    assert data["agent_performance"] == []
    assert data["bottlenecks"] == []
    assert data["timeline"] == []


def test_dashboard_handles_malformed_analytics(
    client,
    db_session,
    test_user,
    auth_headers,
):
    investigation = Investigation(
        title="Malformed Analytics",
        description="Malformed analytics test",
        user_id=test_user.id,
        execution_analytics={
            "overview": None,
            "agent_performance": "invalid",
            "bottlenecks": None,
            "failure_retry_metrics": None,
            "timeline": "invalid",
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

    assert data["investigation_id"] == investigation.id
    assert data["overview"]["total_executions"] == 0
    assert data["agent_performance"] == []
    assert data["bottlenecks"] == []
    assert data["timeline"] == []


def test_dashboard_rejects_unauthenticated_request(
    client,
    db_session,
    test_user,
):
    investigation = Investigation(
        title="Protected Analytics",
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


def test_dashboard_returns_not_found_for_missing_investigation(
    client,
    auth_headers,
):
    response = client.get(
        "/api/v1/investigations/999999999/analytics/dashboard",
        headers=auth_headers,
    )

    assert response.status_code == 404
