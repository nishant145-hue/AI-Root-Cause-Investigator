from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.auth.dependencies import get_current_user
from app.database.session import get_session
from app.models.user import User
from app.notifications.preferences import (
    NotificationPreferenceService,
)
from app.schemas.notification_preference import (
    NotificationPreferenceRead,
    NotificationPreferenceUpdate,
)

router = APIRouter(
    prefix="/notifications/preferences",
    tags=["Notification Preferences"],
)


def get_preference_service(
    session: Session = Depends(get_session),
) -> NotificationPreferenceService:
    return NotificationPreferenceService(session)


@router.get(
    "",
    response_model=NotificationPreferenceRead,
)
def get_preferences(
    current_user: User = Depends(get_current_user),
    service: NotificationPreferenceService = Depends(
        get_preference_service
    ),
):
    """Get notification preferences for the current user."""

    return service.get_or_create(current_user.id)


@router.put(
    "",
    response_model=NotificationPreferenceRead,
)
def update_preferences(
    preference_data: NotificationPreferenceUpdate,
    current_user: User = Depends(get_current_user),
    service: NotificationPreferenceService = Depends(
        get_preference_service
    ),
):
    """Update notification preferences."""

    preference = service.get_or_create(current_user.id)

    update_data = preference_data.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(preference, field, value)

    service.session.add(preference)
    service.session.commit()
    service.session.refresh(preference)

    return preference