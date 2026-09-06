"""WhatsApp Commerce Engine endpoints: webhook verification and order flow."""
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

WHATSAPP_VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "sawatoken123")
WHATSAPP_APP_SECRET = os.getenv("WHATSAPP_APP_SECRET", "")

def _resolve_business_id(db: Session, msg: Dict[str, Any], value: Dict[str, Any]) -> Optional[int]:
    to_number = msg.get("to", "")
    if to_number:
        account = db.scalar(select(WhatsAppAccount).where(WhatsAppAccount.phone_number == to_number))
        if account is not None: return account.business_id
    metadata = value.get("metadata", {})
    phone_number_id = metadata.get("phone_number_id", "")
    if phone_number_id:
        account = db.scalar(select(WhatsAppAccount).where(WhatsAppAccount.phone_number_id == phone_number_id))
        if account is not None: return account.business_id
    return None

def _get_product_catalog(db: Session, business_id: int) -> List[Dict[str, Any]]:
    products = db.query(Product).filter(Product.business_id == business_id, Product.is_active.is_(True)).all()
    return [{"id": p.id, "name": p.name, "price": p.price, "stock_quantity": p.stock} for p in products]

def _pay_link_text(language: str) -> str:
    return "Suyi da haka" if language in ("ha", "ha-en") else "Pay here"

def _verify_webhook_signature(body_bytes: bytes, signature_header: str) -> None:
    if not WHATSAPP_APP_SECRET:
        return
    if not signature_header:
        raise HTTPException(status_code=403, detail="Missing signature")
    expected_sig = hmac.new(WHATSAPP_APP_SECRET.encode("utf-8"), body_bytes, hashlib.sha256).hexdigest()
    incoming_sig = signature_header.split("=")[1] if "=" in signature_header else ""
    if not hmac.compare_digest(expected_sig, incoming_sig):
        raise HTTPException(status_code=403, detail="Invalid signature")

async def _process_text_message(db: Session, msg: Dict[str, Any], value: Dict[str, Any]) -> None:
    from_number = msg.get("from", "")
    text_body = msg.get("text", {}).get("body", "")

    resolved_business_id = _resolve_business_id(db, msg, value)
    # FIXED: Always fallback to Sodangi (Business 1) if no account is found
    if resolved_business_id is None:
        resolved_business_id = 1
    business_id = resolved_business_id

    product_catalog = _get_product_catalog(db, business_id)
    detected = detect_language(text_body)

    parsed_intent = parse_customer_intent(text_body, product_catalog)
    ai_reply = parsed_intent.get("reply_message", "")
    language = parsed_intent.get("detected_language") or detected.language

    if parsed_intent.get("intent") == "place_order":
        order_result = await create_order_from_intent(
            db=db, whatsapp_id=from_number,
            parsed_intent=parsed_intent, business_id=business_id,
        )
        if order_result.get("success"):
            checkout_url = order_result.get("checkout_url", "")
            if checkout_url:
                ai_reply = f"{ai_reply}\n\n{_pay_link_text(language)} {checkout_url}"

    if ai_reply:
        await send_whatsapp_message(from_number, ai_reply)

async def _process_audio_message(db: Session, msg: Dict[str, Any], value: Dict[str, Any]) -> None:
    from_number = msg.get("from", "")
    audio_data = msg.get("audio", {}) or {}
    media_id = audio_data.get("id", "")
    if not media_id: return

    wp_provider = get_whatsapp_provider()
    try:
        audio_bytes = wp_provider.download_media(media_id)
    except Exception:
        return

    speech_provider = get_speech_provider()
    transcript = speech_provider.transcribe(audio_bytes).get("text", "") or ""

    business_id = _resolve_business_id(db, msg, value)
    if business_id is None:
        business_id = 1

    try:
        account = db.query(WhatsAppAccount).filter(WhatsAppAccount.business_id == business_id, WhatsAppAccount.is_connected.is_(True)).first()
        if account:
            db.add(WhatsAppMessage(business_id=business_id, account_id=account.id, to_number=msg.get("to", ""), from_number=from_number, message_text=transcript, message_type="audio", media_id=media_id, transcript=transcript, direction="inbound", status="received"))
            db.commit()
    except Exception:
        db.rollback()

    text_msg = {**msg, "type": "text", "text": {"body": transcript}}
    await _process_text_message(db, text_msg, value)

@router.get("/webhook", response_class=PlainTextResponse)
async def verify_webhook(hub_mode: str = Query(..., alias="hub.mode"), hub_verify_token: str = Query(..., alias="hub.verify_token"), hub_challenge: str = Query(..., alias="hub.challenge")) -> str:
    if hub_mode == "subscribe" and hub_verify_token == WHATSAPP_VERIFY_TOKEN:
        return hub_challenge
    raise HTTPException(status_code=403, detail="Verification failed")

@router.post("/parse")
async def parse_message(payload: ParseMessageRequest) -> Dict[str, Any]:
    return parse_customer_intent(payload.message, [])

@router.post("/webhook")
async def receive_webhook(request: Request, db: Session = Depends(get_db)) -> Dict[str, Any]:
    body_bytes = await request.body()
    signature_header = request.headers.get("X-Hub-Signature-256", "")
    _verify_webhook_signature(body_bytes, signature_header)
    try:
        payload = json.loads(body_bytes)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    messages: List[Tuple[Dict[str, Any], Dict[str, Any]]] = []
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            for msg in value.get("messages", []):
                messages.append((msg, value))

    for msg, value in messages:
        msg_type = msg.get("type", "")
        try:
            if msg_type == "audio":
                await _process_audio_message(db, msg, value)
            elif msg_type == "text":
                await _process_text_message(db, msg, value)
            else:
                continue
        except Exception:
            pass

        try:
            automation_business_id = _resolve_business_id(db, msg, value)
            if automation_business_id is not None:
                await trigger_automations(automation_business_id, "whatsapp_message_received", {"phone": msg.get("from", ""), "text": msg.get("text", {}).get("body", ""), "type": msg_type, "business_id": automation_business_id})
        except Exception:
            pass

    return {"status": "success"}

# --- MAGIC BUTTON ADDED BELOW ---
@router.get("/send-test")
async def send_test():
    token = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
    phone_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
    env = getattr(settings, "ENVIRONMENT", "MISSING")
    try:
        await send_whatsapp_message("2348142969979", "Sannu! Wannan gwaji ne daga Vercel backend.")
        return {"status": "SUCCESS", "message": "Check your phone!", "token_length": len(token), "phone_id": phone_id, "environment": env}
    except Exception as e:
        return {"status": "FAILED", "error": str(e), "token_length": len(token), "phone_id": phone_id, "environment": env}
