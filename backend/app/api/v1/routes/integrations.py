from fastapi import APIRouter, Depends

from app.auth.dependencies import get_current_user
from app.core.config import settings
from app.models.user import User

router = APIRouter(
    prefix="/integrations",
    tags=["Integrations"],
)


@router.get("/status")
def get_integration_status(
    current_user: User = Depends(get_current_user),
):
    """Return safe configuration status for notification integrations."""

    return {
        "email": {
            "registered": True,
            "configured": bool(
                settings.SMTP_HOST
                and settings.SMTP_FROM_EMAIL
            ),
        },
        "slack": {
            "registered": True,
            "configured": bool(
                settings.SLACK_WEBHOOK_URL
            ),
        },
        "teams": {
            "registered": True,
            "configured": bool(
                settings.TEAMS_WEBHOOK_URL
            ),
        },
    }
