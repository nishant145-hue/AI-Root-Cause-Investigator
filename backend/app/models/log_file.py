from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.user import User


class LogFile(SQLModel, table=True):
    __tablename__ = "log_files"

    id: int | None = Field(default=None, primary_key=True)

    user_id: int = Field(
        foreign_key="users.id",
        index=True,
    )

    original_filename: str

    stored_filename: str = Field(
        index=True,
        unique=True,
    )

    storage_path: str

    mime_type: str

    file_size: int

    sha256_hash: Optional[str] = Field(
    default=None,
    unique=True,
    index=True,
)
    
    status: str = Field(default="uploaded")

    uploaded_at: datetime = Field(default_factory=datetime.utcnow)

    user: "User" = Relationship(
        back_populates="log_files"
    )