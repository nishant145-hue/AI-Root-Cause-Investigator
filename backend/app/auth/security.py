from fastapi import Depends, HTTPException, status

from app.auth.dependencies import get_current_user
from app.models.user import User


def require_admin(
    current_user: User = Depends(get_current_user),
):
    """
    Allow only administrators.
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required.",
        )

    return current_user


def require_user(
    current_user: User = Depends(get_current_user),
):
    """
    Allow any authenticated user.
    """
    return current_user