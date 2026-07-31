from datetime import datetime, timedelta, timezone

from app.auth.hashing import hash_password, verify_password
from app.auth.jwt_handler import create_access_token
from app.auth.refresh_token import (
    generate_refresh_token,
    hash_refresh_token,
)
from app.core.config import settings
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.repositories.refresh_token_repository import (
    RefreshTokenRepository,
)
from app.repositories.user_repository import UserRepository
from app.schemas.token import Token
from app.schemas.user import UserCreate
from fastapi import HTTPException, status
from sqlmodel import Session


class AuthService:

    @staticmethod
    def register_user(
        session: Session,
        user_data: UserCreate,
    ) -> User:

        # Check email
        if UserRepository.get_by_email(
            session,
            user_data.email,
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        # Check username
        if UserRepository.get_by_username(
            session,
            user_data.username,
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists",
            )

        # Create User
        user = User(
            username=user_data.username,
            email=user_data.email,
            full_name=user_data.full_name,
            hashed_password=hash_password(
                user_data.password
            ),
        )

        return UserRepository.create(
            session,
            user,
        )

    @staticmethod
    def login_user(
        session: Session,
        email: str,
        password: str,
    ) -> Token:

        # Find user
        user = UserRepository.get_by_email(
            session,
            email,
        )

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        # Verify password
        if not verify_password(
            password,
            user.hashed_password,
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        # Create Access Token
        access_token = create_access_token(
            {
                "sub": user.email,
                "user_id": user.id,
                "role": user.role,
            }
        )

        # Create Refresh Token
        refresh_token = generate_refresh_token()

        # Hash Refresh Token
        token_hash = hash_refresh_token(
            refresh_token
        )

        # Save Refresh Token
        refresh_token_db = RefreshToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=datetime.utcnow()
            + timedelta(
                days=settings.REFRESH_TOKEN_EXPIRE_DAYS
            ),
            revoked=False,
        )

        RefreshTokenRepository.create(
            session=session,
            refresh_token=refresh_token_db,
        )

        # Return Tokens
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
        )
        
    @staticmethod
    def refresh_access_token(
        session: Session,
        refresh_token: str,
    ) -> Token:

        # Hash incoming refresh token
        token_hash = hash_refresh_token(
            refresh_token
        )

    # Find token in database
        db_token = RefreshTokenRepository.get_by_hash(
            session=session,
            token_hash=token_hash,
        )

        if db_token is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        # Check revoked
        if db_token.revoked:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token revoked",
            )

        # Check expiry
        if db_token.expires_at < datetime.now(timezone.utc).replace(tzinfo=None):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token expired",
            )

        # Load user
        user = session.get(
            User,
            db_token.user_id,
        )

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )  

        # ---------------------------------------
        # ROTATE THE REFRESH TOKEN
        # ---------------------------------------

        # Revoke old refresh token
        RefreshTokenRepository.revoke(
            session=session,
            refresh_token=db_token,
        )

        # Generate new refresh token
        new_refresh_token = generate_refresh_token()

        # Hash new refresh token
        new_token_hash = hash_refresh_token(
            new_refresh_token
        )

        # Save new refresh token
        new_refresh_token_db = RefreshToken(
            user_id=user.id,
            token_hash=new_token_hash,
            expires_at=datetime.utcnow()
            + timedelta(
                days=settings.REFRESH_TOKEN_EXPIRE_DAYS
            ),
            revoked=False,
        )

        RefreshTokenRepository.create(
            session=session,
            refresh_token=new_refresh_token_db,
        )

        # Create new access token
        access_token = create_access_token(
            {
                "sub": user.email,
                "user_id": user.id,
                "role": user.role,
            }
        )

        # Return NEW tokens
        return Token(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
        )
        
    @staticmethod
    def logout(
            session: Session,
            refresh_token: str,
        ):

        token_hash = hash_refresh_token(
            refresh_token
        )

        db_token = RefreshTokenRepository.get_by_hash(
            session=session,
            token_hash=token_hash,
        )

        if db_token is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        if db_token.revoked:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token already revoked",
            )

        RefreshTokenRepository.revoke(
            session=session,
            refresh_token=db_token,
        )

        return {
            "message": "Logged out successfully"
        }