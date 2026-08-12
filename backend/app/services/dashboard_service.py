from app.models.investigation import InvestigationStatus
from app.repositories.dashboard_repository import DashboardRepository
from sqlmodel import Session


class DashboardService:
    """Service layer for user-scoped dashboard analytics."""

    def __init__(self, session: Session):
        self.repository = DashboardRepository(session)

    def get_overview(self, user_id: int):
        return {
            "total_investigations":
                self.repository.get_total_investigations(user_id),

            "critical":
                self.repository.get_severity_count(
                    user_id,
                    "CRITICAL",
                ),

            "high":
                self.repository.get_severity_count(
                    user_id,
                    "HIGH",
                ),

            "medium":
                self.repository.get_severity_count(
                    user_id,
                    "MEDIUM",
                ),

            "low":
                self.repository.get_severity_count(
                    user_id,
                    "LOW",
                ),

            "resolved":
                self.repository.get_status_count(
                    user_id,
                    InvestigationStatus.COMPLETED,
                ),

            "pending":
                self.repository.get_status_count(
                    user_id,
                    InvestigationStatus.OPEN,
                ),

            "average_confidence":
                self.repository.get_average_confidence(user_id),

            "average_duration_seconds": 0,
        }

    def get_recent_investigations(
        self,
        user_id: int,
        limit: int = 10,
        offset: int = 0,
    ):
        return self.repository.get_recent_investigations(
            user_id,
            limit,
            offset,
        )

    def get_timeline(self, user_id: int):
        return self.repository.get_timeline(user_id)

    def get_severity_distribution(self, user_id: int):
        return self.repository.get_severity_distribution(user_id)

    def get_root_cause_distribution(self, user_id: int):
        return self.repository.get_root_cause_distribution(user_id)

    def get_failed_component_distribution(self, user_id: int):
        return self.repository.get_failed_component_distribution(user_id)

    def get_confidence_analytics(self, user_id: int):
        return self.repository.get_confidence_analytics(user_id)