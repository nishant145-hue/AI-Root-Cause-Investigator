from app.models.investigation_history import (
    InvestigationAction,
    InvestigationHistory,
)
from app.repositories.investigation_history_repository import (
    InvestigationHistoryRepository,
)
from app.schemas.investigation_history import (
    InvestigationHistoryCreate,
)


class InvestigationHistoryService:

    def __init__(
        self,
        repository: InvestigationHistoryRepository,
    ):
        self.repository = repository

    def create(
        self,
        history_data: InvestigationHistoryCreate,
    ) -> InvestigationHistory:

        history = InvestigationHistory(
            investigation_id=history_data.investigation_id,
            user_id=history_data.user_id,
            action=history_data.action,
            old_value=history_data.old_value,
            new_value=history_data.new_value,
        )

        return self.repository.create(history)

    def get_by_investigation(
        self,
        investigation_id: int,
    ):

        items = self.repository.get_by_investigation(
            investigation_id
        )

        total = self.repository.count(
            investigation_id
        )

        return {
            "items": items,
            "total": total,
        }