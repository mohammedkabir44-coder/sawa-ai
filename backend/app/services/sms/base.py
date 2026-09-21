"""SMS provider interface."""
from abc import ABC, abstractmethod
from typing import Any, Dict


class SMSProvider(ABC):
    """Interface for SMS messaging providers."""

    @abstractmethod
    def send_sms(self, to: str, body: str) -> Dict[str, Any]:
        """Send an SMS message to a recipient."""
        raise NotImplementedError