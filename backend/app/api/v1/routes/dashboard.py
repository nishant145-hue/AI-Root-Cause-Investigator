from app.database.session import get_session
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
from fastapi import APIRouter, Depends
from sqlmodel import Session

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get(
    "/overview",
    response_model=DashboardOverview,
)
def dashboard_overview(
    session: Session = Depends(get_session),
):
    service = DashboardService(session)
    return service.get_overview()

@router.get(
    "/recent",
    response_model=list[RecentInvestigation],
)
def recent_investigations(
    limit: int = 10,
    offset: int = 0,
    session: Session = Depends(get_session),
):
    service = DashboardService(session)

    return service.get_recent_investigations(
        limit,
        offset,
    )

@router.get(
    "/timeline",
    response_model=list[TimelinePoint],
)
def dashboard_timeline(
    session: Session = Depends(get_session),
):
    service = DashboardService(session)
    return service.get_timeline()

@router.get(
    "/severity",
    response_model=list[SeverityAnalytics],
)
def severity_distribution(
    session: Session = Depends(get_session),
):
    service = DashboardService(session)
    return service.get_severity_distribution()

@router.get(
    "/root-causes",
    response_model=list[RootCauseAnalytics],
)
def root_causes(
    session: Session = Depends(get_session),
):
    service = DashboardService(session)
    return service.get_root_cause_distribution()

@router.get(
    "/failed-components",
    response_model=list[FailedComponentAnalytics],
)
def failed_components(
    session: Session = Depends(get_session),
):
    service = DashboardService(session)
    return service.get_failed_component_distribution()

@router.get(
    "/confidence",
    response_model=ConfidenceAnalytics,
)
def confidence_analytics(
    session: Session = Depends(get_session),
):
    service = DashboardService(session)
    return service.get_confidence_analytics()