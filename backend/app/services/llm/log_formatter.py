from app.models.parsed_log import ParsedLog


class LogFormatter:
    """Convert parsed logs into AI-ready dictionaries."""

    @staticmethod
    def format_log(log: ParsedLog) -> dict:
        return {
            "timestamp": (
                log.timestamp.isoformat()
                if log.timestamp
                else None
            ),
            "severity": log.severity,
            "source": log.source,
            "component": log.component,
            "message": log.message,
        }

    @staticmethod
    def format_logs(
        logs: list[ParsedLog],
    ) -> list[dict]:

        return [
            LogFormatter.format_log(log)
            for log in logs
        ]