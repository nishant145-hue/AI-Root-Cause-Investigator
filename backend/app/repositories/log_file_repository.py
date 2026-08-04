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
    def get_by_hash(
        session: Session,
        sha256_hash: str,
    ) -> LogFile | None:

        statement = select(LogFile).where(
            LogFile.sha256_hash == sha256_hash
        )

        return session.exec(statement).first()