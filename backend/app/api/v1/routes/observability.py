from typing import Any

from app.agent.execution_manager import (
    AgentExecutionManager,
)
from app.agent.execution_manager_provider import (
    get_execution_manager,
)
from app.api.v1.investigation import (
    get_service,
)
from app.auth.dependencies import (
    get_current_user,
)
from app.models.user import User
from app.services.investigation_service import (
    InvestigationService,
)
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

router = APIRouter(
    prefix="/observability",
    tags=["Observability"],
)


def _verify_investigation_ownership(
    investigation_id: int,
    current_user: User,
    service: InvestigationService,
) -> None:
    """
    Verify that the authenticated user owns the investigation.

    InvestigationService.get_by_id() is the canonical ownership
    check used by the investigation API.
    """
    service.get_by_id(
        investigation_id=investigation_id,
        user_id=current_user.id,
    )


# ------------------------------------------------------------------
# Investigation observability
# ------------------------------------------------------------------


@router.get("/investigations/{investigation_id}")
def investigation_observability(
    investigation_id: int,
    current_user: User = Depends(get_current_user),
    service: InvestigationService = Depends(get_service),
    manager: AgentExecutionManager = Depends(
        get_execution_manager
    ),
) -> dict[str, Any]:
    _verify_investigation_ownership(
        investigation_id,
        current_user,
        service,
    )

    snapshot = manager.observability_snapshot(
        investigation_id=investigation_id
    )

    investigation = snapshot.get("investigation")

    if not investigation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Investigation observability data not found",
        )

    return snapshot


# ------------------------------------------------------------------
# Investigation summary
# ------------------------------------------------------------------


@router.get("/investigations/{investigation_id}/summary")
def investigation_observability_summary(
    investigation_id: int,
    current_user: User = Depends(get_current_user),
    service: InvestigationService = Depends(get_service),
    manager: AgentExecutionManager = Depends(
        get_execution_manager
    ),
) -> dict[str, Any]:
    _verify_investigation_ownership(
        investigation_id,
        current_user,
        service,
    )

    snapshot = manager.investigation_trace_summary(
        investigation_id
    )

    if snapshot.get("status") == "NOT_FOUND":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Investigation observability data not found",
        )

    return snapshot


# ------------------------------------------------------------------
# Investigation timeline
# ------------------------------------------------------------------


@router.get("/investigations/{investigation_id}/timeline")
def investigation_timeline(
    investigation_id: int,
    current_user: User = Depends(get_current_user),
    service: InvestigationService = Depends(get_service),
    manager: AgentExecutionManager = Depends(
        get_execution_manager
    ),
) -> dict[str, Any]:
    _verify_investigation_ownership(
        investigation_id,
        current_user,
        service,
    )

    trace = manager.investigation_trace_snapshot(
        investigation_id
    )

    if trace.get("status") == "NOT_FOUND":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Investigation observability data not found",
        )

    return {
        "investigation_id": investigation_id,
        "timeline": manager.investigation_timeline(
            investigation_id
        ),
    }


# ------------------------------------------------------------------
# Investigation critical path
# ------------------------------------------------------------------


@router.get(
    "/investigations/{investigation_id}/critical-path"
)
def investigation_critical_path(
    investigation_id: int,
    current_user: User = Depends(get_current_user),
    service: InvestigationService = Depends(get_service),
    manager: AgentExecutionManager = Depends(
        get_execution_manager
    ),
) -> dict[str, Any]:
    _verify_investigation_ownership(
        investigation_id,
        current_user,
        service,
    )

    trace = manager.investigation_trace_snapshot(
        investigation_id
    )

    if trace.get("status") == "NOT_FOUND":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Investigation observability data not found",
        )

    return manager.investigation_critical_path(
        investigation_id
    )


# ------------------------------------------------------------------
# Runtime observability
# ------------------------------------------------------------------


@router.get("/runtime")
def runtime_observability(
    current_user: User = Depends(get_current_user),
    manager: AgentExecutionManager = Depends(
        get_execution_manager
    ),
) -> dict[str, Any]:
    return manager.observability_snapshot()


# ------------------------------------------------------------------
# Failure observability
# ------------------------------------------------------------------


@router.get("/failures")
def failure_observability(
    current_user: User = Depends(get_current_user),
    manager: AgentExecutionManager = Depends(
        get_execution_manager
    ),
) -> dict[str, Any]:
    return {
        "failures": manager.failure_telemetry_snapshot(),
        "aggregate": manager.failure_telemetry_aggregate(),
    }


# ------------------------------------------------------------------
# Observability health
# ------------------------------------------------------------------

@router.get("/health")
def observability_health(
    current_user: User = Depends(get_current_user),
    manager: AgentExecutionManager = Depends(
        get_execution_manager
    ),
) -> dict[str, Any]:
    return manager.runtime_health_snapshot()
