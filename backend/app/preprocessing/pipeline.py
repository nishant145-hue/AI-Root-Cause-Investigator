from app.preprocessing.cleaner import MessageCleaner
from app.preprocessing.deduplicator import Deduplicator
from app.preprocessing.severity import SeverityNormalizer
from app.preprocessing.timestamp import TimestampNormalizer
from app.schemas.parsed_log import ParsedLog


class PreprocessingPipeline:
    """
    Runs all preprocessing steps on parsed logs.
    """

    @classmethod
    def process(
        cls,
        logs: list[ParsedLog],
    ) -> list[ParsedLog]:

        processed_logs = []

        for log in logs:

            log.timestamp = TimestampNormalizer.normalize(
                log.timestamp
            )

            log.severity = SeverityNormalizer.normalize(
                log.severity
            )

            log.message = MessageCleaner.clean(
                log.message
            )

            processed_logs.append(log)

        processed_logs = Deduplicator.remove_duplicates(
            processed_logs
        )

        return processed_logs