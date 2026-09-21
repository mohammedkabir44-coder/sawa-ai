"""AI-powered customer message parser for WhatsApp commerce.

Phase 6 (AI) — Intent parsing with Gemini integration.

Uses the configured AI provider (Gemini when ``AI_PROVIDER=gemini`` and
``GEMINI_API_KEY`` is set, otherwise the Mock provider) to detect language,
classify intent, and generate a contextual reply.  The provider is selected
via :func:`app.services.ai.get_ai_provider`.

The parser NEVER invents prices, products, or stock.  If the AI cannot
determine intent with confidence, it returns ``intent="unknown"`` and asks
the customer to clarify.
"""
import json
import os
from typing import Any, Dict, List, Optional

from app.services.ai.base import AIProvider, AIResponse
from app.services.ai.language import detect_language
from app.services.ai.mock import MockAIProvider

# Set a dummy key so the OpenAI import in the old code path doesn't crash
# during local development / tests.
if not os.getenv("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = "sk-dummy-key-for-local-testing-12345"

# ---------------------------------------------------------------------------
# System prompt for the Gemini intent parser.
# ---------------------------------------------------------------------------
INTENT_PARSER_SYSTEM_PROMPT = """
You are an expert AI sales assistant and order parser for a West African
WhatsApp commerce platform. You fluidly understand English, Hausa, and
mixed Hausa+English (including colloquial phrasing like 'Nawa ne wannan?',
'Ina son siyayya', 'Ina so nawa?', 'Ina mai shago').

Your task is to analyze an incoming customer message and extract structured
sales intent against the merchant's product catalog.

STRICT RULES:
- NEVER invent prices, products, stock availability, delivery timelines,
  payment policies, return policies, business hours, or promises.
- If information is unavailable, say you need to confirm with the business.
- If you do not understand (low confidence), return intent "unknown" and
  ask for clarification.

You MUST respond ONLY with a valid JSON object matching this exact schema:
{
  "intent": "price_enquiry" | "product_enquiry" | "availability" | "place_order" | "greeting" | "human_agent" | "unknown",
  "language": "en" | "ha" | "ha-en",
  "confidence": 0.0 - 1.0,
  "product_query": "extracted product name or keyword, or null if none",
  "quantity": 1,
  "delivery_address": "extracted delivery address or null if none",
  "reply_message": "A polite, natural, conversion-driven response in the exact same language detected (Hausa or English) guiding the customer to complete their order or confirming details."
}
"""


def _get_provider() -> AIProvider:
    """Return the configured AI provider (Gemini or Mock)."""
    from app.services.ai import get_ai_provider
    return get_ai_provider()


def _parse_with_gemini(
    message: str,
    product_catalog: List[Dict[str, Any]],
    detected_language: str,
) -> Dict[str, Any]:
    """Call Gemini to parse the customer intent.

    Returns a dict matching the schema described in
    :data:`INTENT_PARSER_SYSTEM_PROMPT`.
    """
    provider = _get_provider()

    # Build business context for the AI provider.
    catalog_summary = ", ".join([
        f"ID: {p.get('id')} | Name: {p.get('name')} | Price: ₦{p.get('price')} | Stock: {p.get('stock_quantity', 0)}"
        for p in product_catalog
    ]) or "No products currently listed in catalog."

    business_context: Dict[str, Any] = {
        "products": product_catalog,
        "knowledge": [],
        "business_name": "the business",
    }

    prompt = f"""Analyze this customer message for a WhatsApp commerce platform in West Africa.

Message: "{message}"

Pre-detected language: {detected_language}

Product Catalog:
{catalog_summary}

Extract the following information and respond with ONLY a JSON object matching this exact schema:
{{
  "intent": "price_enquiry" | "product_enquiry" | "availability" | "place_order" | "greeting" | "human_agent" | "unknown",
  "language": "en" | "ha" | "ha-en",
  "confidence": 0.0 - 1.0,
  "product_query": "extracted product name or keyword, or null if none",
  "quantity": 1,
  "delivery_address": "extracted delivery address or null if none",
  "reply_message": "A polite, natural, conversion-driven response in the exact same language detected"
}}"""

    # Use the AI provider's generate_response to get a natural-language
    # response, then parse the JSON from it.
    response: AIResponse = provider.generate_response(
        message=prompt,
        language=detected_language,
        business_context=business_context,
        conversation_history=[],
    )

    # The AI provider returns text; we expect it to contain a JSON object.
    text = response.text.strip()
    # Strip markdown fences if present.
    text = text.removeprefix("```json").removesuffix("```").strip()
    text = text.removeprefix("```").removesuffix("```").strip()

    try:
        result = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        # If the AI didn't return valid JSON, fall back to a safe default.
        return {
            "intent": "unknown",
            "language": detected_language,
            "confidence": 0.0,
            "product_query": None,
            "quantity": 1,
            "delivery_address": None,
            "reply_message": (
                "Sannu! Ban fahimci sakon ka ba sosai. Za ka iya sake turo min?"
                if detected_language in ("ha", "ha-en")
                else "Hello! I didn't quite catch that. Could you please repeat?"
            ),
        }

    # Ensure required fields exist with safe defaults.
    result.setdefault("quantity", 1)
    if result.get("delivery_address") == "":
        result["delivery_address"] = None
    if result.get("product_query") == "":
        result["product_query"] = None
    if "detected_language" not in result and "language" in result:
        result["detected_language"] = result["language"]
    if "detected_language" not in result:
        result["detected_language"] = detected_language
    if "reply_message" not in result:
        result["reply_message"] = (
            "Sannu! Ban fahimci sakon ka ba sosai. Za ka iya sake turo min?"
            if detected_language in ("ha", "ha-en")
            else "Hello! I didn't quite catch that. Could you please repeat?"
        )

    return result


def parse_customer_intent(
    message: str,
    product_catalog: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Parse a customer message to extract shopping intent.

    Uses the configured AI provider (Gemini or Mock) to detect language,
    classify intent, and generate a contextual reply.  Falls back to a
    safe mock response if the AI provider fails.

    Args:
        message: The customer message text (or transcribed voice text).
        product_catalog: List of product dicts with id, name, price,
            stock_quantity.

    Returns:
        Dict with keys: ``intent``, ``language``, ``confidence``,
        ``product_query``, ``quantity``, ``delivery_address``,
        ``reply_message``, and ``detected_language``.
    """
    # Detect language using the vocabulary-based detector first.
    lang_result = detect_language(message)
    detected_language = lang_result.language

    try:
        result = _parse_with_gemini(message, product_catalog, detected_language)
        # Ensure detected_language is always present for downstream consumers.
        result.setdefault("detected_language", detected_language)
        return result
    except Exception as e:  # noqa: BLE001
        print(f"Error in NLP intent parser: {e}")
        # Fallback: safe mock response supporting both Hausa and English.
        return {
            "intent": "unknown",
            "language": detected_language,
            "detected_language": detected_language,
            "confidence": 0.0,
            "product_query": None,
            "quantity": 1,
            "delivery_address": None,
            "reply_message": (
                "Sannu! Ban fahimci sakon ka ba sosai. Za ka iya sake turo min?"
                if detected_language in ("ha", "ha-en")
                else "Hello! I didn't quite catch that. Could you please repeat?"
            ),
        }


if __name__ == "__main__":
    samples = [
        "Nawa ne farashin wannan?",
        "How much is this item?",
        "Ina so na saya, but how much is the price?",
        "",
    ]
    for s in samples:
        print(s, "->", parse_customer_intent(s, []))
