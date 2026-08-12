from typing import Optional

from sqlmodel import Session, select

from app.models.notification_preference import NotificationPreference
from app.notifications.enums import NotificationProvider, NotificationSeverity


class NotificationPreferenceService:
    """Manage user notification preferences."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_or_create(
        self,
        user_id: int,
    ) -> NotificationPreference:
        """Get preferences or create default preferences."""

        statement = select(NotificationPreference).where(
            NotificationPreference.user_id == user_id
        )

        preference = self.session.exec(statement).first()

        if preference is not None:
            return preference

        preference = NotificationPreference(
            user_id=user_id,
            email_enabled=True,
            slack_enabled=False,
            teams_enabled=False,
            critical_only=False,
            daily_digest=False,
            weekly_digest=False,
        )

        self.session.add(preference)
        self.session.commit()
        self.session.refresh(preference)

        return preference

    def is_provider_enabled(
        self,
        preference: NotificationPreference,
        provider: NotificationProvider,
    ) -> bool:
        """Check whether a provider is enabled."""

        if provider == NotificationProvider.EMAIL:
            return preference.email_enabled

        if provider == NotificationProvider.SLACK:
            return preference.slack_enabled

        if provider == NotificationProvider.TEAMS:
            return preference.teams_enabled

        return False

    def should_send(
        self,
        preference: NotificationPreference,
        provider: NotificationProvider,
        severity: NotificationSeverity,
    ) -> bool:
        """Determine whether a notification should be delivered."""

        if not self.is_provider_enabled(
            preference,
            provider,
        ):
            return False

        if (
            preference.critical_only
            and severity != NotificationSeverity.CRITICAL
        ):
            return False

        return True