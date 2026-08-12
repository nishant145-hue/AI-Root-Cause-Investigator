from app.auth.dependencies import get_current_user
from app.database.session import get_session
from app.models.user import User
from app.schemas.dashboard import (
    ConfidenceAnalytics,
    DashboardOverview,
    FailedComponentAnalytics,
    RecentInvestigation,
    RootCauseAnalytics,
    SeverityAnalytics,
    TimelinePoint,
)
from app.services.dashboard_service import DashboardService
from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)


@router.get(
    "/overview",
    response_model=DashboardOverview,
)
def dashboard_overview(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    service = DashboardService(session)

    return service.get_overview(
        current_user.id
    )


@router.get(
    "/recent",
    response_model=list[RecentInvestigation],
)
def recent_investigations(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    service = DashboardService(session)

    return service.get_recent_investigations(
        current_user.id,
        limit,
        offset,
    )


@router.get(
    "/timeline",
    response_model=list[TimelinePoint],
)
def dashboard_timeline(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    service = DashboardService(session)

    return service.get_timeline(
        current_user.id
    )


@router.get(
    "/severity",
    response_model=list[SeverityAnalytics],
)
def severity_distribution(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    service = DashboardService(session)

    return service.get_severity_distribution(
        current_user.id
    )


@router.get(
    "/root-causes",
    response_model=list[RootCauseAnalytics],
)
def root_causes(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    service = DashboardService(session)

    return service.get_root_cause_distribution(
        current_user.id
    )


@router.get(
    "/failed-components",
    response_model=list[FailedComponentAnalytics],
)
def failed_components(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    service = DashboardService(session)

    return service.get_failed_component_distribution(
        current_user.id
    )


@router.get(
    "/confidence",
    response_model=ConfidenceAnalytics,
)
def confidence_analytics(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    service = DashboardService(session)

    return service.get_confidence_analytics(
        current_user.id
    )