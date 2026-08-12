from abc import ABC, abstractmethod

from ..types import NotificationMessage


class NotificationProviderBase(ABC):
    """Abstract interface for notification providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the provider name."""
        raise NotImplementedError

    @abstractmethod
    async def send(self, notification: NotificationMessage) -> bool:
        """
        Send a notification.

        Returns:
            True if delivery succeeds, otherwise False.
        """
        raise NotImplementedError