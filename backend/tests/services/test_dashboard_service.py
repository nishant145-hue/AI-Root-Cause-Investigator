import pytest

from app.services.dashboard_service import DashboardService


@pytest.fixture
def dashboard_service(db_session):
    return DashboardService(db_session)


def test_dashboard_overview(dashboard_service):
    overview = dashboard_service.get_overview()

    assert isinstance(overview, dict)

    assert "total_investigations" in overview
    assert "average_confidence" in overview
    assert "resolved" in overview
    assert "pending" in overview


def test_recent_investigations(dashboard_service):
    investigations = dashboard_service.get_recent_investigations()

    assert isinstance(investigations, list)


def test_timeline(dashboard_service):
    timeline = dashboard_service.get_timeline()

    assert isinstance(timeline, list)


def test_severity_distribution(dashboard_service):
    severity = dashboard_service.get_severity_distribution()

    assert isinstance(severity, list)


def test_root_cause_distribution(dashboard_service):
    causes = dashboard_service.get_root_cause_distribution()

    assert isinstance(causes, list)


def test_failed_component_distribution(dashboard_service):
    components = dashboard_service.get_failed_component_distribution()

    assert isinstance(components, list)


def test_confidence_analytics(dashboard_service):
    analytics = dashboard_service.get_confidence_analytics()

    assert isinstance(analytics, dict)

    assert "average_confidence" in analytics