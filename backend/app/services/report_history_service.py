from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Session, select

from app.models.report_history import ReportHistory


class ReportHistoryService:
    """Service for recording and retrieving report generation history."""

    def __init__(self, session: Session):
        self.session = session

    def record_report(
        self,
        *,
        user_id: int,
        report_type: str,
        format: str,
        filename: str,
        investigation_id: Optional[int] = None,
        status: str = "COMPLETED",
    ) -> ReportHistory:
        """Record a successfully generated report."""

        report_history = ReportHistory(
            user_id=user_id,
            investigation_id=investigation_id,
            report_type=report_type,
            format=format,
            filename=filename,
            status=status,
            created_at=datetime.now(timezone.utc),
        )

        self.session.add(report_history)
        self.session.commit()
        self.session.refresh(report_history)

        return report_history

    def get_history(
        self,
        *,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ReportHistory]:
        """Return report history belonging to the current user."""

        statement = (
            select(ReportHistory)
            .where(ReportHistory.user_id == user_id)
            .order_by(ReportHistory.created_at.desc())
            .offset(offset)
            .limit(limit)
        )

        return list(self.session.exec(statement).all())
