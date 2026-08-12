from unittest.mock import MagicMock, patch

import pytest

from app.notifications.exceptions import NotificationProviderError
from app.notifications.providers.email import (
    EmailNotificationProvider,
)
from app.notifications.types import NotificationMessage


def test_provider_name():
    provider = EmailNotificationProvider()

    assert provider.name == "email"


def test_missing_smtp_host():
    provider = EmailNotificationProvider()

    with patch(
        "app.notifications.providers.email.settings.SMTP_HOST",
        "",
    ):
        with pytest.raises(NotificationProviderError):
            provider._validate_configuration()


def test_missing_from_email():
    provider = EmailNotificationProvider()

    with patch(
        "app.notifications.providers.email.settings.SMTP_HOST",
        "smtp.example.com",
    ), patch(
        "app.notifications.providers.email.settings.SMTP_FROM_EMAIL",
        "",
    ):
        with pytest.raises(NotificationProviderError):
            provider._validate_configuration()


def test_build_message():
    provider = EmailNotificationProvider()

    with patch(
        "app.notifications.providers.email.settings.SMTP_FROM_EMAIL",
        "noreply@example.com",
    ), patch(
        "app.notifications.providers.email.settings.SMTP_FROM_NAME",
        "AI Root Cause Investigator",
    ):
        notification = NotificationMessage(
            subject="Critical Incident",
            message="Database connection failed.",
            recipient="user@example.com",
        )

        email = provider._build_message(
            notification,
            "user@example.com",
        )

    assert email["Subject"] == "Critical Incident"
    assert email["To"] == "user@example.com"
    assert "noreply@example.com" in email["From"]


@pytest.mark.asyncio
async def test_send_success():
    provider = EmailNotificationProvider()

    notification = NotificationMessage(
        subject="Test Notification",
        message="Test message",
        recipient="user@example.com",
    )

    with patch.object(
        provider,
        "_validate_configuration",
    ), patch.object(
        provider,
        "_send_sync",
    ) as mock_send:

        result = await provider.send(notification)

    assert result is True
    mock_send.assert_called_once()


@pytest.mark.asyncio
async def test_send_requires_recipient():
    provider = EmailNotificationProvider()

    notification = NotificationMessage(
        subject="Test",
        message="Test message",
        recipient=None,
    )

    with patch.object(
        provider,
        "_validate_configuration",
    ):
        with pytest.raises(NotificationProviderError):
            await provider.send(notification)