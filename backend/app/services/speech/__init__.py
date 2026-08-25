"""Speech-to-text provider factory."""
import logging

from app.core.config import settings
from app.services.speech.base import SpeechProvider
from app.services.speech.mock import MockSpeechProvider

logger = logging.getLogger(__name__)


def get_speech_provider() -> SpeechProvider:
    """Return the configured Speech-to-Text provider.

    Controlled by the ``SPEECH_PROVIDER`` environment variable.
    Real providers are only used when credentials are present; the mock
    is the safe default for local development and tests.
    """
    provider = settings.SPEECH_PROVIDER.lower()

    if provider == "gemini" and settings.GEMINI_API_KEY:
        try:
            from app.services.speech.gemini import GeminiSpeechProvider

            return GeminiSpeechProvider(api_key=settings.GEMINI_API_KEY)
        except ImportError:
            logger.warning(
                "SPEECH_PROVIDER=gemini but Gemini speech provider is "
                "not installed; falling back to MockSpeechProvider."
            )

    # Default: clearly-labelled mock provider for development.
    return MockSpeechProvider()


__all__ = ["SpeechProvider", "get_speech_provider"]