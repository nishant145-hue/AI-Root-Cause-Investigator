from app.schemas.parsed_log import ParsedLog


def test_valid_txt(txt_parser, sample_logs_dir):
    """
    Verify TXT parser correctly parses plain text logs.
    """

    logs = txt_parser.parse(
        sample_logs_dir / "valid.txt"
    )

    assert len(logs) == 2

    assert isinstance(logs[0], ParsedLog)

    assert logs[0].message == "Application started"

    assert logs[1].message == "Database connected"
    
def test_txt_ignores_empty_lines(tmp_path, txt_parser):
    """
    TXT parser should ignore blank lines.
    """

    file = tmp_path / "empty_lines.txt"

    file.write_text(
        "Application started\n\n\nDatabase connected\n",
        encoding="utf-8",
    )

    logs = txt_parser.parse(file)

    assert len(logs) == 2