import json
from urllib import error, request

from app.core.config import settings
from app.notifications.exceptions import NotificationProviderError
from app.notifications.providers.base import NotificationProviderBase
from app.notifications.types import NotificationMessage


class SlackNotificationProvider(NotificationProviderBase):
    """Slack Incoming Webhook notification provider."""

    @property
    def name(self) -> str:
        return "slack"

    def _validate_configuration(self) -> None:
        """Validate Slack configuration."""

        if not settings.SLACK_WEBHOOK_URL:
            raise NotificationProviderError(
                "SLACK_WEBHOOK_URL is not configured."
            )

    def _build_payload(
        self,
        notification: NotificationMessage,
    ) -> dict:
        """Build Slack webhook payload."""

        return {
            "text": (
                f"*{notification.subject}*\n"
                f"{notification.message}"
            ),
        }

    def _send_sync(
        self,
        payload: dict,
    ) -> None:
        """Send payload to Slack webhook."""

        body = json.dumps(payload).encode("utf-8")

        http_request = request.Request(
            settings.SLACK_WEBHOOK_URL,
            data=body,
            headers={
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with request.urlopen(
                http_request,
                timeout=settings.SLACK_TIMEOUT,
            ) as response:

                status_code = response.status

                if status_code < 200 or status_code >= 300:
                    raise NotificationProviderError(
                        f"Slack returned HTTP {status_code}."
                    )

        except error.HTTPError as exc:
            raise NotificationProviderError(
                f"Slack returned HTTP {exc.code}."
            ) from exc

        except error.URLError as exc:
            raise NotificationProviderError(
                f"Slack connection failed: {exc.reason}"
            ) from exc

        except TimeoutError as exc:
            raise NotificationProviderError(
                "Slack request timed out."
            ) from exc

    async def send(
        self,
        notification: NotificationMessage,
    ) -> bool:
        """Send notification to Slack."""

        self._validate_configuration()

        payload = self._build_payload(notification)

        self._send_sync(payload)

        return True