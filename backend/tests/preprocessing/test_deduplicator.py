from app.enums.severity import SeverityLevel
from app.preprocessing.deduplicator import Deduplicator
from app.schemas.parsed_log import ParsedLog

logs = [
    ParsedLog(
        severity=SeverityLevel.INFO,
        message="Server Started",
    ),
    ParsedLog(
        severity=SeverityLevel.ERROR,
        message="Database Timeout",
    ),
    ParsedLog(
        severity=SeverityLevel.INFO,
        message="Server Started",
    ),
    ParsedLog(
        severity=SeverityLevel.WARNING,
        message="Disk Usage High",
    ),
    ParsedLog(
        severity=SeverityLevel.ERROR,
        message="Database Timeout",
    ),
]

print("Before:", len(logs))

clean_logs = Deduplicator.remove_duplicates(logs)

print("After:", len(clean_logs))
print()

for log in clean_logs:
    print(log)