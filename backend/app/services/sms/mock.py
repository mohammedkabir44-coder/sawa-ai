"""Mock SMS provider for local development.

Logs the outgoing message and returns a well-formed success response so the
SMS pipeline can be exercised end-to-end without external APIs.
"""
import logging
from typing import Any, Dict

from app.services.sms.base import SMSProvider

logger = logging.getLogger(__name__)


class MockSMSProvider(SMSProvider):
    """Simulates SMS sending without external calls.

    Every send is logged locally and acknowledged with a deterministic
    message id so callers (single sends, campaigns) can trace delivery.
    """

    # Shared counter so ids stay unique within a process.
    _count = 0

    def send_sms(self, to: str, body: str) -> Dict[str, Any]:
        MockSMSProvider._count += 1
        message_id = f"mock_{MockSMSProvider._count}"
        logger.info(
            "[mock-sms] to=%s message_id=%s body=%s", to, message_id, body
        )
        return {
            "success": True,
            "provider": "mock",
            "message_id": message_id,
            "to": to,
            "body": body,
        }