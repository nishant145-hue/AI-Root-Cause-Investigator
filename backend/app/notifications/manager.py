from .exceptions import UnsupportedNotificationProvider
from .providers.base import NotificationProviderBase
from .types import NotificationMessage


class NotificationManager:
    """
    Central manager responsible for dispatching notifications
    to registered providers.
    """

    def __init__(self) -> None:
        self._providers: dict[str, NotificationProviderBase] = {}

    def register_provider(
        self,
        provider: NotificationProviderBase,
    ) -> None:
        """Register a notification provider."""

        self._providers[provider.name] = provider

    def get_provider(
        self,
        provider_name: str,
    ) -> NotificationProviderBase:
        """Return a registered provider."""

        provider = self._providers.get(provider_name)

        if provider is None:
            raise UnsupportedNotificationProvider(
                f"Notification provider '{provider_name}' is not registered."
            )

        return provider

    async def send(
        self,
        provider_name: str,
        notification: NotificationMessage,
    ) -> bool:
        """Send a notification through a specific provider."""

        provider = self.get_provider(provider_name)

        return await provider.send(notification)
    
    def list_providers(self) -> list[str]:
        """Return names of all registered providers."""

        return sorted(self._providers.keys())