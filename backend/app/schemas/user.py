from datetime import datetime
from typing import Optional

from pydantic import EmailStr
from sqlmodel import SQLModel


class UserCreate(SQLModel):
    """
    Request body for user registration.
    """

    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None


class UserLogin(SQLModel):
    """
    Request body for user login.
    """

    email: EmailStr
    password: str


class UserRead(SQLModel):
    """
    Response returned to the client.
    """

    id: int
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    role: str
    is_active: bool
    is_verified: bool
    created_at: datetime


class UserUpdate(SQLModel):
    """
    Update user profile.
    """

    full_name: Optional[str] = None