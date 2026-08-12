from datetime import datetime, timezone
from typing import Annotated

from app.auth.dependencies import get_current_user
from app.database.session import get_session
from app.models.notification import Notification
from app.models.user import User
from app.notifications.registry import create_notification_manager
from app.notifications.service import NotificationService
from app.schemas.notification import (
    NotificationCreate,
    NotificationRead,
)
from app.schemas.notification_bulk import NotificationBulkRequest
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlmodel import Session, func, select

router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"],
)


def get_notification_service(
    session: Session = Depends(get_session),
) -> NotificationService:
    return NotificationService(
        session=session,
        manager=create_notification_manager(),
    )


@router.post(
    "",
    response_model=NotificationRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_notification(
    notification_data: NotificationCreate,
    current_user: User = Depends(get_current_user),
    service: NotificationService = Depends(
        get_notification_service
    ),
):
    """Create and deliver a notification."""

    notification = service.create_notification(
        user_id=current_user.id,
        provider=notification_data.provider,
        severity=notification_data.severity,
        subject=notification_data.subject,
        message=notification_data.message,
        metadata=notification_data.metadata_json,
    )

    await service.deliver(notification)

    return notification


@router.get(
    "",
    response_model=list[NotificationRead],
)
def get_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    is_read: bool | None = Query(
        default=None,
        description="Filter notifications by read status.",
    ),
    is_archived: bool | None = Query(
        default=None,
        description="Filter notifications by archive status.",
    ),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Get notifications belonging to the current user."""

    statement = (
        select(Notification)
        .where(Notification.user_id == current_user.id)
    )

    if is_read is not None:
        statement = statement.where(
            Notification.is_read == is_read
        )
    if is_archived is not None:
        statement = statement.where(
            Notification.is_archived == is_archived
        ) 
    statement = (
        statement
        .order_by(Notification.created_at.desc())
        .offset(skip)
        .limit(limit)
    )

    return list(session.exec(statement).all())


@router.get(
    "/unread-count",
    response_model=int,
)
def get_unread_count(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Return the number of unread notifications for the current user."""

    statement = (
        select(func.count())
        .select_from(Notification)
        .where(
            Notification.user_id == current_user.id,
            Notification.is_read.is_(False),
        )
    )

    return session.exec(statement).one()


@router.patch(
    "/read-all",
    response_model=int,
)
def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Mark all unread notifications belonging to the current user as read."""

    notifications = list(
        session.exec(
            select(Notification).where(
                Notification.user_id == current_user.id,
                Notification.is_read.is_(False),
            )
        ).all()
    )

    now = datetime.now(timezone.utc)

    for notification in notifications:
        notification.is_read = True
        notification.read_at = now
        session.add(notification)

    session.commit()

    return len(notifications)

@router.patch(
    "/bulk/archive",
    response_model=int,
)
def bulk_archive_notifications(
    request: NotificationBulkRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Archive selected notifications belonging to the current user."""

    notifications = list(
        session.exec(
            select(Notification).where(
                Notification.id.in_(request.notification_ids),
                Notification.user_id == current_user.id,
                Notification.is_archived.is_(False),
            )
        ).all()
    )

    now = datetime.now(timezone.utc)

    for notification in notifications:
        notification.is_archived = True
        notification.archived_at = now
        session.add(notification)

    session.commit()

    return len(notifications)

@router.patch(
    "/bulk/unarchive",
    response_model=int,
)
def bulk_unarchive_notifications(
    request: NotificationBulkRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Unarchive selected notifications belonging to the current user."""

    notifications = list(
        session.exec(
            select(Notification).where(
                Notification.id.in_(request.notification_ids),
                Notification.user_id == current_user.id,
                Notification.is_archived.is_(True),
            )
        ).all()
    )

    for notification in notifications:
        notification.is_archived = False
        notification.archived_at = None
        session.add(notification)

    session.commit()

    return len(notifications)

@router.patch(
    "/bulk/read",
    response_model=int,
)
def bulk_mark_notifications_read(
    request: NotificationBulkRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Mark selected notifications as read."""

    notifications = list(
        session.exec(
            select(Notification).where(
                Notification.id.in_(request.notification_ids),
                Notification.user_id == current_user.id,
                Notification.is_read.is_(False),
            )
        ).all()
    )

    now = datetime.now(timezone.utc)

    for notification in notifications:
        notification.is_read = True
        notification.read_at = now
        session.add(notification)

    session.commit()

    return len(notifications)

@router.patch(
    "/bulk/unread",
    response_model=int,
)
def bulk_mark_notifications_unread(
    request: NotificationBulkRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Mark selected notifications as unread."""

    notifications = list(
        session.exec(
            select(Notification).where(
                Notification.id.in_(request.notification_ids),
                Notification.user_id == current_user.id,
                Notification.is_read.is_(True),
            )
        ).all()
    )

    for notification in notifications:
        notification.is_read = False
        notification.read_at = None
        session.add(notification)

    session.commit()

    return len(notifications)

@router.delete(
    "/bulk",
    response_model=int,
)
def bulk_delete_notifications(
    request: NotificationBulkRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Delete selected notifications belonging to the current user."""

    notifications = list(
        session.exec(
            select(Notification).where(
                Notification.id.in_(request.notification_ids),
                Notification.user_id == current_user.id,
            )
        ).all()
    )

    for notification in notifications:
        session.delete(notification)

    session.commit()

    return len(notifications)

@router.get(
    "/{notification_id}",
    response_model=NotificationRead,
)
def get_notification(
    notification_id: Annotated[int, Path(ge=1)],
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Get one notification belonging to the current user."""

    notification = session.get(
        Notification,
        notification_id,
    )

    if (
        notification is None
        or notification.user_id != current_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found.",
        )

    return notification


@router.patch(
    "/{notification_id}/read",
    response_model=NotificationRead,
)
def mark_notification_read(
    notification_id: Annotated[int, Path(ge=1)],
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Mark one notification as read."""

    notification = session.get(
        Notification,
        notification_id,
    )

    if (
        notification is None
        or notification.user_id != current_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found.",
        )

    if not notification.is_read:
        notification.is_read = True
        notification.read_at = datetime.now(timezone.utc)

        session.add(notification)
        session.commit()
        session.refresh(notification)

    return notification

@router.patch(
    "/archive-all",
    response_model=int,
)
def archive_all_notifications(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Archive all active notifications belonging to the current user."""

    notifications = list(
        session.exec(
            select(Notification).where(
                Notification.user_id == current_user.id,
                Notification.is_archived.is_(False),
            )
        ).all()
    )

    now = datetime.now(timezone.utc)

    for notification in notifications:
        notification.is_archived = True
        notification.archived_at = now
        session.add(notification)

    session.commit()

    return len(notifications)

@router.delete(
    "/{notification_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_notification(
    notification_id: Annotated[int, Path(ge=1)],
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Delete one notification belonging to the current user."""

    notification = session.get(
        Notification,
        notification_id,
    )

    if (
        notification is None
        or notification.user_id != current_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found.",
        )

    session.delete(notification)
    session.commit()
    
@router.post(
    "/{notification_id}/retry",
    response_model=NotificationRead,
)
async def retry_notification(
    notification_id: Annotated[int, Path(ge=1)],
    current_user: User = Depends(get_current_user),
    service: NotificationService = Depends(
        get_notification_service
    ),
):
    """Retry a failed notification."""

    notification = service.session.get(
        Notification,
        notification_id,
    )

    if (
        notification is None
        or notification.user_id != current_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found.",
        )

    if not service.can_retry(notification):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Notification retry limit reached.",
        )

    await service.retry_delivery(notification)

    return notification

@router.patch(
    "/{notification_id}/archive",
    response_model=NotificationRead,
)
def archive_notification(
    notification_id: Annotated[int, Path(ge=1)],
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Archive one notification belonging to the current user."""

    notification = session.get(
        Notification,
        notification_id,
    )

    if (
        notification is None
        or notification.user_id != current_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found.",
        )

    if not notification.is_archived:
        notification.is_archived = True
        notification.archived_at = datetime.now(timezone.utc)

        session.add(notification)
        session.commit()
        session.refresh(notification)

    return notification

@router.patch(
    "/{notification_id}/unarchive",
    response_model=NotificationRead,
)
def unarchive_notification(
    notification_id: Annotated[int, Path(ge=1)],
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Unarchive one notification belonging to the current user."""

    notification = session.get(
        Notification,
        notification_id,
    )

    if (
        notification is None
        or notification.user_id != current_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found.",
        )

    if notification.is_archived:
        notification.is_archived = False
        notification.archived_at = None

        session.add(notification)
        session.commit()
        session.refresh(notification)

    return notification