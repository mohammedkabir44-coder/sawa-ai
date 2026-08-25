"""Mock speech-to-text provider for local development.

Returns a dummy transcript with a *detected* language so that the voice-note
pipeline can be exercised end-to-end without real audio or external APIs.
"""
from typing import Any, Dict

from app.services.ai.language import detect_language
from app.services.speech.base import SpeechProvider


class MockSpeechProvider(SpeechProvider):
    """Simulates transcription without external calls.

    The returned text is a short Hausa phrase so that downstream language
    detection and AI parsing receive realistic, non-English input during
    development and tests.
    """

    # A short Hausa phrase that the mock "transcribes" from any audio.
    _DUMMY_TRANSCRIPT = "Ina son saya Ankara Fabric guda daya, don Kano"

    def transcribe(self, audio: bytes, language: str = "en") -> Dict[str, Any]:
        transcript = self._DUMMY_TRANSCRIPT
        detected = detect_language(transcript)
        return {
            "text": transcript,
            "language": detected.language,
            "detected_language": detected.language,
            "hausa_ratio": detected.hausa_ratio,
            "provider": "mock",
            "input_language": language,
        }