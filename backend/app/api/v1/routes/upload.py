from app.auth.dependencies import get_current_user
from app.database.session import get_session
from app.repositories.log_file_repository import LogFileRepository
from app.repositories.parsed_log_repository import ParsedLogRepository
from app.schemas.upload_schema import (
    UploadListItem,
    UploadResponse,
)
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

@router.get(
    "",
    response_model=list[UploadListItem],
)
async def list_uploads(
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    log_files = LogFileRepository.get_all_for_user(
        session=session,
        user_id=current_user.id,
    )

    results = []

    for log_file in log_files:
        parsed_logs = ParsedLogRepository.get_by_log_file_id(
            session=session,
            log_file_id=log_file.id,
        )

        results.append(
            UploadListItem(
                id=log_file.id,
                filename=log_file.original_filename,
                content_type=log_file.mime_type,
                size=log_file.file_size,
                parsed_logs=len(parsed_logs),
                status=log_file.status,
                uploaded_at=log_file.uploaded_at,
            )
        )

    return results