from app.enums.severity import SeverityLevel
from app.preprocessing.pipeline import PreprocessingPipeline
from app.schemas.parsed_log import ParsedLog

logs = [
    ParsedLog(
        timestamp="2026-08-04T10:10:10",
        severity=SeverityLevel.ERROR,
        message="  Database    Timeout ",
        raw_line="  Database    Timeout ",
    ),
    ParsedLog(
        timestamp="2026-08-04T10:10:10",
        severity=SeverityLevel.ERROR,
        message="Database Timeout",
        raw_line="Database Timeout",
    ),
    ParsedLog(
        timestamp="2026-08-04T10:20:10",
        severity=SeverityLevel.WARNING,
        message=" Disk   Usage   High ",
        raw_line=" Disk   Usage   High ",
    ),
]

print("Before:", len(logs))

logs = PreprocessingPipeline.process(logs)

print("After:", len(logs))

for log in logs:
    print(log)