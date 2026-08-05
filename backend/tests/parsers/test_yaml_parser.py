import pytest

from app.exceptions.parser_exceptions import ParserError


def test_valid_yaml(yaml_parser, sample_logs_dir):
    """
    Verify that a valid YAML log file is parsed correctly.
    """
    logs = yaml_parser.parse(
        sample_logs_dir / "valid.yaml"
    )

    assert len(logs) == 1

    assert logs[0].message == "Database timeout"

    assert logs[0].severity.value == "ERROR"


def test_invalid_yaml(yaml_parser, sample_logs_dir):
    """
    Verify that invalid YAML raises ParserError.
    """
    with pytest.raises(ParserError):

        yaml_parser.parse(
            sample_logs_dir / "invalid.yaml"
        )