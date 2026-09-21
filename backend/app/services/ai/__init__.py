"""AI provider factory."""
from app.core.config import settings
from app.services.ai.base import AIProvider, AIResponse
from app.services.ai.mock import MockAIProvider


def get_ai_provider() -> AIProvider:
    """Return the configured AI provider.

    Controlled by the AI_PROVIDER environment variable.
    Real providers are only used when credentials are present.
    """
    provider = settings.AI_PROVIDER.lower()
    if provider == "gemini" and settings.GEMINI_API_KEY:
        from app.services.ai.gemini import GeminiProvider

        return GeminiProvider(api_key=settings.GEMINI_API_KEY)
    # Default to the clearly-labelled mock provider for development.
    return MockAIProvider()


__all__ = ["AIProvider", "AIResponse", "get_ai_provider"]