from pydantic import Field
from sqlmodel import SQLModel


class NotificationBulkRequest(SQLModel):
    """Request containing notification IDs for bulk operations."""

    notification_ids: list[int] = Field(
        min_length=1,
        max_length=100,
    )