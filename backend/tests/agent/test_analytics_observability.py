from app.core.metrics import MetricsCollector


def test_analytics_dashboard_metrics():
    metrics = MetricsCollector()

    metrics.record_analytics_dashboard_request(
        success=True,
        duration_ms=100.0,
    )

    metrics.record_analytics_dashboard_request(
        success=False,
        duration_ms=200.0,
    )

    snapshot = metrics.snapshot()

    dashboard = snapshot["analytics"]["dashboard"]

    assert dashboard["requests"] == 2
    assert dashboard["successes"] == 1
    assert dashboard["failures"] == 1

    assert dashboard["duration_ms"]["average"] == 150.0
    assert dashboard["duration_ms"]["maximum"] == 200.0


def test_analytics_validation_metrics():
    metrics = MetricsCollector()

    metrics.record_analytics_validation(
        status="success",
    )

    metrics.record_analytics_validation(
        status="normalized",
    )

    metrics.record_analytics_validation(
        status="failure",
    )

    snapshot = metrics.snapshot()

    validation = snapshot["analytics"]["validation"]

    assert validation["requests"] == 3
    assert validation["successes"] == 1
    assert validation["normalized"] == 1
    assert validation["failures"] == 1


def test_analytics_export_metrics():
    metrics = MetricsCollector()

    metrics.record_analytics_export(
        export_format="pdf",
        success=True,
        duration_ms=250.0,
    )

    metrics.record_analytics_export(
        export_format="pdf",
        success=False,
        duration_ms=350.0,
    )

    snapshot = metrics.snapshot()

    pdf = snapshot["analytics"]["exports"]["pdf"]

    assert pdf["requests"] == 2
    assert pdf["successes"] == 1
    assert pdf["failures"] == 1

    assert pdf["duration_ms"]["average"] == 300.0
    assert pdf["duration_ms"]["maximum"] == 350.0


def test_analytics_metrics_reset():
    metrics = MetricsCollector()

    metrics.record_analytics_dashboard_request(
        success=True,
        duration_ms=100.0,
    )

    metrics.record_analytics_validation(
        status="normalized",
    )

    metrics.record_analytics_export(
        export_format="csv",
        success=True,
        duration_ms=50.0,
    )

    metrics.reset()

    snapshot = metrics.snapshot()

    assert (
        snapshot["analytics"]["dashboard"]["requests"]
        == 0
    )

    assert (
        snapshot["analytics"]["validation"]["requests"]
        == 0
    )

    assert (
        snapshot["analytics"]["exports"]
        == {}
    )


def test_analytics_metrics_do_not_use_investigation_id():
    metrics = MetricsCollector()

    metrics.record_analytics_dashboard_request(
        success=True,
        duration_ms=100.0,
    )

    snapshot = metrics.snapshot()

    assert "investigation_id" not in str(
        snapshot["analytics"]
    )

def test_dashboard_api_records_metrics(
    client,
    db_session,
    test_user,
    auth_headers,
):
    from app.core.metrics import metrics
    from app.models.investigation import Investigation

    metrics.reset()

    investigation = Investigation(
        title="Observability Dashboard Test",
        description="Dashboard metrics test",
        user_id=test_user.id,
        execution_analytics={
            "overview": {
                "total_executions": 1,
                "successful_executions": 1,
                "failed_executions": 0,
            },
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

    snapshot = metrics.snapshot()

    dashboard = snapshot[
        "analytics"
    ][
        "dashboard"
    ]

    assert dashboard["requests"] == 1
    assert dashboard["successes"] == 1
    assert dashboard["failures"] == 0
    assert dashboard["duration_ms"]["maximum"] >= 0

def test_dashboard_api_records_failure_metric(
    client,
    auth_headers,
):
    from app.core.metrics import metrics

    metrics.reset()

    response = client.get(
        "/api/v1/investigations/999999999/"
        "analytics/dashboard",
        headers=auth_headers,
    )

    assert response.status_code == 404

    snapshot = metrics.snapshot()

    dashboard = snapshot[
        "analytics"
    ][
        "dashboard"
    ]

    assert dashboard["requests"] == 1
    assert dashboard["successes"] == 0
    assert dashboard["failures"] == 1
