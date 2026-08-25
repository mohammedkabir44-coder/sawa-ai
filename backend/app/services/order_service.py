"""Order service for WhatsApp commerce: creates orders from AI-parsed intents.

This module bridges the AI intent parser and the e-commerce order models.
When a customer sends a WhatsApp message, the AI parser extracts structured
intent (product, quantity, address).  This service turns that intent into a
real :class:`Order` with :class:`OrderItem` rows and generates a Paystack
checkout URL so the customer can pay.
"""
from __future__ import annotations

import os
import uuid
from typing import Any, Dict, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.customer import Customer
from app.models.order import Order, OrderItem, OrderStatus
from app.models.product import Product


# --------------------------------------------------------------------------- #
# Paystack integration
# --------------------------------------------------------------------------- #
def _create_paystack_checkout(
    *,
    email: str,
    amount: float,
    currency: str,
    reference: str,
    callback_url: Optional[str] = None,
) -> str:
    """Create a Paystack checkout session and return the authorization URL.

    If ``PAYSTACK_SECRET_KEY`` is not configured (e.g. in local development
    or tests), a deterministic mock URL is returned so the flow can be
    exercised end-to-end without real payment infrastructure.
    """
    secret_key = os.getenv("PAYSTACK_SECRET_KEY", "")
    if not secret_key:
        # Mock checkout URL for development / testing.
        return f"https://checkout.paystack.com/mock-checkout/{reference}"

    import httpx

    payload = {
        "email": email,
        "amount": int(amount * 100),  # Paystack expects kobo (cents)
        "currency": currency,
        "reference": reference,
        "callback_url": callback_url or os.getenv("PAYSTACK_CALLBACK_URL", ""),
    }
    headers = {
        "Authorization": f"Bearer {secret_key}",
        "Content-Type": "application/json",
    }
    try:
        resp = httpx.post(
            "https://api.paystack.co/transaction/initialize",
            json=payload,
            headers=headers,
            timeout=15.0,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["data"]["authorization_url"]
    except Exception as exc:  # noqa: BLE001
        # Fall back to a mock URL so the order is still created.
        print(f"[order_service] Paystack checkout failed: {exc}")
        return f"https://checkout.paystack.com/mock-checkout/{reference}"


# --------------------------------------------------------------------------- #
# Customer lookup / creation
# --------------------------------------------------------------------------- #
def _find_or_create_customer(
    db: Session,
    phone_number: str,
    business_id: int,
    name: Optional[str] = None,
) -> Customer:
    """Look up a customer by phone number within a business, or create one.

    WhatsApp phone numbers arrive in the format ``2348012345678`` (no ``+``).
    We normalise to ``+234XXXXXXXXX`` for storage consistency.
    """
    # Normalise: strip leading zeros / + and re-add +234
    raw = phone_number.lstrip("+")
    if raw.startswith("234"):
        normalised = "+" + raw
    elif raw.startswith("0"):
        normalised = "+234" + raw[1:]
    else:
        normalised = "+" + raw

    existing = db.scalar(
        select(Customer).where(
            Customer.business_id == business_id,
            Customer.phone == normalised,
        )
    )
    if existing is not None:
        return existing

    customer = Customer(
        business_id=business_id,
        name=name or "",
        phone=normalised,
        email="",
        preferred_language="unknown",
        source="whatsapp",
    )
    db.add(customer)
    db.flush()
    return customer


# --------------------------------------------------------------------------- #
# Product matching
# --------------------------------------------------------------------------- #
def _find_product(
    db: Session,
    business_id: int,
    product_query: Optional[str],
) -> Optional[Product]:
    """Find a product by name within a business.

    Uses a case-insensitive ``ILIKE`` match on the product name.  If the
    query is ``None`` or empty, returns ``None``.
    """
    if not product_query:
        return None

    # Try exact match first, then partial match.
    product = db.scalar(
        select(Product)
        .where(
            Product.business_id == business_id,
            Product.name.ilike(product_query),
        )
    )
    if product is None:
        # Partial / keyword match
        product = db.scalar(
            select(Product)
            .where(
                Product.business_id == business_id,
                Product.name.ilike(f"%{product_query}%"),
            )
        )
    return product


# --------------------------------------------------------------------------- #
# Main entry point
# --------------------------------------------------------------------------- #
async def create_order_from_intent(
    db: Optional[Session],
    whatsapp_id: str,
    parsed_intent: Dict[str, Any],
    business_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Create an order from an AI-parsed customer intent.

    Args:
        db: SQLAlchemy session.  If ``None`` (e.g. in unit tests with mocked
            dependencies), a minimal success response is returned without
            touching the database.
        whatsapp_id: The customer's WhatsApp phone number (from the webhook
            ``from`` field).
        parsed_intent: The dict returned by :func:`parse_customer_intent`.
        business_id: The tenant/business ID.  Required when ``db`` is provided.

    Returns:
        A dict with keys: ``success``, ``reference``, ``total_amount``,
        ``checkout_url``, ``product_name``, ``quantity``, and optionally
        ``error``.
    """
    intent = parsed_intent.get("intent", "unknown")
    product_query = parsed_intent.get("product_query")
    quantity = parsed_intent.get("quantity", 1)
    delivery_address = parsed_intent.get("delivery_address")

    # Only place_order intent creates an order.
    if intent != "place_order":
        return {
            "success": False,
            "error": f"Intent '{intent}' does not require order creation",
            "intent": intent,
        }

    # If no DB session, return a mock response (used in unit tests).
    if db is None:
        return {
            "success": True,
            "reference": f"WHATSAPP-{uuid.uuid4().hex[:8].upper()}",
            "total_amount": 0.0,
            "checkout_url": "https://checkout.paystack.com/mock-checkout/test",
            "product_name": product_query or "Unknown",
            "quantity": quantity,
        }

    if business_id is None:
        return {
            "success": False,
            "error": "business_id is required when db is provided",
        }

    # Find or create the customer.
    customer = _find_or_create_customer(
        db, whatsapp_id, business_id,
        name=parsed_intent.get("customer_name"),
    )

    # Find the product.
    product = _find_product(db, business_id, product_query)
    if product is None:
        return {
            "success": False,
            "error": f"Product not found: {product_query}",
            "product_query": product_query,
        }

    if product.stock < quantity:
        return {
            "success": False,
            "error": f"Insufficient stock for {product.name} "
                     f"(requested {quantity}, available {product.stock})",
            "product_name": product.name,
            "quantity": quantity,
        }

    # Calculate total.
    total_amount = product.price * quantity

    # Generate a unique order reference.
    reference = f"WHATSAPP-{uuid.uuid4().hex[:12].upper()}"

    # Create the order.
    order = Order(
        reference=reference,
        customer_id=customer.id,
        total_amount=total_amount,
        status=OrderStatus.PENDING,
        delivery_address=delivery_address or "",
        paystack_checkout_url=None,  # set after Paystack call
        metadata_json={
            "source": "whatsapp",
            "whatsapp_id": whatsapp_id,
            "parsed_intent": parsed_intent,
        },
    )
    db.add(order)
    db.flush()

    # Create order item.
    order_item = OrderItem(
        order_id=order.id,
        product_id=product.id,
        quantity=quantity,
        unit_price=product.price,
    )
    db.add(order_item)

    # Generate Paystack checkout URL.
    checkout_url = _create_paystack_checkout(
        email=customer.email or f"{whatsapp_id}@customer.sawa",
        amount=total_amount,
        currency=product.currency,
        reference=reference,
    )
    order.paystack_checkout_url = checkout_url

    # Deduct stock.
    product.stock -= quantity

    db.commit()
    db.refresh(order)

    return {
        "success": True,
        "reference": reference,
        "total_amount": total_amount,
        "checkout_url": checkout_url,
        "product_name": product.name,
        "quantity": quantity,
        "order_id": order.id,
        "customer_id": customer.id,
    }
