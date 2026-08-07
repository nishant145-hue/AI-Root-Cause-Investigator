from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlmodel import Session

from app.database.session import get_session
from app.services.report_service import ReportService

router = APIRouter(
    prefix="/reports",
    tags=["Reports"],
)


@router.get("/csv")
def export_csv(
    session: Session = Depends(get_session),
):
    service = ReportService(session)

    file_path = service.export_csv()

    return FileResponse(
        path=file_path,
        media_type="text/csv",
        filename="investigations.csv",
    )
    
@router.get("/excel")
def export_excel(
    session: Session = Depends(get_session),
):
    service = ReportService(session)

    file_path = service.export_excel()

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
    session: Session = Depends(get_session),
):
    service = ReportService(session)

    file_path = service.export_pdf()

    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename="investigations.pdf",
    )