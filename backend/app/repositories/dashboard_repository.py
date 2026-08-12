from sqlalchemy import func
from sqlmodel import Session, select

from app.models.investigation import (
    Investigation,
    InvestigationStatus,
)


class DashboardRepository:
    """Repository for user-scoped dashboard analytics."""

    def __init__(self, session: Session):
        self.session = session

    def get_total_investigations(self, user_id: int) -> int:
        return self.session.exec(
            select(func.count())
            .select_from(Investigation)
            .where(Investigation.user_id == user_id)
        ).one()

    def get_average_confidence(self, user_id: int) -> float:
        value = self.session.exec(
            select(func.avg(Investigation.confidence))
            .where(Investigation.user_id == user_id)
        ).one()

        return round(float(value or 0), 2)

    def get_status_count(
        self,
        user_id: int,
        status: InvestigationStatus,
    ) -> int:
        return self.session.exec(
            select(func.count())
            .select_from(Investigation)
            .where(
                Investigation.user_id == user_id,
                Investigation.status == status,
            )
        ).one()

    def get_severity_count(
        self,
        user_id: int,
        severity: str,
    ) -> int:
        return self.session.exec(
            select(func.count())
            .select_from(Investigation)
            .where(
                Investigation.user_id == user_id,
                Investigation.severity == severity,
            )
        ).one()

    def get_recent_investigations(
        self,
        user_id: int,
        limit: int = 10,
        offset: int = 0,
    ):
        statement = (
            select(Investigation)
            .where(Investigation.user_id == user_id)
            .order_by(Investigation.created_at.desc())
            .offset(offset)
            .limit(limit)
        )

        return self.session.exec(statement).all()

    def get_timeline(self, user_id: int):
        statement = (
            select(
                func.date(Investigation.created_at).label("date"),
                func.count(Investigation.id).label("count"),
            )
            .where(Investigation.user_id == user_id)
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

    def get_severity_distribution(self, user_id: int):
        return self._group_and_count(
            user_id,
            Investigation.severity,
            "severity",
        )

    def get_root_cause_distribution(self, user_id: int):
        return self._group_and_count(
            user_id,
            Investigation.root_cause,
            "root_cause",
        )

    def get_failed_component_distribution(self, user_id: int):
        return self._group_and_count(
            user_id,
            Investigation.failed_component,
            "component",
        )

    def get_confidence_analytics(self, user_id: int):
        average = self.session.exec(
            select(func.avg(Investigation.confidence))
            .where(Investigation.user_id == user_id)
        ).one()

        minimum = self.session.exec(
            select(func.min(Investigation.confidence))
            .where(Investigation.user_id == user_id)
        ).one()

        maximum = self.session.exec(
            select(func.max(Investigation.confidence))
            .where(Investigation.user_id == user_id)
        ).one()

        high = self.session.exec(
            select(func.count())
            .select_from(Investigation)
            .where(
                Investigation.user_id == user_id,
                Investigation.confidence >= 0.8,
            )
        ).one()

        medium = self.session.exec(
            select(func.count())
            .select_from(Investigation)
            .where(
                Investigation.user_id == user_id,
                Investigation.confidence >= 0.5,
                Investigation.confidence < 0.8,
            )
        ).one()

        low = self.session.exec(
            select(func.count())
            .select_from(Investigation)
            .where(
                Investigation.user_id == user_id,
                Investigation.confidence < 0.5,
            )
        ).one()

        return {
            "average_confidence": round(float(average or 0), 2),
            "minimum_confidence": round(float(minimum or 0), 2),
            "maximum_confidence": round(float(maximum or 0), 2),
            "high_confidence": high,
            "medium_confidence": medium,
            "low_confidence": low,
        }

    def _group_and_count(
        self,
        user_id: int,
        column,
        output_key: str,
    ):
        statement = (
            select(
                column,
                func.count(Investigation.id).label("count"),
            )
            .where(
                Investigation.user_id == user_id,
                column.is_not(None),
            )
            .group_by(column)
            .order_by(
                func.count(Investigation.id).desc()
            )
        )

        rows = self.session.exec(statement).all()

        return [
            {
                output_key: row[0],
                "count": row.count,
            }
            for row in rows
        ]

    def get_report_data(self, user_id: int):
        statement = (
            select(Investigation)
            .where(Investigation.user_id == user_id)
            .order_by(Investigation.created_at.desc())
        )

        return self.session.exec(statement).all()