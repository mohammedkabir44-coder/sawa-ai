"""Meta (Facebook) WhatsApp Cloud API provider.

Phase 6 stub - implements the WhatsAppProvider interface using the
Meta Graph API via httpx.  In production this provider is selected when
WHATSAPP_PROVIDER=meta and WHATSAPP_ACCESS_TOKEN is set (see
app.services.whatsapp.get_whatsapp_provider).

The real implementation will add retry logic, rate-limit handling, and proper
error mapping.  For now this makes a straightforward HTTP call to the Meta
Graph API.
"""
import logging
from typing import Any, Dict

import httpx

from app.core.config import settings
from app.services.whatsapp.base import WhatsAppProvider

logger = logging.getLogger(__name__)


class MetaWhatsAppProvider(WhatsAppProvider):
    """WhatsApp provider that communicates with the Meta Graph API.

    Args:
        access_token: Long-lived access token for the Meta Cloud API.
        phone_number_id: The WhatsApp Business Account phone-number ID.
    """

    BASE_URL = "https://graph.facebook.com/v18.0"

    def __init__(self, access_token: str, phone_number_id: str) -> None:
        self.access_token = access_token
        self.phone_number_id = phone_number_id

    def send_message(self, to: str, body: str) -> Dict[str, Any]:
        """Send a text message via the Meta Graph API.

        Uses httpx to POST to /{phone_number_id}/messages.

        Returns:
            A dict with status ("success" or "error") and either a
            response key (on success) or a detail key (on failure).
        """
        url = f"{self.BASE_URL}/{self.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": body},
        }
        try:
            response = httpx.post(url, headers=headers, json=payload, timeout=30.0)
            response.raise_for_status()
            return {"status": "success", "response": response.json()}
        except httpx.HTTPStatusError as exc:
            logger.error("Meta WhatsApp API error: %s", exc)
            return {"status": "error", "detail": str(exc)}
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to send WhatsApp message: %s", exc)
            return {"status": "error", "detail": str(exc)}

    def verify_webhook(self, token: str) -> bool:
        """Verify the webhook subscription challenge token.

        Compares the incoming token against WHATSAPP_VERIFY_TOKEN from
        application settings.
        """
        return token == settings.WHATSAPP_VERIFY_TOKEN

    def download_media(self, media_id: str) -> bytes:
        """Download media (audio/image/document) from the Meta Graph API.

        Implements the two-step Meta retrieval pattern:

        1. GET /{media_id} -- returns JSON containing a temporary
           url pointing at the CDN where the media lives.
        2. GET <url> -- downloads the actual media bytes.

        Args:
            media_id: The id from the webhook message's audio.id
                (or image.id / document.id) field.

        Returns:
            Raw media bytes.

        Raises:
            httpx.HTTPStatusError: if either HTTP request fails.
        """
        if not media_id:
            raise ValueError("media_id is required to download media")

        # Step 1 -- resolve the CDN download URL.
        meta_url = f"{self.BASE_URL}/{media_id}"
        meta_headers = {
            "Authorization": f"Bearer {self.access_token}",
        }
        response = httpx.get(meta_url, headers=meta_headers, timeout=30.0)
        response.raise_for_status()
        media_info = response.json()
        cdn_url = media_info.get("url")
        if not cdn_url:
            raise ValueError(
                f"Meta Graph API did not return a download url for media {media_id}"
            )

        # Step 2 -- download the actual media bytes from the CDN.
        download_resp = httpx.get(cdn_url, timeout=30.0)
        download_resp.raise_for_status()
        return download_resp.content