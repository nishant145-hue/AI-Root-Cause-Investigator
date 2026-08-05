from pydantic import BaseModel



class UploadResponse(BaseModel):
    filename: str
    saved_as: str
    file_path: str
    content_type: str
    size: int
    message: str
    parsed_logs: int