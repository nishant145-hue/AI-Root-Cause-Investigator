from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.mark.asyncio
async def test_deliver_notification_not_found():
    mock_session = MagicMock()
    mock_session.__enter__.return_value = mock_session
    mock_session.__exit__.return_value = None
    mock_session.get.return_value = None

    with patch(
        "app.notifications.background.Session",
        return_value=mock_session,
    ), patch(
        "app.notifications.background.create_notification_manager",
    ):

        from app.notifications.background import (
            deliver_notification,
        )

        await deliver_notification(
            notification_id=999,
        )

    mock_session.get.assert_called_once()


@pytest.mark.asyncio
async def test_deliver_notification():
    notification = MagicMock()
    notification.id = 1

    mock_session = MagicMock()
    mock_session.__enter__.return_value = mock_session
    mock_session.__exit__.return_value = None
    mock_session.get.return_value = notification

    mock_service = MagicMock()
    mock_service.deliver = AsyncMock()

    with patch(
        "app.notifications.background.Session",
        return_value=mock_session,
    ), patch(
        "app.notifications.background.create_notification_manager",
    ) as mock_manager, patch(
        "app.notifications.background.NotificationService",
        return_value=mock_service,
    ):

        from app.notifications.background import (
            deliver_notification,
        )

        await deliver_notification(
            notification_id=1,
            recipient="test@example.com",
        )

    mock_session.get.assert_called_once()
    mock_service.deliver.assert_awaited_once_with(
        notification,
        recipient="test@example.com",
    )