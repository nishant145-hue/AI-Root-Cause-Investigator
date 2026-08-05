import logging
from pathlib import Path

from app.exceptions.parser_exceptions import ParserError
from app.parsers.parser_factory import ParserFactory
from app.preprocessing.pipeline import PreprocessingPipeline
from app.schemas.parsed_log import ParsedLog

logger = logging.getLogger(__name__)


class LogProcessingService:
    """
    Handles log parsing and preprocessing.
    """
    @staticmethod
    def process(file_path: str | Path) -> list[ParsedLog]:

        file_path = Path(file_path)

        parser = ParserFactory.get_parser(file_path.name)

        try:
            parsed_logs = parser.parse(str(file_path))

        except ParserError:
            logger.exception(
                "Parser failed while processing %s",
                file_path.name,
            )
            raise

        try:
            processed_logs = PreprocessingPipeline.process(
                parsed_logs
            )

        except Exception:
            logger.exception(
                "Preprocessing failed for %s",
                file_path.name,
            )
            raise

        logger.info(
            "Processed %d log entries using %s",
            len(processed_logs),
            parser.__class__.__name__,
        )

        return processed_logs