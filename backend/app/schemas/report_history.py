from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ReportHistoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    investigation_id: int | None
    report_type: str
    format: str
    filename: str
    status: str
    created_at: datetime


class ReportHistoryList(BaseModel):
    items: list[ReportHistoryRead]
    total: int
