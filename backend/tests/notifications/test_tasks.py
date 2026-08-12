from unittest.mock import MagicMock, patch

from app.notifications.tasks import (
    enqueue_notification_delivery,
)


def test_enqueue_notification_delivery():
    background_tasks = MagicMock()

    with patch(
        "app.notifications.tasks.deliver_notification"
    ) as mock_delivery:

        enqueue_notification_delivery(
            background_tasks,
            notification_id=123,
            recipient="test@example.com",
        )

    background_tasks.add_task.assert_called_once_with(
        mock_delivery,
        123,
        "test@example.com",
    )