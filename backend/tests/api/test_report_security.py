from io import BytesIO

from openpyxl import load_workbook

from app.services.report_service import ReportService


def test_spreadsheet_formula_values_are_sanitized(
    db_session,
):
    service = ReportService(db_session)

    dangerous_values = [
        "=1+1",
        "+1+1",
        "-1+1",
        "@SUM(A1:A2)",
    ]

    for value in dangerous_values:
        result = service._sanitize_spreadsheet_value(
            value
        )

        assert result.startswith("'")
        assert result[1:] == value


def test_normal_spreadsheet_values_are_not_modified(
    db_session,
):
    service = ReportService(db_session)

    values = [
        "Normal title",
        "Root cause detected",
        "database",
        "API failure",
    ]

    for value in values:
        assert (
            service._sanitize_spreadsheet_value(value)
            == value
        )


def test_numeric_spreadsheet_values_are_not_modified(
    db_session,
):
    service = ReportService(db_session)

    assert service._sanitize_spreadsheet_value(123) == 123
    assert service._sanitize_spreadsheet_value(0) == 0
    assert service._sanitize_spreadsheet_value(0.95) == 0.95


def test_report_file_paths_are_unique(db_session):
    service = ReportService(db_session)

    path_a = service._create_report_path(".csv")
    path_b = service._create_report_path(".csv")

    assert path_a != path_b
    assert path_a.suffix == ".csv"
    assert path_b.suffix == ".csv"


def test_report_file_extensions_are_correct(db_session):
    service = ReportService(db_session)

    assert (
        service._create_report_path(".csv").suffix
        == ".csv"
    )

    assert (
        service._create_report_path(".xlsx").suffix
        == ".xlsx"
    )

    assert (
        service._create_report_path(".pdf").suffix
        == ".pdf"
    )