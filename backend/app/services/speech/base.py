"""Speech-to-text provider interface."""
from abc import ABC, abstractmethod
from typing import Any, Dict


class SpeechProvider(ABC):
    """Interface for speech-to-text providers."""

    @abstractmethod
    def transcribe(self, audio: bytes, language: str = "en") -> Dict[str, Any]:
        """Transcribe audio bytes into text."""
        raise NotImplementedError