from app.models.investigation import Investigation, InvestigationStatus
from app.models.investigation_history import (
    InvestigationAction,
)
from app.repositories.investigation_repository import (
    InvestigationRepository,
)
from app.schemas.investigation import (
    InvestigationCreate,
    InvestigationUpdate,
)
from app.schemas.investigation_history import (
    InvestigationHistoryCreate,
)
from app.services.investigation_history_service import (
    InvestigationHistoryService,
)
from fastapi import HTTPException, status


class InvestigationService:
    def __init__(
        self,
        repository: InvestigationRepository,
        history_service: InvestigationHistoryService,
    ):
        self.repository = repository
        self.history_service = history_service

    def create(
        self,
        investigation_data: InvestigationCreate,
        user_id: int,
    ) -> Investigation:
        existing = self.repository.get_by_title(
            investigation_data.title,
            user_id,
        )

        if existing:
            raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An investigation with this title already exists.",
            )

        investigation = Investigation(
            title=investigation_data.title,
            description=investigation_data.description,
            user_id=user_id,
        )

        created = self.repository.create(investigation)

        self.history_service.create(
            InvestigationHistoryCreate(
                investigation_id=created.id,
                user_id=user_id,
                action=InvestigationAction.CREATED,
                old_value=None,
                new_value=created.title,
            )
        )

        return created

        

    def get_by_id(
        self,
        investigation_id: int,
        user_id: int,
    ) -> Investigation:
        investigation = self.repository.get_by_id(investigation_id)

        if investigation is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Investigation not found",
            )

        if investigation.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )

        return investigation

    def get_all(
    self,
    user_id: int,
    skip: int = 0,
    limit: int = 10,
    search: str | None = None,
    status: InvestigationStatus | None = None,
):
        items = self.repository.get_all(
            user_id=user_id,
            skip=skip,
            limit=limit,
            search=search,
            status=status,
        )
        total = self.repository.count(
            user_id=user_id,
            search=search,
            status=status,
        )

        return {
            "items": items,
            "total": total,
            "skip": skip,
            "limit": limit,
            "has_next": skip + limit < total,
        }

    def update(
    self,
    investigation_id: int,
    investigation_data: InvestigationUpdate,
    user_id: int,
) -> Investigation:

        investigation = self.get_by_id(
            investigation_id,
            user_id,
        )
        old_title = investigation.title
        old_status = investigation.status
        update_data = investigation_data.model_dump(
            exclude_unset=True
        )

        existing = None

        if "title" in update_data:
            existing = self.repository.get_by_title(
                update_data["title"],
                user_id,
            )

        if existing and existing.id != investigation.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An investigation with this title already exists.",
            )

        for key, value in update_data.items():
            setattr(investigation, key, value)

        updated = self.repository.update(investigation)

        if old_title != updated.title:
            self.history_service.create(
        InvestigationHistoryCreate(
            investigation_id=updated.id,
            user_id=user_id,
            action=InvestigationAction.UPDATED,
            old_value=old_title,
            new_value=updated.title,
        )
    )

        if old_status != updated.status:
            self.history_service.create(
        InvestigationHistoryCreate(
            investigation_id=updated.id,
            user_id=user_id,
            action=InvestigationAction.STATUS_CHANGED,
            old_value=str(old_status),
            new_value=str(updated.status),
        )
    )

        return updated

    def delete(
    self,
    investigation_id: int,
    user_id: int,
):
        investigation = self.get_by_id(
        investigation_id,
        user_id,
    )
        title = investigation.title
        
        self.history_service.create(
            InvestigationHistoryCreate(
                investigation_id=investigation.id,
                user_id=user_id,
                action=InvestigationAction.DELETED,
                old_value=title,
                new_value=None,
            )
        )
        
        self.repository.delete(investigation)

        return {"message": "Investigation deleted successfully"}