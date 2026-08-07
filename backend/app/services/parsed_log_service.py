from uuid import UUID

from app.models.parsed_log import ParsedLog as ParsedLogModel
from app.repositories.parsed_log_repository import ParsedLogRepository
from app.schemas.parsed_log import ParsedLog as ParsedLogSchema
from sqlmodel import Session


class ParsedLogService:
    """
    Handles persistence of parsed logs.
    """

    @staticmethod
    def save_logs(
        session: Session,
        log_file_id: int,
        parsed_logs: list[ParsedLogSchema],
    ) -> list[ParsedLogModel]:

        db_logs = []

        for log in parsed_logs:

            db_logs.append(
                ParsedLogModel(
                    log_file_id=log_file_id,
                    timestamp=log.timestamp,
                    severity=log.severity.value,
                    source=log.source,
                    component=log.component,
                    message=log.message,
                    raw_line=log.raw_line,
                    log_metadata=str(log.metadata),
                )
            )

        return ParsedLogRepository.create_many(
            session=session,
            parsed_logs=db_logs,
        )
        
    @staticmethod
    def get_logs(
        session: Session,
        log_file_id: int,
    ) -> list[ParsedLogModel]:
        """
        Returns all parsed logs for a log file.
        """
        return ParsedLogRepository.get_by_log_file_id(
            session=session,
            log_file_id=log_file_id,
        )


    @staticmethod
    def get_by_log_file_id(
        session: Session,
        log_file_id: int,
    ) -> list[ParsedLogModel]:
        """
        Backward-compatible wrapper used by tests and AI services.
        """
        return ParsedLogService.get_logs(
            session=session,
            log_file_id=log_file_id,
        )
        
    