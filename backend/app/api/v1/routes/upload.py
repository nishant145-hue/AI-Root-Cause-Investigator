from app.auth.dependencies import get_current_user
from app.database.session import get_session
from app.schemas.upload_schema import UploadResponse
from app.services.upload_service import process_upload
from fastapi import APIRouter, Depends, File, UploadFile
from sqlmodel import Session

router = APIRouter(
    prefix="/uploads",
    tags=["Uploads"]
)


@router.post(
    "",
    response_model=UploadResponse  # noqa: F821
)
async def upload_log(
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return await process_upload(
        file=file,
        current_user=current_user,
        session=session,
    )