import logging
from pathlib import Path
from uuid import uuid4

from app.exceptions.parser_exceptions import ParserError
from app.models.log_file import LogFile
from app.repositories.log_file_repository import LogFileRepository
from app.services.log_processing_service import LogProcessingService
from app.services.parsed_log_service import ParsedLogService
from app.utils.file_utils import UPLOAD_DIR
from app.utils.hash_utils import generate_sha256
from app.utils.upload_validation import (
    validate_extension,
    validate_file_size,
    validate_not_empty,
)
from fastapi import HTTPException, UploadFile, status

logger = logging.getLogger(__name__)

async def process_upload(
    file: UploadFile,
    current_user,
    session,
) -> dict:
    """
    Save uploaded file to local storage.
    """
    validate_extension(file.filename)
    
    extension = Path(file.filename).suffix

    unique_filename = f"{uuid4()}{extension}"

    destination = UPLOAD_DIR / unique_filename
    
    
    
    content = await file.read()
    
    validate_not_empty(len(content))
    
    validate_file_size(len(content))
    
    file_hash = generate_sha256(content)
    
    existing_file = LogFileRepository.get_by_hash(
    session=session,
    sha256_hash=file_hash,
)

    if existing_file:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This file has already been uploaded.",
        )
    
    try:
        with open(destination, "wb") as f:
                f.write(content)

            
    
        log_file = LogFile(
            user_id=current_user.id,
            original_filename=file.filename,
            stored_filename=unique_filename,
            storage_path=str(destination),
            mime_type=file.content_type,
            file_size=len(content),
            sha256_hash=file_hash,
        )

        log_file = LogFileRepository.create(
            session=session,
            log_file=log_file,
        )

    except Exception:
        if destination.exists():
            destination.unlink()

        raise

    try:
        processed_logs = LogProcessingService.process(
            destination
        )

        ParsedLogService.save_logs(
            session=session,
            log_file_id=log_file.id,
            parsed_logs=processed_logs,
        )

    except ParserError as e:

        logger.warning(
            "Parser error while processing '%s': %s",
            file.filename,
            e,
        )

        if destination.exists():
            destination.unlink()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    except Exception:

        logger.exception(
            "Unexpected error while processing '%s'",
            file.filename,
        )

        if destination.exists():
            destination.unlink()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process uploaded log file.",
        )



    return {
        "filename": file.filename,
        "saved_as": unique_filename,
        "file_path": str(destination),
        "content_type": file.content_type,
        "size": len(content),
        "parsed_logs": len(processed_logs),
        "message": "File uploaded successfully.",
    }