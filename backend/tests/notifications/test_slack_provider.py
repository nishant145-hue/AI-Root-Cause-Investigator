from unittest.mock import MagicMock, patch

import pytest

from app.notifications.exceptions import NotificationProviderError
from app.notifications.providers.slack import (
    SlackNotificationProvider,
)
from app.notifications.types import NotificationMessage


def test_provider_name():
    provider = SlackNotificationProvider()

    assert provider.name == "slack"


def test_missing_webhook():
    provider = SlackNotificationProvider()

    with patch(
        "app.notifications.providers.slack.settings.SLACK_WEBHOOK_URL",
        "",
    ):
        with pytest.raises(NotificationProviderError):
            provider._validate_configuration()


def test_build_payload():
    provider = SlackNotificationProvider()

    notification = NotificationMessage(
        subject="Critical Incident",
        message="Database connection failed.",
    )

    payload = provider._build_payload(notification)

    assert payload["text"] == (
        "*Critical Incident*\n"
        "Database connection failed."
    )


@pytest.mark.asyncio
async def test_send_success():
    provider = SlackNotificationProvider()

    notification = NotificationMessage(
        subject="Test",
        message="Test message",
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
async def test_send_calls_webhook():
    provider = SlackNotificationProvider()

    notification = NotificationMessage(
        subject="Critical",
        message="Database failure",
    )

    with patch(
        "app.notifications.providers.slack.settings.SLACK_WEBHOOK_URL",
        "https://hooks.slack.com/test",
    ), patch.object(
        provider,
        "_send_sync",
    ) as mock_send:

        result = await provider.send(notification)

    assert result is True
    mock_send.assert_called_once_with(
        {
            "text": "*Critical*\nDatabase failure",
        }
    )