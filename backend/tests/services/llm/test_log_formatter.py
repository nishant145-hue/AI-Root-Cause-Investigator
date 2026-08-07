from datetime import datetime

from app.models.parsed_log import ParsedLog
from app.services.llm.log_formatter import LogFormatter


def make_log():
    return ParsedLog(
        log_file_id=1,
        timestamp=datetime(2026, 8, 6, 10, 0, 0),
        severity="ERROR",
        source="Database",
        component="ConnectionPool",
        message="Connection pool exhausted.",
        raw_line="Connection pool exhausted.",
        log_metadata="{}",
    )


def test_format_logs_success():
    logs = [make_log()]

    formatted = LogFormatter.format_logs(logs)

    assert isinstance(formatted, list)
    assert len(formatted) == 1
    assert isinstance(formatted[0], dict)


def test_empty_logs():
    formatted = LogFormatter.format_logs([])

    assert formatted == []


def test_multiple_logs():
    logs = [
        make_log(),
        make_log(),
    ]

    formatted = LogFormatter.format_logs(logs)

    assert len(formatted) == 2


def test_log_contains_all_fields():
    formatted = LogFormatter.format_logs([make_log()])

    log = formatted[0]

    assert log["timestamp"] == "2026-08-06T10:00:00"
    assert log["severity"] == "ERROR"
    assert log["source"] == "Database"
    assert log["component"] == "ConnectionPool"
    assert log["message"] == "Connection pool exhausted."


def test_formatter_is_deterministic():
    logs = [make_log()]

    output1 = LogFormatter.format_logs(logs)
    output2 = LogFormatter.format_logs(logs)

    assert output1 == output2