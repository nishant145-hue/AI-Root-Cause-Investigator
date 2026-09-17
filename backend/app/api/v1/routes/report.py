from fastapi import APIRouter, Depends, Query
from fastapi.responses import FileResponse
from sqlmodel import Session

from app.auth.dependencies import get_current_user
from app.database.session import get_session
from app.models.user import User
from app.schemas.report_history import ReportHistoryList
from app.services.report_history_service import ReportHistoryService
from app.services.report_service import ReportService


router = APIRouter(
    prefix="/reports",
    tags=["Reports"],
)


@router.get(
    "/history",
    response_model=ReportHistoryList,
)
def get_report_history(
    limit: int = Query(
        default=50,
        ge=1,
        le=100,
    ),
    offset: int = Query(
        default=0,
        ge=0,
    ),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    service = ReportHistoryService(session)

    items = service.get_history(
        user_id=current_user.id,
        limit=limit,
        offset=offset,
    )

    return ReportHistoryList(
        items=items,
        total=len(items),
    )


@router.get("/csv")
def export_csv(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    service = ReportService(session)

    file_path = service.export_csv(
        user_id=current_user.id,
    )

    filename = "investigations.csv"

    ReportHistoryService(session).record_report(
        user_id=current_user.id,
        investigation_id=None,
        report_type="ALL_INVESTIGATIONS",
        format="CSV",
        filename=filename,
    )

    return FileResponse(
        path=file_path,
        media_type="text/csv",
        filename=filename,
    )


@router.get("/excel")
def export_excel(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    service = ReportService(session)

    file_path = service.export_excel(
        user_id=current_user.id,
    )

    filename = "investigations.xlsx"

    ReportHistoryService(session).record_report(
        user_id=current_user.id,
        investigation_id=None,
        report_type="ALL_INVESTIGATIONS",
        format="EXCEL",
        filename=filename,
    )

    return FileResponse(
        path=file_path,
        media_type=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
        filename=filename,
    )


@router.get("/pdf")
def export_pdf(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    service = ReportService(session)

    file_path = service.export_pdf(
        user_id=current_user.id,
    )

    filename = "investigations.pdf"

    ReportHistoryService(session).record_report(
        user_id=current_user.id,
        investigation_id=None,
        report_type="ALL_INVESTIGATIONS",
        format="PDF",
        filename=filename,
    )

    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=filename,
    )
