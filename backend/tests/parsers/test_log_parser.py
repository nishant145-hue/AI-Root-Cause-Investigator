from app.schemas.parsed_log import ParsedLog


def test_valid_log(log_parser, sample_logs_dir):
    """
    Verify LOG parser correctly parses log files.
    """

    logs = log_parser.parse(
        sample_logs_dir / "valid.log"
    )

    assert len(logs) == 2

    assert isinstance(logs[0], ParsedLog)

    assert logs[0].message == "INFO Application started"

    assert logs[1].message == "ERROR Database timeout"
    
def test_log_ignores_empty_lines(tmp_path, log_parser):
    """
    LOG parser should ignore blank lines.
    """

    file = tmp_path / "sample.log"

    file.write_text(
        "INFO Started\n\nERROR Failed\n",
        encoding="utf-8",
    )

    logs = log_parser.parse(file)

    assert len(logs) == 2