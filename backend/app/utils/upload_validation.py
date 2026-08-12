from pathlib import Path

from app.core.config import settings
from fastapi import HTTPException, status


ALLOWED_EXTENSIONS = {
    ".txt",
    ".log",
    ".json",
    ".csv",
    ".yaml",
    ".yml",
}

MAX_FILENAME_LENGTH = 255


def validate_extension(filename: str) -> None:
    if not filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must have a filename.",
        )

    if len(filename) > MAX_FILENAME_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is too long.",
        )

    extension = Path(filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=(
                f"Unsupported file type '{extension}'. "
                f"Allowed types: "
                f"{', '.join(sorted(ALLOWED_EXTENSIONS))}"
            ),
        )
        
def validate_file_size(size: int) -> None:
    """
    Validate uploaded file size.
    """

    if size > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=(
                f"File exceeds maximum size of "
                f"{settings.MAX_UPLOAD_SIZE // (1024 * 1024)} MB."
            ),
        )


def validate_not_empty(size: int) -> None:
    """
    Reject empty uploaded files.
    """

    if size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )