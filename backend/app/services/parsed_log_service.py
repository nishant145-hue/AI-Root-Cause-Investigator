from uuid import UUID

from sqlmodel import Session

from app.models.parsed_log import ParsedLog as ParsedLogModel
from app.repositories.parsed_log_repository import ParsedLogRepository
from app.schemas.parsed_log import ParsedLog as ParsedLogSchema


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