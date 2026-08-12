from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlmodel import Session

from app.auth.dependencies import get_current_user
from app.database.session import get_session
from app.models.user import User
from app.services.report_service import ReportService


router = APIRouter(
    prefix="/reports",
    tags=["Reports"],
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

    return FileResponse(
        path=file_path,
        media_type="text/csv",
        filename="investigations.csv",
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

    return FileResponse(
        path=file_path,
        media_type=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
        filename="investigations.xlsx",
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

    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename="investigations.pdf",
    )