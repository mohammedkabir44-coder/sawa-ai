"""WhatsApp Commerce Engine endpoints: webhook verification and order flow.

This module implements the WhatsApp Commerce Engine — a flow that lets
customers place orders via WhatsApp text messages.  The flow is:

1. Customer sends a WhatsApp message (text or voice note).
2. The webhook endpoint receives the message.
3. The AI intent parser extracts structured intent (product, quantity,
   address, language).
4. The order service creates an :class:`Order` and generates a Paystack
   checkout URL.
5. A reply message with the payment link is sent back to the customer.
"""
import hmac
import hashlib
import json
import logging
import os
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.product import Product
from app.models.whatsapp import WhatsAppMessage, WhatsAppAccount
from app.services.ai.language import detect_language
from app.services.ai.parser import parse_customer_intent
from app.services.order_service import create_order_from_intent
from app.services.workflow_engine import (
    send_whatsapp_message,
    trigger_automations,
)
from app.services.speech import get_speech_provider
from app.services.whatsapp import get_whatsapp_provider

router = APIRouter(prefix="/whatsapp-commerce", tags=["whatsapp-commerce"])

logger = logging.getLogger(__name__)


class ParseMessageRequest(BaseModel):
    message: str


# Verify token for webhook subscription (Meta Cloud API)
WHATSAPP_VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "sawatoken123")
WHATSAPP_APP_SECRET = os.getenv("WHATSAPP_APP_SECRET", "")


def _is_production() -> bool:
    """Best-effort production check.

    Falls back to "development" if the setting isn't defined, so this
    module doesn't hard-fail in environments where ENVIRONMENT isn't set.
    """
    return getattr(settings, "ENVIRONMENT", "development").lower() == "production"


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _resolve_business_id(
    db: Session,
    msg: Dict[str, Any],
    value: Dict[str, Any],
) -> Optional[int]:
    """Resolve the tenant ``business_id`` from the WhatsApp webhook payload.

    Meta's webhook payload carries the business phone number in two places:

    * ``messages[].to`` – the business phone number the message was sent to.
    * ``value.metadata.phone_number_id`` – the WhatsApp Business Account
      phone-number ID.

    We try both against the :class:`WhatsAppAccount` table.  If neither
    matches (e.g. in tests or when the account isn't configured yet) we
    return ``None`` so the caller can decide how to handle it — the caller
    must NOT blindly default this to a real tenant's business_id in
    production, since that would misattribute the order/customer data.
    """
    # 1. Try the ``to`` field on the message (business phone number).
    to_number = msg.get("to", "")
    if to_number:
        account = db.scalar(
            select(WhatsAppAccount).where(
                WhatsAppAccount.phone_number == to_number
            )
        )
        if account is not None:
            return account.business_id

    # 2. Try the phone_number_id from metadata.
    metadata = value.get("metadata", {})
    phone_number_id = metadata.get("phone_number_id", "")
    if phone_number_id:
        account = db.scalar(
            select(WhatsAppAccount).where(
                WhatsAppAccount.phone_number_id == phone_number_id
            )
        )
        if account is not None:
            return account.business_id

    return None


def _get_product_catalog(db: Session, business_id: int) -> List[Dict[str, Any]]:
    """Build a product catalog summary for the AI parser.

    Returns a list of dicts with ``id``, ``name``, ``price`` and
    ``stock_quantity`` keys, matching the schema expected by
    :func:`parse_customer_intent`.
    """
    products = (
        db.query(Product)
        .filter(
            Product.business_id == business_id,
            Product.is_active.is_(True),
        )
        .all()
    )
    return [
        {
            "id": p.id,
            "name": p.name,
            "price": p.price,
            "stock_quantity": p.stock,
        }
        for p in products
    ]


def _pay_link_text(language: str) -> str:
    """Return a localized 'pay here' label based on detected language.

    `language` should be one of the values returned by
    `app.services.ai.language.detect_language` ("en", "ha", "ha-en",
    "unknown") — the single source of truth for language classification,
    so the pay-link label never drifts from whatever the AI parser itself
    reports (or fails to report).
    """
    if language in ("ha", "ha-en"):
        return "Suyi da haka"
    return "Pay here"


def _verify_webhook_signature(body_bytes: bytes, signature_header: str) -> None:
    """Verify the Meta X-Hub-Signature-256 HMAC, enforcing it in production.

    * In production, WHATSAPP_APP_SECRET must be configured and every
      request must carry a valid signature — otherwise the webhook is
      wide open to forged order-creation requests.
    * Outside production (local dev / tests), verification is skipped if
      no app secret is configured, to keep local setup friction-free.
    """
    if _is_production() and not WHATSAPP_APP_SECRET:
        # Fail loudly rather than silently accepting unauthenticated
        # webhooks in production.
        logger.critical(
            "WHATSAPP_APP_SECRET is not configured in production; "
            "refusing to process webhook."
        )
        raise HTTPException(status_code=500, detail="Webhook not configured")

    if not WHATSAPP_APP_SECRET:
        # No secret configured and we're not in production — allow
        # through for local/dev convenience.
        return

    if not signature_header:
        raise HTTPException(status_code=403, detail="Missing signature")

    expected_sig = hmac.new(
        WHATSAPP_APP_SECRET.encode("utf-8"),
        body_bytes,
        hashlib.sha256,
    ).hexdigest()
    incoming_sig = signature_header.split("=")[1] if "=" in signature_header else ""
    if not hmac.compare_digest(expected_sig, incoming_sig):
        raise HTTPException(status_code=403, detail="Invalid signature")


async def _process_text_message(
    db: Session, msg: Dict[str, Any], value: Dict[str, Any]
) -> None:
    """Process a single inbound text message through the commerce flow.

    Isolated into its own function so the webhook loop can catch and log
    a failure on one message without dropping the rest of the batch or
    returning a 5xx to Meta (which would trigger aggressive retries of
    the entire payload, including messages that already succeeded).
    """
    from_number = msg.get("from", "")
    text_body = msg.get("text", {}).get("body", "")

    # Resolve the tenant business_id from the WhatsApp account mapping
    # (phone number or phone_number_id).
    resolved_business_id = _resolve_business_id(db, msg, value)
    if resolved_business_id is None:
        if _is_production():
            # Do NOT default to business_id=1 in production — that would
            # silently misattribute this order/customer to whichever
            # tenant happens to own id 1. Drop the message and log it
            # for investigation instead.
            logger.warning(
                "Could not resolve business_id for inbound WhatsApp "
                "message from %s; no matching WhatsAppAccount found. "
                "Message dropped.",
                from_number,
            )
            return
        # Local dev / tests: no WhatsAppAccount configured yet.
        resolved_business_id = 1
    business_id = resolved_business_id

    # Fetch the product catalog for this business so the AI parser can
    # match product names and check stock.
    product_catalog = _get_product_catalog(db, business_id)

    # Determine language once, from our own deterministic detector, so
    # every downstream use (AI parser context + pay-link label) agrees.
    detected = detect_language(text_body)

    # Step 1: Parse customer intent with AI (GPT-4o).
    parsed_intent = parse_customer_intent(text_body, product_catalog)

    # Step 2: Create order and generate Paystack link.
    if parsed_intent.get("intent") == "place_order":
        order_result = await create_order_from_intent(
            db=db,
            whatsapp_id=from_number,
            parsed_intent=parsed_intent,
            business_id=business_id,
        )
        if order_result.get("success"):
            # Step 3: Dispatch WhatsApp message with payment link. Use
            # the AI-parsed reply_message and append the checkout URL.
            checkout_url = order_result.get("checkout_url", "")
            ai_reply = parsed_intent.get("reply_message", "")
            # Prefer the AI parser's own language field when it reports
            # one; fall back to our deterministic detector otherwise, so
            # the label never silently defaults to English.
            language = parsed_intent.get("detected_language") or detected.language
            if checkout_url:
                reply = f"{ai_reply}\n\n{_pay_link_text(language)} {checkout_url}"
            else:
                reply = ai_reply
            await send_whatsapp_message(from_number, reply)


async def _process_audio_message(
    db: Session, msg: Dict[str, Any], value: Dict[str, Any]
) -> None:
    """Process an inbound voice note through transcription + commerce flow.

    1. Download the audio via the WhatsApp provider.
    2. Transcribe it with the speech-to-text provider.
    3. Persist the transcript on a :class:`WhatsAppMessage` record.
    4. Feed the transcript into the standard text-message flow so the AI
       parser can detect intent and trigger auto-reply / order creation.
    """
    from_number = msg.get("from", "")

    # 1. Extract the media id from the audio payload (Meta sends it in
    #    msg["audio"]["id"]).
    audio_data = msg.get("audio", {}) or {}
    media_id = audio_data.get("id", "")
    if not media_id:
        logger.warning(
            "Audio message from %s has no media id; skipping transcription",
            from_number,
        )
        return

    # 2. Download the audio bytes via the WhatsApp provider.
    wp_provider = get_whatsapp_provider()
    try:
        audio_bytes = wp_provider.download_media(media_id)
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to download media %s: %s", media_id, exc)
        return

    # 3. Transcribe with the speech-to-text provider.
    speech_provider = get_speech_provider()
    transcript_result = speech_provider.transcribe(audio_bytes)
    transcript = transcript_result.get("text", "") or ""
    logger.info(
        "Transcribed voice note from %s: %s", from_number, transcript[:100]
    )

    # 4. Resolve the tenant business_id (same logic as text messages).
    business_id = _resolve_business_id(db, msg, value)
    if business_id is None:
        if _is_production():
            logger.warning(
                "Could not resolve business_id for inbound audio from %s; "
                "message dropped.",
                from_number,
            )
            return
        business_id = 1

    # 5. Persist the transcript on a WhatsAppMessage record (best-effort —
    #    won't block the commerce flow if the DB lacks an account row).
    try:
        account = (
            db.query(WhatsAppAccount)
            .filter(
                WhatsAppAccount.business_id == business_id,
                WhatsAppAccount.is_connected.is_(True),
            )
            .first()
        )
        if account:
            message_record = WhatsAppMessage(
                business_id=business_id,
                account_id=account.id,
                to_number=msg.get("to", ""),
                from_number=from_number,
                message_text=transcript,
                message_type="audio",
                media_url=audio_data.get("url", ""),
                media_id=media_id,
                transcript=transcript,
                direction="inbound",
                status="received",
            )
            db.add(message_record)
            db.commit()
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        logger.warning("Could not persist audio transcript message: %s", exc)

    # 6. Feed the transcript into the standard text-message commerce flow.
    text_msg = {**msg, "type": "text", "text": {"body": transcript}}
    await _process_text_message(db, text_msg, value)


# --------------------------------------------------------------------------- #
# Endpoints
# --------------------------------------------------------------------------- #
@router.get("/webhook", response_class=PlainTextResponse)
async def verify_webhook(
    hub_mode: str = Query(..., alias="hub.mode"),
    hub_verify_token: str = Query(..., alias="hub.verify_token"),
    hub_challenge: str = Query(..., alias="hub.challenge"),
) -> str:
    """Verify the WhatsApp webhook subscription challenge."""
    if hub_mode == "subscribe" and hub_verify_token == WHATSAPP_VERIFY_TOKEN:
        return hub_challenge
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/parse")
async def parse_message(payload: ParseMessageRequest) -> Dict[str, Any]:
    """Parse a customer message using AI intent parser (GPT-4o)."""
    parsed = parse_customer_intent(payload.message, [])
    return parsed


@router.post("/webhook")
async def receive_webhook(
    request: Request,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Receive WhatsApp webhook events (messages, statuses, etc.).

    The raw request body is read **first** so that the HMAC signature can
    be verified before the JSON is parsed.  This avoids the common pitfall
    of consuming the body stream with ``request.json()`` before
    ``request.body()`` is called.
    """
    # 1. Read the raw body bytes (needed for signature verification).
    body_bytes = await request.body()

    # 2. Verify signature (enforced in production; skippable in dev when
    #    no app secret is configured — see _verify_webhook_signature).
    signature_header = request.headers.get("X-Hub-Signature-256", "")
    _verify_webhook_signature(body_bytes, signature_header)

    # 3. Parse the JSON payload from the already-read body.
    try:
        payload = json.loads(body_bytes)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    # 4. Extract incoming WhatsApp messages, keeping the parent ``value``
    #    dict so we can resolve the business_id later.
    messages: List[Tuple[Dict[str, Any], Dict[str, Any]]] = []
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            for msg in value.get("messages", []):
                messages.append((msg, value))

    # 5. Process each incoming message through the commerce flow. Each
    #    message is isolated in its own try/except so one bad or
    #    unexpected message can't take down the whole webhook request
    #    (which would cause Meta to retry the entire batch).
    for msg, value in messages:
        msg_type = msg.get("type", "")
        try:
            if msg_type == "audio":
                await _process_audio_message(db, msg, value)
            elif msg_type == "text":
                await _process_text_message(db, msg, value)
            else:
                # Ignore unsupported message types (images, documents,
                # stickers, reactions, etc.) without erroring the batch.
                logger.info(
                    "Ignoring unsupported WhatsApp message type=%s from=%s",
                    msg_type,
                    msg.get("from"),
                )
                continue
        except Exception:
            logger.exception(
                "Failed to process WhatsApp message id=%s from=%s type=%s",
                msg.get("id"),
                msg.get("from"),
                msg_type,
            )
            continue

        # Fire any automations matching the whatsapp_message_received trigger.
        try:
            automation_business_id = _resolve_business_id(db, msg, value)
            if automation_business_id is not None:
                await trigger_automations(
                    automation_business_id,
                    "whatsapp_message_received",
                    {
                        "phone": msg.get("from", ""),
                        "text": msg.get("text", {}).get("body", ""),
                        "type": msg_type,
                        "business_id": automation_business_id,
                    },
                )
        except Exception:
            logger.exception(
                "Failed to fire automations for message id=%s", msg.get("id")
            )

    return {"status": "success"}
