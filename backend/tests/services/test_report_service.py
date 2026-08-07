from pathlib import Path

import pytest
from app.services.report_service import ReportService


@pytest.fixture
def report_service(db_session):
    return ReportService(db_session)


def test_get_report_data(report_service):
    data = report_service.get_report_data()

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
        
def test_export_csv(report_service):
        file_path = report_service.export_csv()

        assert isinstance(file_path, Path)

        assert file_path.exists()

        assert file_path.suffix == ".csv"
        
def test_export_excel(report_service):
    file_path = report_service.export_excel()

    assert isinstance(file_path, Path)
    assert file_path.exists()
    assert file_path.suffix == ".xlsx"
    
def test_export_pdf(report_service):
    file_path = report_service.export_pdf()

    assert file_path.exists()
    assert file_path.suffix == ".pdf"