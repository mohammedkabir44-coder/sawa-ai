"""WhatsApp Commerce Engine - simplified reliable build."""
import hmac
import hashlib
import json
import logging
import os
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.product import Product
from app.models.whatsapp import WhatsAppAccount
from app.services.ai.language import detect_language
from app.services.ai.parser import parse_customer_intent

router = APIRouter(prefix="/whatsapp-commerce", tags=["whatsapp-commerce"])
logger = logging.getLogger(__name__)

class ParseMessageRequest(BaseModel):
    message: str

WHATSAPP_VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "sawatoken123")
WHATSAPP_APP_SECRET = os.getenv("WHATSAPP_APP_SECRET", "")


def _direct_send(to_number: str, text: str) -> Dict[str, Any]:
    """Send a WhatsApp text using the PROVEN env credentials."""
    token = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
    phone_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
    url = f"https://graph.facebook.com/v25.0/{phone_id}/messages"
    payload = json.dumps({
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {"body": text},
    }).encode("utf-8")
    req = urllib.request.Request(url, data=payload, method="POST")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _resolve_business_id(db: Session, msg: Dict[str, Any], value: Dict[str, Any]) -> Optional[int]:
    to_number = msg.get("to", "")
    if to_number:
        account = db.scalar(select(WhatsAppAccount).where(WhatsAppAccount.phone_number == to_number))
        if account is not None:
            return account.business_id
    metadata = value.get("metadata", {})
    phone_number_id = metadata.get("phone_number_id", "")
    if phone_number_id:
        account = db.scalar(select(WhatsAppAccount).where(WhatsAppAccount.phone_number_id == phone_number_id))
        if account is not None:
            return account.business_id
    return None


def _get_product_catalog(db: Session, business_id: int) -> List[Dict[str, Any]]:
    products = db.query(Product).filter(Product.business_id == business_id, Product.is_active.is_(True)).all()
    return [{"id": p.id, "name": p.name, "price": p.price, "stock_quantity": p.stock} for p in products]


def _smart_reply(text_body: str, catalog: List[Dict[str, Any]]) -> str:
    """Fast, deterministic Hausa/English responder (never hangs)."""
    low = text_body.lower()
    for p in catalog:
        name = str(p["name"]).lower()
        if name in low or name.split()[0] in low:
            return (f"Sannu! {p['name']} yana nan. Farashi: {p['price']:,.2f}. "
                    f"Adadi a kaya: {p['stock_quantity']}. Za ka so ka yi oda?")
    if catalog:
        names = ", ".join(str(p["name"]) for p in catalog[:6])
        return f"Sannu! Ga kayayyakinmu: {names}. Wanne kake son sani?"
    return "Sannu! Na karbi sakonka. Za a amsa maka nan take."


async def _process_text_message(db: Session, msg: Dict[str, Any], value: Dict[str, Any]) -> Dict[str, Any]:
    from_number = msg.get("from", "")
    text_body = msg.get("text", {}).get("body", "")
    business_id = _resolve_business_id(db, msg, value) or 1
    catalog = _get_product_catalog(db, business_id)
    reply = _smart_reply(text_body, catalog)
    try:
        send_result = _direct_send(from_number, reply)
        return {"status": "SENT", "reply": reply, "meta": send_result}
    except Exception as exc:
        meta_body = ""
        if hasattr(exc, "read"):
            try:
                meta_body = exc.read().decode("utf-8")
            except Exception:
                meta_body = ""
        return {"status": "SEND_FAILED", "reply": reply, "error": str(exc), "meta_response": meta_body}


@router.get("/webhook", response_class=PlainTextResponse)
async def verify_webhook(hub_mode: str = Query(..., alias="hub.mode"), hub_verify_token: str = Query(..., alias="hub.verify_token"), hub_challenge: str = Query(..., alias="hub.challenge")) -> str:
    if hub_mode == "subscribe" and hub_verify_token == WHATSAPP_VERIFY_TOKEN:
        return hub_challenge
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/parse")
async def parse_message(payload: ParseMessageRequest) -> Dict[str, Any]:
    try:
        return parse_customer_intent(payload.message, [])
    except Exception as e:
        return {"intent": "error", "reply_message": _smart_reply(payload.message, []), "error": str(e)}


@router.post("/debug-inbound")
async def debug_inbound(request: Request, db: Session = Depends(get_db)):
    payload = await request.json()
    msg = payload.get("msg", {})
    value = payload.get("value", {})
    return await _process_text_message(db, msg, value)


@router.get("/send-test")
async def send_test():
    try:
        result = _direct_send("2348142969979", "Sannu! Wannan gwaji ne daga Vercel backend.")
        return {"status": "SUCCESS", "environment": getattr(settings, "ENVIRONMENT", "MISSING"), "meta": result}
    except Exception as e:
        return {"status": "FAILED", "error": str(e), "environment": getattr(settings, "ENVIRONMENT", "MISSING")}


@router.post("/webhook")
async def receive_webhook(request: Request, db: Session = Depends(get_db)) -> Dict[str, Any]:
    body_bytes = await request.body()
    signature_header = request.headers.get("X-Hub-Signature-256", "")
    if WHATSAPP_APP_SECRET:
        if not signature_header:
            raise HTTPException(status_code=403, detail="Missing signature")
        expected_sig = hmac.new(WHATSAPP_APP_SECRET.encode("utf-8"), body_bytes, hashlib.sha256).hexdigest()
        incoming_sig = signature_header.split("=")[1] if "=" in signature_header else ""
        if not hmac.compare_digest(expected_sig, incoming_sig):
            raise HTTPException(status_code=403, detail="Invalid signature")
    try:
        payload = json.loads(body_bytes)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            for msg in value.get("messages", []):
                if msg.get("type") == "text":
                    try:
                        await _process_text_message(db, msg, value)
                    except Exception:
                        logger.exception("Failed to process message")
    return {"status": "success"}
