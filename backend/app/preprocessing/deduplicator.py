from app.schemas.parsed_log import ParsedLog


class Deduplicator:
    """
    Removes duplicate ParsedLog entries while preserving order.
    """

    @staticmethod
    def remove_duplicates(logs: list[ParsedLog]) -> list[ParsedLog]:

        seen = set()
        unique_logs = []

        for log in logs:

            key = (
                log.timestamp.isoformat() if log.timestamp else None,
                log.severity.value,
                log.message.lower(),
            )

            if key not in seen:
                seen.add(key)
                unique_logs.append(log)

        return unique_logs