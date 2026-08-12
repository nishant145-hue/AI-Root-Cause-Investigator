from sqlmodel import Session, SQLModel, create_engine

from app.models.notification_preference import (
    NotificationPreference,
)
from app.notifications.enums import (
    NotificationProvider,
    NotificationSeverity,
)
from app.notifications.preferences import (
    NotificationPreferenceService,
)


def create_session():
    engine = create_engine("sqlite://")

    SQLModel.metadata.create_all(engine)

    return Session(engine)


def test_get_or_create_creates_default_preferences():
    session = create_session()

    service = NotificationPreferenceService(session)

    preference = service.get_or_create(1)

    assert preference.user_id == 1
    assert preference.email_enabled is True
    assert preference.slack_enabled is False
    assert preference.teams_enabled is False

    session.close()


def test_get_or_create_returns_existing_preferences():
    session = create_session()

    service = NotificationPreferenceService(session)

    first = service.get_or_create(1)
    second = service.get_or_create(1)

    assert first.id == second.id

    session.close()


def test_provider_enabled():
    session = create_session()

    service = NotificationPreferenceService(session)

    preference = NotificationPreference(
        user_id=1,
        email_enabled=True,
        slack_enabled=False,
        teams_enabled=True,
    )

    assert service.is_provider_enabled(
        preference,
        NotificationProvider.EMAIL,
    ) is True

    assert service.is_provider_enabled(
        preference,
        NotificationProvider.SLACK,
    ) is False

    assert service.is_provider_enabled(
        preference,
        NotificationProvider.TEAMS,
    ) is True

    session.close()


def test_should_send_normal_notification():
    session = create_session()

    service = NotificationPreferenceService(session)

    preference = NotificationPreference(
        user_id=1,
        email_enabled=True,
        slack_enabled=False,
        teams_enabled=False,
        critical_only=False,
    )

    assert service.should_send(
        preference,
        NotificationProvider.EMAIL,
        NotificationSeverity.INFO,
    ) is True

    session.close()


def test_should_not_send_disabled_provider():
    session = create_session()

    service = NotificationPreferenceService(session)

    preference = NotificationPreference(
        user_id=1,
        email_enabled=False,
        slack_enabled=False,
        teams_enabled=False,
    )

    assert service.should_send(
        preference,
        NotificationProvider.EMAIL,
        NotificationSeverity.CRITICAL,
    ) is False

    session.close()


def test_critical_only():
    session = create_session()

    service = NotificationPreferenceService(session)

    preference = NotificationPreference(
        user_id=1,
        email_enabled=True,
        critical_only=True,
    )

    assert service.should_send(
        preference,
        NotificationProvider.EMAIL,
        NotificationSeverity.INFO,
    ) is False

    assert service.should_send(
        preference,
        NotificationProvider.EMAIL,
        NotificationSeverity.WARNING,
    ) is False

    assert service.should_send(
        preference,
        NotificationProvider.EMAIL,
        NotificationSeverity.CRITICAL,
    ) is True

    session.close()