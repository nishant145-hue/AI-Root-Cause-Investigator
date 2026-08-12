from fastapi import BackgroundTasks

from app.notifications.background import deliver_notification


def enqueue_notification_delivery(
    background_tasks: BackgroundTasks,
    notification_id: int,
    recipient: str | None = None,
) -> None:
    """Schedule notification delivery as a FastAPI background task."""

    background_tasks.add_task(
        deliver_notification,
        notification_id,
        recipient,
    )