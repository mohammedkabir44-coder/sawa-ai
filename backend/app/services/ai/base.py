"""AI provider interface."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class AIResponse:
    text: str
    language: str = "en"
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class AIProvider(ABC):
    """Interface for AI conversation providers.

    Implementations must never invent prices, products, availability,
    delivery timelines, policies, or promises. They must answer only
    from the provided business knowledge and say when information is
    unavailable.
    """

    @abstractmethod
    def generate_response(
        self,
        message: str,
        language: str,
        business_context: Dict[str, Any],
        conversation_history: List[Dict[str, Any]],
    ) -> AIResponse:
        """Generate a customer-facing response."""
        raise NotImplementedError

    @abstractmethod
    def generate_campaign(
        self,
        prompt: str,
        business_context: Dict[str, Any],
    ) -> Dict[str, str]:
        """Generate a campaign draft (title + messages)."""
        raise NotImplementedError