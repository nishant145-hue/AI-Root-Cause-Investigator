from pathlib import Path

import pytest

from app.services.report_service import ReportService


@pytest.fixture
def report_service(db_session):
    return ReportService(db_session)


@pytest.fixture
def test_user_id():
    """
    User ID used by the report-service unit tests.

    ReportService requires an explicit user_id so that report
    queries remain scoped to the authenticated user.
    """
    return 1


def test_get_report_data(report_service, test_user_id):
    data = report_service.get_report_data(
        user_id=test_user_id,
    )

    assert isinstance(data, list)

    if data:
        record = data[0]

        assert "id" in record
        assert "title" in record
        assert "status" in record
        assert "severity" in record
        assert "confidence" in record
        assert "root_cause" in record
        assert "failed_component" in record
        assert "created_at" in record


def test_export_csv(report_service, test_user_id):
    file_path = report_service.export_csv(
        user_id=test_user_id,
    )

    assert isinstance(file_path, Path)
    assert file_path.exists()
    assert file_path.suffix == ".csv"


def test_export_excel(report_service, test_user_id):
    file_path = report_service.export_excel(
        user_id=test_user_id,
    )

    assert isinstance(file_path, Path)
    assert file_path.exists()
    assert file_path.suffix == ".xlsx"


def test_export_pdf(report_service, test_user_id):
    file_path = report_service.export_pdf(
        user_id=test_user_id,
    )

    assert isinstance(file_path, Path)
    assert file_path.exists()
    assert file_path.suffix == ".pdf"