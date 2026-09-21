"""Tests for WhatsApp Commerce Engine webhook and order flow."""
import os
import pytest
import hmac
import hashlib
from unittest.mock import patch, AsyncMock

# Set dummy OpenAI API key to allow module imports without real credentials
os.environ["OPENAI_API_KEY"] = "test-dummy-key"

from app.main import app
from app.models.ecommerce import Product, Customer, Order, OrderStatus


@pytest.fixture
def sample_product(db) -> Product:
    """Create a sample product in the test database."""
    product = Product(
        business_id=1,
        sku="TEST-SKU-001",
        name="Ankara Fabric",
        description="High quality traditional fabric",
        price=15000.0,
        stock=10,
        category="Fashion",
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@pytest.fixture
def sample_customer(db) -> Customer:
    """Create a sample customer in the test database."""
    customer = Customer(
        business_id=1,
        name="Test Customer",
        phone="+2348012345678",
        email="test@example.com",
        preferred_language="ha",
        source="whatsapp",
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@pytest.mark.asyncio
async def test_verify_webhook_success(async_client):
    """Webhook verification succeeds with correct token."""
    response = await async_client.get(
        "/api/v1/whatsapp-commerce/webhook"
        "?hub.mode=subscribe&hub.verify_token=sawatoken123&hub.challenge=12345"
    )
    assert response.status_code == 200
    assert response.text == "12345"


@pytest.mark.asyncio
async def test_verify_webhook_failure(async_client):
    """Webhook verification fails with wrong token."""
    response = await async_client.get(
        "/api/v1/whatsapp-commerce/webhook"
        "?hub.mode=subscribe&hub.verify_token=wrongtoken&hub.challenge=12345"
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_parse_message(async_client):
    """Parse endpoint returns AI-parsed intent."""
    with patch(
        "app.api.v1.endpoints.whatsapp_commerce.parse_customer_intent"
    ) as mock_parse:
        mock_parse.return_value = {
            "detected_language": "ha",
            "intent": "place_order",
            "product_query": "Ankara Fabric",
            "quantity": 1,
            "delivery_address": "No 10 Main Street, Kano",
            "reply_message": "An shirya odar ka.",
        }
        response = await async_client.post(
            "/api/v1/whatsapp-commerce/parse",
            json={"message": "Ina son saya Ankara Fabric guda daya"},
        )
    assert response.status_code == 200
    body = response.json()
    assert body["intent"] == "place_order"
    assert body["product_query"] == "Ankara Fabric"


@pytest.mark.asyncio
@patch("app.api.v1.endpoints.whatsapp_commerce.parse_customer_intent")
@patch("app.api.v1.endpoints.whatsapp_commerce.create_order_from_intent", new_callable=AsyncMock)
@patch("app.api.v1.endpoints.whatsapp_commerce.send_whatsapp_message", new_callable=AsyncMock)
async def test_whatsapp_text_order_flow(
    mock_send_msg,
    mock_create_order,
    mock_parse_intent,
    async_client,
    sample_product,
):
    """End-to-end WhatsApp text order flow with mocked AI, order, Paystack, and dispatch."""
    # Mock AI Intent Parser response
    mock_parse_intent.return_value = {
        "intent": "place_order",
        "product_query": "Ankara Fabric",
        "quantity": 1,
        "delivery_address": "No 10 Main Street, Kano",
        "detected_language": "ha",
        "reply_message": "An shirya odar ka.",
    }

    # Mock Order Service response
    mock_create_order.return_value = {
        "success": True,
        "reference": "WHATSAPP-ABC123XYZ",
        "total_amount": 15000.0,
        "checkout_url": "https://checkout.paystack.com/test-url",
        "product_name": "Ankara Fabric",
        "quantity": 1,
    }

    payload = {
        "entry": [{
            "changes": [{
                "value": {
                    "messages": [{
                        "from": "2348012345678",
                        "type": "text",
                        "text": {"body": "Ina son saya Ankara Fabric guda daya"}
                    }]
                }
            }]
        }]
    }

    # No app secret configured in tests, so signature check is skipped.
    response = await async_client.post(
        "/api/v1/whatsapp-commerce/webhook",
        json=payload,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "success"
    mock_parse_intent.assert_called_once()
    mock_create_order.assert_awaited_once()
    mock_send_msg.assert_awaited_once()


@pytest.mark.asyncio
@patch("app.api.v1.endpoints.whatsapp_commerce.parse_customer_intent")
@patch("app.api.v1.endpoints.whatsapp_commerce.create_order_from_intent", new_callable=AsyncMock)
@patch("app.api.v1.endpoints.whatsapp_commerce.send_whatsapp_message", new_callable=AsyncMock)
async def test_whatsapp_webhook_non_order_intent(
    mock_send_msg,
    mock_create_order,
    mock_parse_intent,
    async_client,
):
    """Webhook with non-place_order intent does not create an order."""
    mock_parse_intent.return_value = {
        "intent": "greeting",
        "product_query": None,
        "quantity": 1,
        "delivery_address": None,
        "detected_language": "en",
        "reply_message": "Hello! How can I help you?",
    }

    payload = {
        "entry": [{
            "changes": [{
                "value": {
                    "messages": [{
                        "from": "2348012345678",
                        "type": "text",
                        "text": {"body": "Hello"}
                    }]
                }
            }]
        }]
    }

    response = await async_client.post(
        "/api/v1/whatsapp-commerce/webhook",
        json=payload,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "success"
    mock_parse_intent.assert_called_once()
    mock_create_order.assert_not_awaited()
    mock_send_msg.assert_not_awaited()


@pytest.mark.asyncio
async def test_whatsapp_webhook_invalid_signature(async_client):
    """Webhook with invalid signature returns 403."""
    # Set a temporary app secret for this test
    with patch(
        "app.api.v1.endpoints.whatsapp_commerce.WHATSAPP_APP_SECRET",
        "test-secret-key",
    ):
        body_bytes = b'{"test": "payload"}'
        # Compute a wrong signature
        wrong_sig = "sha256=" + hmac.new(
            b"wrong-secret", body_bytes, hashlib.sha256
        ).hexdigest()

        response = await async_client.post(
            "/api/v1/whatsapp-commerce/webhook",
            content=body_bytes,
            headers={
                "X-Hub-Signature-256": wrong_sig,
                "Content-Type": "application/json",
            },
        )

    assert response.status_code == 403
