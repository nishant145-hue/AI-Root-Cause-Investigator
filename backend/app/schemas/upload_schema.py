from datetime import datetime

from pydantic import BaseModel


class UploadResponse(BaseModel):
    id: int
    filename: str
    saved_as: str
    file_path: str
    content_type: str
    size: int
    message: str
    parsed_logs: int


class UploadListItem(BaseModel):
    id: int
    filename: str
    content_type: str
    size: int
    parsed_logs: int
    status: str
    uploaded_at: datetime