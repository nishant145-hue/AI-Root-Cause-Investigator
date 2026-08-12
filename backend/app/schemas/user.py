from datetime import datetime
from typing import Optional

from pydantic import EmailStr, Field, field_validator
from sqlmodel import SQLModel


class UserCreate(SQLModel):
    """
    Request body for user registration.

    Security:
    - Restricts username length and characters.
    - Validates email format.
    - Restricts password length.
    - Prevents control characters.
    - Does not expose or accept privileged server-controlled fields.
    """

    username: str = Field(
        min_length=3,
        max_length=50,
        description="Unique username.",
    )

    email: EmailStr

    password: str = Field(
        min_length=8,
        max_length=128,
        description="User password.",
    )

    full_name: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Optional user's full name.",
    )

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        """
        Validate and normalize username.
        """

        value = value.strip()

        if not value:
            raise ValueError("Username cannot be empty.")

        # Allow only predictable username characters.
        #
        # This prevents:
        # - control characters
        # - path-like values
        # - unexpected punctuation
        # - whitespace injection
        allowed = set(
            "abcdefghijklmnopqrstuvwxyz"
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            "0123456789"
            "_.-"
        )

        if any(character not in allowed for character in value):
            raise ValueError(
                "Username contains invalid characters."
            )

        return value

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        """
        Validate password content.

        Passwords may contain spaces and normal special characters,
        but control characters are rejected.
        """

        if not value:
            raise ValueError("Password cannot be empty.")

        if any(ord(character) < 32 for character in value):
            raise ValueError(
                "Password contains invalid control characters."
            )

        if any(ord(character) == 127 for character in value):
            raise ValueError(
                "Password contains invalid control characters."
            )

        return value

    @field_validator("full_name")
    @classmethod
    def validate_full_name(
        cls,
        value: Optional[str],
    ) -> Optional[str]:
        """
        Validate optional full name.
        """

        if value is None:
            return None

        value = value.strip()

        if not value:
            return None

        if any(ord(character) < 32 for character in value):
            raise ValueError(
                "Full name contains invalid control characters."
            )

        if any(ord(character) == 127 for character in value):
            raise ValueError(
                "Full name contains invalid control characters."
            )

        return value


class UserLogin(SQLModel):
    """
    Request body for user login.
    """

    email: EmailStr

    password: str = Field(
        min_length=1,
        max_length=128,
    )

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        """
        Prevent malformed control-character input.
        """

        if any(ord(character) < 32 for character in value):
            raise ValueError(
                "Password contains invalid control characters."
            )

        if any(ord(character) == 127 for character in value):
            raise ValueError(
                "Password contains invalid control characters."
            )

        return value


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

    full_name: Optional[str] = Field(
        default=None,
        max_length=255,
    )

    @field_validator("full_name")
    @classmethod
    def validate_full_name(
        cls,
        value: Optional[str],
    ) -> Optional[str]:
        """
        Validate optional profile name.
        """

        if value is None:
            return None

        value = value.strip()

        if not value:
            return None

        if any(ord(character) < 32 for character in value):
            raise ValueError(
                "Full name contains invalid control characters."
            )

        if any(ord(character) == 127 for character in value):
            raise ValueError(
                "Full name contains invalid control characters."
            )

        return value