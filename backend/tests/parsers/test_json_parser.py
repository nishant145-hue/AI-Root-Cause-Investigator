import pytest

from app.exceptions.parser_exceptions import ParserError


def test_valid_json(json_parser, sample_logs_dir):
    """
    Verify that a valid JSON log file is parsed correctly.
    """
    logs = json_parser.parse(
        sample_logs_dir / "valid.json"
    )

    assert len(logs) == 1

    assert logs[0].message == "Database timeout"

    assert logs[0].severity.value == "ERROR"


def test_invalid_json(json_parser, sample_logs_dir):
    """
    Verify that invalid JSON raises ParserError.
    """
    with pytest.raises(ParserError):

        json_parser.parse(
            sample_logs_dir / "invalid.json"
        )