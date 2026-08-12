from app.auth.dependencies import get_current_user
from app.auth.security import require_admin, require_user
from app.core.rate_limit import limiter
from app.database.session import get_session
from app.models.user import User
from app.schemas.token import (
    Message,
    RefreshTokenRequest,
    Token,
)
from app.schemas.user import UserCreate, UserRead
from app.services.auth_service import AuthService
from fastapi import APIRouter, Depends, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
)
def register(

    user_data: UserCreate,
    session: Session = Depends(get_session),
):
    """
    Register a new user.
    """
    return AuthService.register_user(
        session=session,
        user_data=user_data,
    )


@router.post(
    "/login",
    response_model=Token,
)
@limiter.limit("5/minute")
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
):
    """
    Authenticate user and return access + refresh tokens.
    """
    return AuthService.login_user(
        session=session,
        email=form_data.username,
        password=form_data.password,
    )


@router.get(
    "/me",
    response_model=UserRead,
)
def get_me(
    current_user: User = Depends(get_current_user),
):
    """
    Return current authenticated user.
    """
    return current_user


@router.get("/admin")
def admin_dashboard(
    current_user: User = Depends(require_admin),
):
    """
    Admin-only endpoint.
    """
    return {
        "message": "Welcome Admin",
        "user": current_user.username,
    }


@router.get("/profile")
def profile(
    current_user: User = Depends(require_user),
):
    """
    Accessible by any authenticated user.
    """
    return {
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role,
    }


@router.post(
    "/refresh",
    response_model=Token,
)
def refresh_token(

    request: RefreshTokenRequest,
    session: Session = Depends(get_session),
):
    """
    Generate a new access token using a refresh token.
    """
    return AuthService.refresh_access_token(
        session=session,
        refresh_token=request.refresh_token,
    )


@router.post(
    "/logout",
    response_model=Message,
)
def logout(
    request: RefreshTokenRequest,
    session: Session = Depends(get_session),
):
    """
    Revoke a refresh token.
    """
    return AuthService.logout(
        session=session,
        refresh_token=request.refresh_token,
    )
