from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.enums.severity import SeverityLevel


class ParsedLog(BaseModel):
    timestamp: datetime | None = None
    severity: SeverityLevel = SeverityLevel.INFO
    source: str = ""
    component: str = ""
    message: str
    raw_line: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)