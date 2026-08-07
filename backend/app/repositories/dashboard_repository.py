from sqlalchemy import case, func
from sqlmodel import Session, select

from app.models.investigation import (
    Investigation,
    InvestigationStatus,
)


class DashboardRepository:
    """Repository for dashboard analytics."""

    def __init__(self, session: Session):
        self.session = session

    def get_total_investigations(self) -> int:
        return self.session.exec(
            select(func.count()).select_from(Investigation)
        ).one()

    def get_average_confidence(self) -> float:
        value = self.session.exec(
            select(func.avg(Investigation.confidence))
        ).one()

        return round(float(value or 0), 2)

    def get_status_count(
        self,
        status: InvestigationStatus,
    ) -> int:
        return self.session.exec(
            select(func.count())
            .select_from(Investigation)
            .where(Investigation.status == status)
        ).one()

    def get_severity_count(
        self,
        severity: str,
    ) -> int:
        return self.session.exec(
            select(func.count())
            .select_from(Investigation)
            .where(Investigation.severity == severity)
        ).one()
        
    def get_recent_investigations(
        self,
        limit: int = 10,
        offset: int = 0,
    ):
        statement = (
            select(Investigation)
            .order_by(Investigation.created_at.desc())
            .offset(offset)
            .limit(limit)
        )

        return self.session.exec(statement).all()
    
    def get_timeline(self):
        """Return investigation counts grouped by date."""

        statement = (
            select(
                func.date(Investigation.created_at).label("date"),
                func.count(Investigation.id).label("count"),
            )
            .group_by(func.date(Investigation.created_at))
            .order_by(func.date(Investigation.created_at))
        )

        rows = self.session.exec(statement).all()

        return [
            {
                "date": row.date,
                "count": row.count,
            }
            for row in rows
        ]
    
    def get_severity_distribution(self):
        return self._group_and_count(
            Investigation.severity,
            "severity",
        )

        
    def get_root_cause_distribution(self):
        return self._group_and_count(
            Investigation.root_cause,
            "root_cause",
        )
    
    def get_failed_component_distribution(self):
        return self._group_and_count(
            Investigation.failed_component,
            "component",
        )

        
    def get_confidence_analytics(self):
        """Return AI confidence statistics."""

        average = self.session.exec(
            select(func.avg(Investigation.confidence))
        ).one()

        minimum = self.session.exec(
            select(func.min(Investigation.confidence))
        ).one()

        maximum = self.session.exec(
            select(func.max(Investigation.confidence))
        ).one()

        high = self.session.exec(
            select(func.count())
            .select_from(Investigation)
            .where(Investigation.confidence >= 0.8)
        ).one()

        medium = self.session.exec(
            select(func.count())
            .select_from(Investigation)
            .where(
                Investigation.confidence >= 0.5,
                Investigation.confidence < 0.8,
            )
        ).one()

        low = self.session.exec(
            select(func.count())
            .select_from(Investigation)
            .where(Investigation.confidence < 0.5)
        ).one()

        return {
            "average_confidence": round(float(average or 0), 2),
            "minimum_confidence": round(float(minimum or 0), 2),
            "maximum_confidence": round(float(maximum or 0), 2),
            "high_confidence": high,
            "medium_confidence": medium,
            "low_confidence": low,
        }
        
    def _group_and_count(self, column, output_key: str):
        """Generic helper to group investigations by a column."""

        statement = (
            select(
                column,
                func.count(Investigation.id).label("count"),
            )
            .where(column.is_not(None))
            .group_by(column)
            .order_by(func.count(Investigation.id).desc())
        )

        rows = self.session.exec(statement).all()

        return [
            {
                output_key: row[0],
                "count": row.count,
            }
            for row in rows
        ]
        
    def get_report_data(self):
        """
        Return all investigations ordered by newest first.
        Used by CSV, Excel and PDF exports.
        """

        statement = (
            select(Investigation)
            .order_by(Investigation.created_at.desc())
        )

        return self.session.exec(statement).all()