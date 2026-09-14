"""Meta (Facebook) WhatsApp Cloud API provider.

Implements the WhatsAppProvider interface using the Meta Graph API via httpx.
Selected when WHATSAPP_PROVIDER=meta (see app.services.whatsapp.get_whatsapp_provider
for the factory). The provider is constructed with **per-account** credentials —
the access token stored (encrypted) on the WhatsAppAccount row and the
account's phone-number ID — so every tenant's messages go out through their
own connected WhatsApp Business number.
"""
import logging
from typing import Any, Dict

import httpx

from app.core.config import settings
from app.services.whatsapp.base import WhatsAppProvider

logger = logging.getLogger(__name__)

# Meta error subcodes we understand; anything else is reported generically.
_RATE_LIMIT_CODES = {130429, 131048, 131026}
_TRANSIENT_CODES = {1, 2, 130050}


def _error_detail(payload: Dict[str, Any], status_code: int) -> str:
    """Extract a human-readable message from a Meta error payload."""
    error = payload.get("error") or {}
    message = error.get("message") or payload.get("message") or "Unknown error"
    code = error.get("code")
    subcode = error.get("error_subcode")
    if subcode in _RATE_LIMIT_CODES or code in _RATE_LIMIT_CODES:
        return f"Rate limited by Meta (code={code}, subcode={subcode})"
    if status_code == 429:
        return "Rate limited by Meta (HTTP 429)"
    if code == 131026 or status_code == 412:
        return "Message content rejected by Meta — check template approval / consent"
    if subcode == 133010:
        return "Permission error — the token may lack whatsapp_business_messaging scope"
    if status_code in (401, 403):
        return "Authentication failed — check the access token"
    return f"Meta API error (HTTP {status_code}): {message}"


class MetaWhatsAppProvider(WhatsAppProvider):
    """WhatsApp provider that communicates with the Meta Graph API.

    Args:
        access_token: Long-lived access token for the Meta Cloud API
            (the decrypted ``api_key`` from the tenant's WhatsAppAccount).
        phone_number_id: The WhatsApp Business Account phone-number ID.
    """

    BASE_URL = "https://graph.facebook.com/v18.0"

    def __init__(self, access_token: str, phone_number_id: str) -> None:
        self.access_token = access_token
        self.phone_number_id = phone_number_id

    def send_message(self, to: str, body: str) -> Dict[str, Any]:
        """Send a text message via the Meta Graph API.

        POSTs to /{phone_number_id}/messages and extracts the WhatsApp
        message ID (wamid) from the response so callers can store it as
        ``provider_message_id`` for webhook matching.

        Returns:
            On success: {"status": "sent", "message_id": <wamid>, "response": ...}
            On failure: {"status": "error", "detail": ..., "status_code": ...}
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
            "recipient_type": "individual",
            "text": {"body": body},
        }
        try:
            response = httpx.post(url, headers=headers, json=payload, timeout=30.0)
            if response.status_code >= 400:
                try:
                    body_json = response.json()
                except ValueError:
                    body_json = {}
                logger.error(
                    "Meta WhatsApp API error (HTTP %s): %s",
                    response.status_code,
                    body_json,
                )
                return {
                    "status": "error",
                    "detail": _error_detail(body_json, response.status_code),
                    "status_code": response.status_code,
                }
            data = response.json()
            messages = data.get("messages") or []
            message_id = messages[0].get("id", "") if messages else ""
            return {"status": "sent", "message_id": message_id, "response": data}
        except httpx.TimeoutException:
            logger.error("Meta WhatsApp API timed out sending to %s", to)
            return {"status": "error", "detail": "Meta API timed out", "status_code": 504}
        except httpx.RequestError as exc:
            logger.error("Meta WhatsApp API request failed: %s", exc)
            return {"status": "error", "detail": f"Network error: {exc}", "status_code": 0}
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to send WhatsApp message: %s", exc)
            return {"status": "error", "detail": str(exc), "status_code": 0}

    def verify_webhook(self, token: str) -> bool:
        """Verify the webhook subscription challenge token.

        Compares the incoming token against WHATSAPP_VERIFY_TOKEN from
        application settings.
        """
        return token == settings.WHATSAPP_VERIFY_TOKEN

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