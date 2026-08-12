from app.notifications.template_renderer import (
    NotificationTemplateRenderer,
)


def test_render_critical_alert():
    renderer = NotificationTemplateRenderer()

    result = renderer.render(
        "critical_alert.html",
        subject="Database Failure",
        severity="critical",
        system_name="Production API",
        root_cause="Connection pool exhausted",
        confidence=96,
        message="Database connections exceeded the configured limit.",
        recommendation="Increase the connection pool and investigate connection leaks.",
    )

    assert "Critical Incident Detected" in result
    assert "Database Failure" in result
    assert "Production API" in result
    assert "96" in result


def test_render_investigation_completed():
    renderer = NotificationTemplateRenderer()

    result = renderer.render(
        "investigation_completed.html",
        subject="API Investigation",
        root_cause="Database timeout",
        confidence=92,
        recommendation="Investigate slow database queries.",
    )

    assert "Investigation Completed" in result
    assert "API Investigation" in result
    assert "Database timeout" in result


def test_render_report_ready():
    renderer = NotificationTemplateRenderer()

    result = renderer.render(
        "report_ready.html",
        subject="Investigation Report",
        investigation_id=123,
    )

    assert "Investigation Report Ready" in result
    assert "123" in result


def test_render_daily_summary():
    renderer = NotificationTemplateRenderer()

    result = renderer.render(
        "daily_summary.html",
        investigations_count=10,
        critical_alerts=2,
        average_confidence=91,
        average_resolution_time="18 minutes",
        top_root_causes=[
            "Database timeout",
            "API dependency failure",
        ],
    )

    assert "Daily Investigation Summary" in result
    assert "10" in result
    assert "Database timeout" in result