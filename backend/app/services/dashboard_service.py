from app.models.investigation import Investigation, InvestigationStatus
from app.repositories.dashboard_repository import DashboardRepository
from sqlmodel import Session


class DashboardService:

    def __init__(self, session: Session):
        self.repository = DashboardRepository(session)

    def get_overview(self):

        return {
            "total_investigations":
                self.repository.get_total_investigations(),

            "critical":
                self.repository.get_severity_count("CRITICAL"),

            "high":
                self.repository.get_severity_count("HIGH"),

            "medium":
                self.repository.get_severity_count("MEDIUM"),

            "low":
                self.repository.get_severity_count("LOW"),

            "resolved":
                self.repository.get_status_count(
                    InvestigationStatus.COMPLETED
                ),

            "pending":
                self.repository.get_status_count(
                    InvestigationStatus.OPEN
                ),

            "average_confidence":
                self.repository.get_average_confidence(),

            "average_duration_seconds": 0,
        }
        
    def get_recent_investigations(
        self,
        limit: int = 10,
        offset: int = 0,
    ):
        return self.repository.get_recent_investigations(
            limit,
            offset,
        )
        
    
    def get_timeline(self):
        return self.repository.get_timeline()
    
    def get_severity_distribution(self):
        return self.repository.get_severity_distribution()
    
    def get_root_cause_distribution(self):
        return self.repository.get_root_cause_distribution()
    
    def get_failed_component_distribution(self):
        return self.repository.get_failed_component_distribution()
    
    def get_confidence_analytics(self):
        return self.repository.get_confidence_analytics()