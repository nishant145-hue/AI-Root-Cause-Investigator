from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

from app.models.log_file import LogFile

if TYPE_CHECKING:
    from app.models.investigation import Investigation
    from app.models.refresh_token import RefreshToken
    from app.models.log_file import LogFile

class User(SQLModel, table=True):
    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True)

    username: str = Field(index=True, unique=True)
    email: str = Field(index=True, unique=True)

    full_name: Optional[str] = Field(default=None)

    hashed_password: str

    role: str = Field(default="user")

    is_active: bool = Field(default=True)
    is_verified: bool = Field(default=False)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    refresh_tokens: list["RefreshToken"] = Relationship(
        back_populates="user"
    )
    investigations: list["Investigation"] = Relationship(
    back_populates="user"
    )
    
    log_files: list["LogFile"] = Relationship(
    back_populates="user"
    )