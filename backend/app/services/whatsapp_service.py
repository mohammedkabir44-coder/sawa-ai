"""WhatsApp service for webhook verification, media download, and transcription."""
import hmac
import hashlib
import os
from typing import Any, Dict

import httpx
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def verify_whatsapp_signature(payload_bytes: bytes, signature_header: str, app_secret: str) -> bool:
    """Verifies X-Hub-Signature-256 header sent by Meta WhatsApp Cloud API.

    The signature header format is:  sha256=<hex_digest>
    We compute the expected digest using HMAC-SHA256 with the app secret
    and compare it against the incoming signature using constant-time comparison.
    """
    if not signature_header or not signature_header.startswith("sha256="):
        return False
    expected_sig = hmac.new(
        app_secret.encode("utf-8"),
        payload_bytes,
        hashlib.sha256,
    ).hexdigest()
    incoming_sig = signature_header.split("=")[1]
    return hmac.compare_digest(expected_sig, incoming_sig)


async def download_and_transcribe_whatsapp_audio(media_id: str) -> str:
    """
    Downloads audio media from Meta WhatsApp Cloud API and transcribes it via OpenAI Whisper.

    Args:
        media_id: The media ID from the WhatsApp webhook payload.

    Returns:
        The transcribed text from the audio.

    Raises:
        ValueError: If media metadata retrieval or audio download fails.
    """
    access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")

    async with httpx.AsyncClient() as http_client:
        # 1. Get media URL from Meta Graph API
        media_meta_res = await http_client.get(
            f"https://graph.facebook.com/v18.0/{media_id}",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        if media_meta_res.status_code != 200:
            raise ValueError("Failed to retrieve media metadata from WhatsApp")

        media_url = media_meta_res.json().get("url")

        # 2. Download the audio file bytes
        audio_res = await http_client.get(
            media_url,
            headers={"Authorization": f"Bearer {access_token}"}
        )
        if audio_res.status_code != 200:
            raise ValueError("Failed to download audio binary from WhatsApp")

        audio_bytes = audio_res.content

    # 3. Save temporarily and transcribe with OpenAI Whisper
    temp_filename = f"/tmp/{media_id}.ogg"
    with open(temp_filename, "wb") as f:
        f.write(audio_bytes)

    try:
        with open(temp_filename, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                prompt="Hausa and English commerce orders (e.g., Ankara fabric, shoes, naira)"
            )
        return transcript.text
    finally:
        if os.path.exists(temp_filename):
            os.remove(temp_filename)