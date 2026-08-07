from sqlmodel import Session, select

from app.models.parsed_log import ParsedLog


class ParsedLogRepository:
    """
    Handles database operations for ParsedLog.
    """

    @staticmethod
    def create(
        session: Session,
        parsed_log: ParsedLog,
    ) -> ParsedLog:

        session.add(parsed_log)
        session.commit()
        session.refresh(parsed_log)

        return parsed_log

    @staticmethod
    def create_many(
        session: Session,
        parsed_logs: list[ParsedLog],
    ) -> list[ParsedLog]:

        if not parsed_logs:
            return []

        session.add_all(parsed_logs)
        session.commit()

        return parsed_logs
    
    @staticmethod
    def get_by_log_file_id(
        session: Session,
        log_file_id: int,
    ) -> list[ParsedLog]:

        statement = (
            select(ParsedLog)
            .where(ParsedLog.log_file_id == log_file_id)
            .order_by(ParsedLog.id)
        )

        return list(session.exec(statement))
    


        