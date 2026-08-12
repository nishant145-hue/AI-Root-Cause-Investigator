import pytest

from app.services.dashboard_service import DashboardService


@pytest.fixture
def dashboard_service(db_session):
    return DashboardService(db_session)


def test_dashboard_overview(
    dashboard_service,
    test_user,
):
    overview = dashboard_service.get_overview(test_user.id)

    assert isinstance(overview, dict)

    assert "total_investigations" in overview
    assert "average_confidence" in overview
    assert "resolved" in overview
    assert "pending" in overview


def test_recent_investigations(
    dashboard_service,
    test_user,
):
    investigations = (
        dashboard_service.get_recent_investigations(
            test_user.id
        )
    )

    assert isinstance(investigations, list)


def test_timeline(
    dashboard_service,
    test_user,
):
    timeline = dashboard_service.get_timeline(
        test_user.id
    )

    assert isinstance(timeline, list)


def test_severity_distribution(
    dashboard_service,
    test_user,
):
    severity = (
        dashboard_service.get_severity_distribution(
            test_user.id
        )
    )

    assert isinstance(severity, list)


def test_root_cause_distribution(
    dashboard_service,
    test_user,
):
    causes = (
        dashboard_service.get_root_cause_distribution(
            test_user.id
        )
    )

    assert isinstance(causes, list)

def test_failed_component_distribution(
    dashboard_service,
    test_user,
):
    components = (
        dashboard_service.get_failed_component_distribution(
            test_user.id
        )
    )

    assert isinstance(components, list)


def test_confidence_analytics(
    dashboard_service,
    test_user,
):
    analytics = (
        dashboard_service.get_confidence_analytics(
            test_user.id
        )
    )

    assert isinstance(analytics, dict)