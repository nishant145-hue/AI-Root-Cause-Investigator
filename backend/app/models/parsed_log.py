from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import SQLModel, Field


class ParsedLog(SQLModel, table=True):
    __tablename__ = "parsed_logs"

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
    )

    log_file_id: int = Field(
        foreign_key="log_files.id",
        index=True,
    )

    timestamp: Optional[datetime] = None

    severity: str = Field(
        max_length=20,
        index=True,
    )

    source: str = Field(
        default="",
        max_length=255,
    )

    component: str = Field(
        default="",
        max_length=255,
    )

    message: str

    raw_line: str

    log_metadata: str = ""

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
    )