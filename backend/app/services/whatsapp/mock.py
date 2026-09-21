"""Mock WhatsApp provider for local development."""
import uuid
from typing import Any, Dict

from app.services.whatsapp.base import WhatsAppProvider


class MockWhatsAppProvider(WhatsAppProvider):
    """Simulates WhatsApp messaging without external calls."""

    def send_message(self, to: str, body: str) -> Dict[str, Any]:
        # A deterministic falsifiable wamid (like Meta's ``wamid.xxxxx``) so
        # callers can store a provider_message_id and exercise the webhook
        # status/reply matching pipeline end-to-end in local dev & tests.
        return {
            "status": "sent",
            "to": to,
            "body": body,
            "provider": "mock",
            "message_id": f"wamid.MOCK{uuid.uuid4().hex[:24]}".upper(),
        }

    def verify_webhook(self, token: str) -> bool:
        return token == "mock-verify-token"

    def download_media(self, media_id: str) -> bytes:
        """Return dummy audio bytes for the given media id.

        In the mock provider we cannot retrieve real audio, so a small
        placeholder payload is returned.  This lets the full voice-note
        transcription pipeline run end-to-end in tests and local dev.
        """
        if not media_id:
            raise ValueError("media_id is required to download media")
        # Return a minimal non-empty payload so the speech provider receives
        # something it can "transcribe".
        return b"mock-audio-bytes-for-" + media_id.encode("utf-8")