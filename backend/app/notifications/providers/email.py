from email.message import EmailMessage
from typing import Optional

import smtplib

from app.core.config import settings
from app.notifications.exceptions import NotificationProviderError
from app.notifications.providers.base import NotificationProviderBase
from app.notifications.types import NotificationMessage


class EmailNotificationProvider(NotificationProviderBase):
    """SMTP-based email notification provider."""

    @property
    def name(self) -> str:
        return "email"

    def _validate_configuration(self) -> None:
        """Validate required SMTP configuration."""

        if not settings.SMTP_HOST:
            raise NotificationProviderError(
                "SMTP_HOST is not configured."
            )

        if not settings.SMTP_FROM_EMAIL:
            raise NotificationProviderError(
                "SMTP_FROM_EMAIL is not configured."
            )

        if settings.SMTP_USE_TLS and settings.SMTP_PORT == 465:
            raise NotificationProviderError(
                "SMTP port 465 is normally used with SSL, "
                "not STARTTLS."
            )

    def _build_message(
        self,
        notification: NotificationMessage,
        recipient: str,
        html: Optional[str] = None,
    ) -> EmailMessage:
        """Build an email message."""

        if not recipient:
            raise NotificationProviderError(
                "Email recipient is required."
            )

        email = EmailMessage()

        email["Subject"] = notification.subject
        email["From"] = (
            f"{settings.SMTP_FROM_NAME} "
            f"<{settings.SMTP_FROM_EMAIL}>"
        )
        email["To"] = recipient

        email.set_content(notification.message)

        if html:
            email.add_alternative(
                html,
                subtype="html",
            )

        return email

    def _send_sync(
        self,
        email: EmailMessage,
    ) -> None:
        """Send email synchronously through SMTP."""

        try:
            with smtplib.SMTP(
                settings.SMTP_HOST,
                settings.SMTP_PORT,
                timeout=30,
            ) as smtp:

                smtp.ehlo()

                if settings.SMTP_USE_TLS:
                    smtp.starttls()
                    smtp.ehlo()

                if settings.SMTP_USERNAME:
                    smtp.login(
                        settings.SMTP_USERNAME,
                        settings.SMTP_PASSWORD,
                    )

                smtp.send_message(email)

        except Exception as exc:
            raise NotificationProviderError(
                f"Failed to send email: {exc}"
            ) from exc

    async def send(
        self,
        notification: NotificationMessage,
    ) -> bool:
        """Send an email notification."""

        self._validate_configuration()

        if not notification.recipient:
            raise NotificationProviderError(
                "Email recipient is required."
            )

        email = self._build_message(
            notification,
            notification.recipient,
        )

        self._send_sync(email)

        return True