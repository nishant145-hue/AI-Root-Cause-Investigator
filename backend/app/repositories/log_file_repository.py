from sqlmodel import Session, select

from app.models.log_file import LogFile


class LogFileRepository:

    @staticmethod
    def create(
        session: Session,
        log_file: LogFile,
    ) -> LogFile:

        session.add(log_file)

        session.commit()

        session.refresh(log_file)

        return log_file

    @staticmethod
    def delete(
        session: Session,
        log_file: LogFile,
    ) -> None:
        session.delete(log_file)
        session.commit()

    @staticmethod
    def get_by_hash(
        session: Session,
        sha256_hash: str,
    ) -> LogFile | None:

        statement = select(LogFile).where(
            LogFile.sha256_hash == sha256_hash
        )

        return session.exec(statement).first()

    @staticmethod
    def get_by_id_for_user(
        session: Session,
        log_file_id: int,
        user_id: int,
    ) -> LogFile | None:
        statement = select(LogFile).where(
            LogFile.id == log_file_id,
            LogFile.user_id == user_id,
        )

        return session.exec(statement).first()

    @staticmethod
    def get_by_id(
        session: Session,
        log_file_id: int,
    ) -> LogFile | None:
        statement = select(LogFile).where(
            LogFile.id == log_file_id
        )

        return session.exec(statement).first()

    @staticmethod
    def get_by_id_and_user(
        session: Session,
        log_file_id: int,
        user_id: int,
    ) -> LogFile | None:
        statement = select(LogFile).where(
            LogFile.id == log_file_id,
            LogFile.user_id == user_id,
        )

        return session.exec(statement).first()

    @staticmethod
    def get_all_for_user(
        session: Session,
        user_id: int,
    ) -> list[LogFile]:
        statement = (
            select(LogFile)
            .where(LogFile.user_id == user_id)
            .order_by(LogFile.uploaded_at.desc())
        )

        return list(session.exec(statement).all())
