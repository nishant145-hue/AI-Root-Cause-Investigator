from app.auth.dependencies import get_current_user
from app.database.session import get_session
from app.models.investigation import InvestigationStatus
from app.models.user import User
from app.notifications.enums import (
    NotificationProvider,
    NotificationSeverity,
)
from app.notifications.registry import create_notification_manager
from app.notifications.service import NotificationService
from app.notifications.tasks import enqueue_notification_delivery
from app.repositories.investigation_history_repository import (
    InvestigationHistoryRepository,
)
from app.repositories.investigation_repository import (
    InvestigationRepository,
)
from app.schemas.investigation import (
    InvestigationCreate,
    InvestigationList,
    InvestigationRead,
    InvestigationUpdate,
    RunAIInvestigationRequest,
)
from app.schemas.investigation_history import (
    InvestigationHistoryList,
)
from app.services.investigation_history_service import (
    InvestigationHistoryService,
)
from app.services.investigation_service import (
    InvestigationService,
)
from typing import Annotated

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Path,
    Query,
    status,
)
from sqlmodel import Session
from typing import Annotated

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Path,
    Query,
    status,
)
router = APIRouter(
    prefix="/investigations",
    tags=["Investigations"],
)
import logging

logger = logging.getLogger(__name__)

def get_service(
    session: Session = Depends(get_session),
):
    investigation_repository = InvestigationRepository(session)

    history_repository = InvestigationHistoryRepository(session)

    history_service = InvestigationHistoryService(
        history_repository
    )

    return InvestigationService(
        repository=investigation_repository,
        history_service=history_service,
        db=session,
    )
    
def get_history_service(
    session: Session = Depends(get_session),
):
    repository = InvestigationHistoryRepository(session)

    return InvestigationHistoryService(repository)


@router.post(
    "",
    response_model=InvestigationRead,
    status_code=status.HTTP_201_CREATED,
)
def create_investigation(
    investigation_data: InvestigationCreate,
    current_user: User = Depends(get_current_user),
    service: InvestigationService = Depends(get_service),
):
    return service.create(
        investigation_data,
        current_user.id,
    )

@router.get(
    "",
    response_model=InvestigationList,
)
def get_all_investigations(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    search: str | None = Query(
        default=None,
        description="Search by title or description",
    ),
    status_filter: InvestigationStatus | None = Query(
        default=None,
        description="Filter by investigation status",
    ),
    current_user: User = Depends(get_current_user),
    service: InvestigationService = Depends(get_service),
):
    return service.get_all(
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        search=search,
        status=status_filter,
    )
    

@router.get(
    "/{investigation_id}",
    response_model=InvestigationRead,
)
def get_investigation(
    investigation_id: Annotated[int, Path(ge=1)],
    current_user: User = Depends(get_current_user),
    service: InvestigationService = Depends(get_service),
):
    return service.get_by_id(
        investigation_id,
        current_user.id,
    )
@router.get(
    "/{investigation_id}/history",
    response_model=InvestigationHistoryList,
)
def get_investigation_history(
    investigation_id: Annotated[int, Path(ge=1)],
    current_user: User = Depends(get_current_user),
    investigation_service: InvestigationService = Depends(get_service),
    history_service: InvestigationHistoryService = Depends(
        get_history_service
    ),
):
    # Verify the investigation exists and belongs to the user
    investigation_service.get_by_id(
        investigation_id,
        current_user.id,
    )

    return history_service.get_by_investigation(
        investigation_id
    )

@router.put(
    "/{investigation_id}",
    response_model=InvestigationRead,
)
def update_investigation(
    investigation_id: Annotated[int, Path(ge=1)],
    investigation_data: InvestigationUpdate,
    current_user: User = Depends(get_current_user),
    service: InvestigationService = Depends(get_service),
):
    return service.update(
        investigation_id,
        investigation_data,
        current_user.id,
    )


@router.delete(
    "/{investigation_id}",
)
def delete_investigation(
    investigation_id: Annotated[int, Path(ge=1)],
    current_user: User = Depends(get_current_user),
    service: InvestigationService = Depends(get_service),
):
    return service.delete(
        investigation_id,
        current_user.id,
    )
    
@router.post(
    "/{investigation_id}/run",
    response_model=InvestigationRead,
    status_code=status.HTTP_200_OK,
    summary="Run AI Investigation",
    description=(
        "Runs the AI Root Cause Investigation engine "
        "on a parsed log file and stores the results."
    ),
    responses={
        200: {
            "description": "AI investigation completed successfully."
        },
        400: {
            "description": "Invalid request."
        },
        401: {
            "description": "Authentication required."
        },
        404: {
            "description": "Investigation or parsed logs not found."
        },
        502: {
            "description": "AI provider unavailable."
        },
    },
)
def run_ai_investigation(
    investigation_id: Annotated[int, Path(ge=1)],
    request: RunAIInvestigationRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    service: InvestigationService = Depends(get_service),
):
    """
    Run AI investigation and schedule notification delivery.

    Notification failures must never change the investigation result.
    """

    try:
        investigation = service.run_ai_investigation(
            investigation_id=investigation_id,
            log_file_id=request.log_file_id,
            user_id=current_user.id,
        )

    except HTTPException as exc:
        # The investigation service has already handled the
        # investigation failure and persisted FAILED status.
        if exc.status_code in (
            status.HTTP_502_BAD_GATEWAY,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        ):
            investigation = service.repository.get_by_id(
                investigation_id
            )

            if investigation is not None:
                _schedule_investigation_notification(
                    service=service,
                    background_tasks=background_tasks,
                    user=current_user,
                    investigation=investigation,
                    severity=NotificationSeverity.ERROR,
                    subject=(
                        f"Investigation Failed: "
                        f"{investigation.title}"
                    ),
                    message=(
                        f"Investigation '{investigation.title}' "
                        "failed.\n\n"
                        f"Reason: {exc.detail}"
                    ),
                    metadata={
                        "investigation_id": investigation.id,
                        "status": "FAILED",
                        "error": str(exc.detail),
                    },
                )

        raise

    # Investigation completed successfully.
    _schedule_investigation_notification(
        service=service,
        background_tasks=background_tasks,
        user=current_user,
        investigation=investigation,
        severity=NotificationSeverity.INFO,
        subject=(
            f"Investigation Completed: "
            f"{investigation.title}"
        ),
        message=(
            f"Your investigation '{investigation.title}' "
            "has completed successfully.\n\n"
            f"Root Cause: "
            f"{investigation.root_cause or 'Not identified'}\n"
            f"Failed Component: "
            f"{investigation.failed_component or 'Not identified'}\n"
            f"Severity: "
            f"{investigation.severity or 'Not specified'}\n"
            f"Confidence: "
            f"Confidence: "
            f"{investigation.confidence if investigation.confidence is not None else 'Not specified'}"
        ),
        metadata={
            "investigation_id": investigation.id,
            "status": investigation.status.value,
            "root_cause": investigation.root_cause,
            "failed_component": investigation.failed_component,
            "severity": investigation.severity,
            "confidence": investigation.confidence,
        },
    )

    return investigation

def _schedule_investigation_notification(
    *,
    service: InvestigationService,
    background_tasks: BackgroundTasks,
    user: User,
    investigation,
    severity: NotificationSeverity,
    subject: str,
    message: str,
    metadata: dict,
) -> None:
    """
    Persist an investigation notification and schedule delivery.

    Notification failures must never change the investigation result.
    """

    try:
        notification_service = NotificationService(
            session=service.db,
            manager=create_notification_manager(),
        )

        notification = notification_service.create_notification(
            user_id=user.id,
            provider=NotificationProvider.EMAIL,
            severity=severity,
            subject=subject,
            message=message,
            metadata=metadata,
        )

        enqueue_notification_delivery(
            background_tasks,
            notification.id,
            user.email,
        )

    except Exception:
        # Notification infrastructure must not break the
        # investigation lifecycle.
        logger.exception(
            "Failed to schedule investigation notification. "
            "Investigation ID=%s",
            investigation.id,
        )