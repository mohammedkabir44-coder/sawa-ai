"""WhatsApp provider interface."""
from abc import ABC, abstractmethod
from typing import Any, Dict


class WhatsAppProvider(ABC):
    """Interface for WhatsApp messaging providers."""

    @abstractmethod
    def send_message(self, to: str, body: str) -> Dict[str, Any]:
        """Send a WhatsApp message to a recipient."""
        raise NotImplementedError

    @abstractmethod
    def verify_webhook(self, token: str) -> bool:
        """Verify an incoming webhook challenge token."""
        raise NotImplementedError

    @abstractmethod
    def download_media(self, media_id: str) -> bytes:
        """Download media (e.g. an audio note) referenced by media_id.

        Returns the raw media bytes so they can be fed to a Speech-to-Text
        provider.  Implementations must raise a clear error when the media
        cannot be retrieved rather than returning empty bytes silently.
        """
        raise NotImplementedError