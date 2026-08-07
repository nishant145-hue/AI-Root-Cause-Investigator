import pytest

from app.repositories.dashboard_repository import DashboardRepository


@pytest.fixture
def dashboard_repository(db_session):
    return DashboardRepository(db_session)


def test_get_total_investigations(dashboard_repository):
    result = dashboard_repository.get_total_investigations()

    assert isinstance(result, int)
    assert result >= 0


def test_get_average_confidence(dashboard_repository):
    result = dashboard_repository.get_average_confidence()

    assert isinstance(result, float)
    assert 0 <= result <= 1


def test_get_recent_investigations(dashboard_repository):
    investigations = dashboard_repository.get_recent_investigations()

    assert isinstance(investigations, list)

    if investigations:
        assert hasattr(investigations[0], "title")
        assert hasattr(investigations[0], "status")


def test_get_timeline(dashboard_repository):
    timeline = dashboard_repository.get_timeline()

    assert isinstance(timeline, list)

    for item in timeline:
        assert "date" in item
        assert "count" in item


def test_get_severity_distribution(dashboard_repository):
    severity = dashboard_repository.get_severity_distribution()

    assert isinstance(severity, list)

    for item in severity:
        assert "severity" in item
        assert "count" in item


def test_get_root_cause_distribution(dashboard_repository):
    causes = dashboard_repository.get_root_cause_distribution()

    assert isinstance(causes, list)

    for item in causes:
        assert "root_cause" in item
        assert "count" in item


def test_get_failed_component_distribution(dashboard_repository):
    components = dashboard_repository.get_failed_component_distribution()

    assert isinstance(components, list)

    for item in components:
        assert "component" in item
        assert "count" in item


def test_get_confidence_analytics(dashboard_repository):
    analytics = dashboard_repository.get_confidence_analytics()

    assert isinstance(analytics, dict)

    assert "average_confidence" in analytics
    assert "minimum_confidence" in analytics
    assert "maximum_confidence" in analytics
    assert "high_confidence" in analytics
    assert "medium_confidence" in analytics
    assert "low_confidence" in analytics