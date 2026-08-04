import os
from pathlib import Path
from uuid import uuid4

from app.models.log_file import LogFile
from app.repositories.log_file_repository import LogFileRepository
from app.utils.file_utils import UPLOAD_DIR
from app.utils.hash_utils import generate_sha256
from app.utils.upload_validation import (
    validate_extension,
    validate_file_size,
    validate_not_empty,
)
from fastapi import HTTPException, UploadFile, status


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

        LogFileRepository.create(
        session=session,
        log_file=log_file,
    )

    except Exception:
        if destination.exists():
            destination.unlink()

        raise

    LogFileRepository.create(
        session=session,
        log_file=log_file,
    )
    return {
        "filename": file.filename,
        "saved_as": unique_filename,
        "file_path": str(destination),
        "content_type": file.content_type,
        "size": len(content),
        "message": "File uploaded successfully."
    }