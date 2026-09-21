"""Mock AI provider for development.

Clearly labelled as a development/mock provider. It answers using only
the provided business knowledge and never invents facts. Used when no
real AI credentials are configured.

When called from the intent parser (:mod:`app.services.ai.parser`), the
provider returns a JSON string matching the parser's expected schema so
that the full commerce flow can be exercised end-to-end without real AI
credentials.
"""
import json
import re
from typing import Any, Dict, List, Optional

from app.services.ai.base import AIProvider, AIResponse


class MockAIProvider(AIProvider):
    name = "mock"

    def _format_price(self, price: float, currency: str) -> str:
        return f"{currency} {price:,.2f}"

    def _find_product(self, message: str, products: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        words = message.lower().split()
        best = None
        best_score = 0
        for p in products:
            score = sum(1 for w in words if w in p["name"].lower())
            if score > best_score:
                best_score = score
                best = p
        return best if best_score > 0 else None

    # ------------------------------------------------------------------ #
    # Helpers for the intent-parsing flow
    # ------------------------------------------------------------------ #
    _MESSAGE_RE = re.compile(r'Message:\s*"([^"]*)"', re.DOTALL)

    def _extract_customer_message(self, prompt: str) -> str:
        """Extract the raw customer message from the parser's prompt.

        The parser wraps the customer message inside a larger prompt that
        looks like ``Message: "..."``.  We pull it out so keyword matching
        isn't polluted by the schema description text.
        """
        match = self._MESSAGE_RE.search(prompt)
        if match:
            return match.group(1)
        return prompt

    def _extract_quantity(self, text: str) -> int:
        """Best-effort quantity extraction from the customer message.

        Handles English digits ("2", "3") and common Hausa words
        ("guda daya" = 1, "guda biyu" = 2, "guda taku" = 3, etc.).
        Defaults to 1 when nothing is found.
        """
        hausa_numbers = {
            "guda daya": 1, "guda biyu": 2, "guda taku": 3, "guda naira": 4,
            "guda biyar": 5, "guda shida": 6, "guda takwas": 7, "guda tara": 8,
            "guda tisa": 9, "guda goma": 10,
        }
        lowered = text.lower()
        for phrase, num in sorted(hausa_numbers.items(), key=lambda x: len(x[0]), reverse=True):
            if phrase in lowered:
                return num
        # Look for standalone digits
        digit_match = re.search(r'\b(\d+)\b', lowered)
        if digit_match:
            return int(digit_match.group(1))
        return 1

    def _extract_address(self, text: str) -> Optional[str]:
        """Best-effort delivery address extraction.

        Looks for common address indicators in the message.
        """
        lowered = text.lower()
        # Look for patterns like "No 10 Main Street, Kano" or "deliver to ..."
        addr_patterns = [
            r'(?:no\.?\s*\d+\s+[^\n,]+(?:,\s*[^\n,]+)*)',
            r'(?:deliver\s+to\s+[^\n,]+(?:,\s*[^\n,]+)*)',
            r'(?:address\s*[:\-]?\s*[^\n,]+(?:,\s*[^\n,]+)*)',
        ]
        for pattern in addr_patterns:
            match = re.search(pattern, lowered)
            if match:
                return match.group(0).strip().title()
        return None

    def _json_response(
        self,
        intent: str,
        language: str,
        confidence: float,
        product_query: Optional[str],
        quantity: int,
        delivery_address: Optional[str],
        reply_message: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AIResponse:
        """Build an AIResponse whose text is a JSON string matching the
        parser's expected schema."""
        payload: Dict[str, Any] = {
            "intent": intent,
            "language": language,
            "confidence": confidence,
            "product_query": product_query,
            "quantity": quantity,
            "delivery_address": delivery_address,
            "reply_message": reply_message,
        }
        return AIResponse(
            text=json.dumps(payload, ensure_ascii=False),
            language=language,
            confidence=confidence,
            metadata=metadata or {},
        )

    def generate_response(
        self,
        message: str,
        language: str,
        business_context: Dict[str, Any],
        conversation_history: List[Dict[str, Any]],
    ) -> AIResponse:
        products = business_context.get("products", [])
        knowledge = business_context.get("knowledge", [])
        business_name = business_context.get("business_name", "our business")

        # Extract the actual customer message from the parser's prompt.
        customer_msg = self._extract_customer_message(message)
        msg_lower = customer_msg.lower()

        product = self._find_product(customer_msg, products)
        quantity = self._extract_quantity(customer_msg)
        delivery_address = self._extract_address(customer_msg)

        # --- Place order ---
        if any(k in msg_lower for k in ["ina so", "ina son", "saya", "buy", "order", "na saya", "na so"]):
            if product:
                price = self._format_price(product["price"], product.get("currency", "NGN"))
                if language in ("ha", "ha-en"):
                    reply = (
                        f"Farashin {product['name']} shine {price}. "
                        f"Za ka iya turo mana sakon idan kana son siyan shi."
                    )
                else:
                    reply = (
                        f"The price of the {product['name']} is {price}. "
                        f"Would you like to place an order?"
                    )
                return self._json_response(
                    "place_order", language, 0.9, product["name"],
                    quantity, delivery_address, reply,
                )
            else:
                if language in ("ha", "ha-en"):
                    reply = "Ban saitin da kuma. Za ka iya turo min?"
                else:
                    reply = "I'm sorry, I couldn't find that product. Could you please clarify?"
                return self._json_response(
                    "product_enquiry", language, 0.5, None,
                    1, None, reply,
                )

        # --- Price enquiry ---
        if any(k in msg_lower for k in ["nawa", "price", "how much", "farashi", "farashin", "cost"]):
            if product:
                price = self._format_price(product["price"], product.get("currency", "NGN"))
                if language in ("ha", "ha-en"):
                    reply = (
                        f"Farashin {product['name']} shine {price}. "
                        f"Za ka iya turo mana sakon idan kana son siyan shi."
                    )
                else:
                    reply = (
                        f"The price of the {product['name']} is {price}. "
                        f"Would you like to place an order?"
                    )
                return self._json_response(
                    "price_enquiry", language, 0.9, product["name"],
                    1, None, reply,
                )
            else:
                if language in ("ha", "ha-en"):
                    reply = "Ban saitin da kuma. Za ka iya turo min?"
                else:
                    reply = "I'm sorry, I couldn't find that product. Could you please clarify?"
                return self._json_response(
                    "price_enquiry", language, 0.5, None,
                    1, None, reply,
                )

        # --- Availability enquiry ---
        if any(k in msg_lower for k in ["yana nan", "available", "in stock", "akwai", "yana da"]):
            if product:
                stock = product.get("stock_quantity", 0)
                if stock <= 0:
                    if language in ("ha", "ha-en"):
                        reply = f"Yi hakuri, {product['name']} bashi nan a yanzu."
                    else:
                        reply = f"Sorry, the {product['name']} is currently out of stock."
                else:
                    if language in ("ha", "ha-en"):
                        reply = f"Eh, {product['name']} yana nan."
                    else:
                        reply = f"Yes, the {product['name']} is available."
                return self._json_response(
                    "availability", language, 0.85, product["name"],
                    1, None, reply,
                )
            else:
                if language in ("ha", "ha-en"):
                    reply = "Ban saitin da kuma. Za ka iya turo min?"
                else:
                    reply = "I'm sorry, I couldn't find that product. Could you please clarify?"
                return self._json_response(
                    "product_enquiry", language, 0.5, None,
                    1, None, reply,
                )

        # --- Greeting ---
        if any(k in msg_lower for k in ["hello", "hi", "sannu", "barka", "good morning", "good afternoon", "good evening"]):
            if language in ("ha", "ha-en"):
                reply = f"Sannu! Barka da zuwa {business_name}. Yaya zan iya taimaka maka?"
            else:
                reply = f"Hello! Welcome to {business_name}. How can I help you today?"
            return self._json_response(
                "greeting", language, 0.9, None,
                1, None, reply,
            )

        # --- Human agent request ---
        if any(k in msg_lower for k in ["human", "agent", "mutum", "magana da mutum", "person", "tallafi"]):
            if language in ("ha", "ha-en"):
                reply = "Zan hada ka da wani daga cikin ma'aikatan mu nan ba da jimawa ba."
            else:
                reply = "I'll connect you with a member of our team shortly."
            return self._json_response(
                "human_agent", language, 0.9, None,
                1, None, reply,
                metadata={"handoff": True},
            )

        # --- Knowledge base lookup ---
        for entry in knowledge:
            if any(k in msg_lower for k in entry.get("keywords", [])):
                return self._json_response(
                    "product_enquiry", language, 0.8, None,
                    1, None, entry["content"],
                )

        # --- Fallback: never invent facts ---
        if language in ("ha", "ha-en"):
            reply = (
                "Yi hakuri, ban fahimci sakon sosai ba. Za ka iya sake turo min? "
                "Ko kuma zan iya hada ka da wani daga cikin ma'aikatan mu."
            )
        else:
            reply = (
                "I'm sorry, I didn't fully understand that. Could you rephrase? "
                "Or I can connect you with a member of our team."
            )
        return self._json_response(
            "unknown", language, 0.4, None,
            1, None, reply,
        )

    def generate_campaign(self, prompt: str, business_context: Dict[str, Any]) -> Dict[str, str]:
        business_name = business_context.get("business_name", "our business")
        return {
            "title": f"New Promotion at {business_name}",
            "message": (
                f"Great news from {business_name}! We have exciting new offers. "
                "Contact us today to learn more."
            ),
            "short_version": f"New offers at {business_name}! Contact us today.",
            "english_version": (
                f"Great news from {business_name}! We have exciting new offers. "
                "Contact us today to learn more."
            ),
            "hausa_version": (
                f"Labari mai dadi daga {business_name}! Muna da sabbin tayi. "
                "Tuntube mu yau don karin bayani."
            ),
        }
