import pytest

from app.exceptions.parser_exceptions import ParserError
from app.services.log_processing_service import LogProcessingService
from app.schemas.parsed_log import ParsedLog

def test_process_valid_json(sample_logs_dir):
    """
    LogProcessingService should process a valid JSON file.
    """

    logs = LogProcessingService.process(
        sample_logs_dir / "valid.json"
    )

    assert len(logs) == 1

    assert isinstance(logs[0], ParsedLog)

    assert logs[0].message == "Database timeout"

    assert logs[0].severity.value == "ERROR"
    
def test_process_valid_txt(sample_logs_dir):
    """
    LogProcessingService should process a TXT file.
    """

    logs = LogProcessingService.process(
        sample_logs_dir / "valid.txt"
    )

    assert len(logs) == 2

    assert logs[0].message == "Application started"

    assert logs[1].message == "Database connected"
    
def test_process_invalid_json(sample_logs_dir):
    """
    Invalid JSON should raise ParserError.
    """

    with pytest.raises(ParserError):

        LogProcessingService.process(
            sample_logs_dir / "invalid.json"
        )
        
def test_process_invalid_yaml(sample_logs_dir):
    """
    Invalid YAML should raise ParserError.
    """

    with pytest.raises(ParserError):

        LogProcessingService.process(
            sample_logs_dir / "invalid.yaml"
        )
        
def test_message_cleaning(tmp_path):
    """
    Verify preprocessing cleans message whitespace.
    """

    file = tmp_path / "dirty.txt"

    file.write_text(
        "   Database      timeout   ",
        encoding="utf-8",
    )

    logs = LogProcessingService.process(file)

    assert logs[0].message == "Database timeout"
    
def test_duplicate_removal(tmp_path):
    """
    Duplicate log messages should be removed.
    """

    file = tmp_path / "duplicate.txt"

    file.write_text(
        "Database timeout\n"
        "Database timeout\n"
        "Database timeout\n",
        encoding="utf-8",
    )

    logs = LogProcessingService.process(file)

    assert len(logs) == 1