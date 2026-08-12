from sqlmodel import Session

from app.database.session import engine
from app.models.notification import Notification
from app.notifications.registry import create_notification_manager
from app.notifications.service import NotificationService


async def deliver_notification(
    notification_id: int,
    recipient: str | None = None,
) -> None:
    """
    Deliver a persisted notification in the background.

    A fresh database session is created because background
    tasks should not reuse a request-scoped database session.
    """

    manager = create_notification_manager()

    with Session(engine) as session:
        notification = session.get(
            Notification,
            notification_id,
        )

        if notification is None:
            return

        service = NotificationService(
            session=session,
            manager=manager,
        )

        await service.deliver(
            notification,
            recipient=recipient,
        )