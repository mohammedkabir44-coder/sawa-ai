"""Gemini AI provider (real integration).

Used only when GEMINI_API_KEY is configured and AI_PROVIDER=gemini.
The API key is read from the environment and never exposed to the frontend.
"""
import json
from typing import Any, Dict, List

import httpx

from app.services.ai.base import AIProvider, AIResponse

GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"


class GeminiProvider(AIProvider):
    name = "gemini"

    def __init__(self, api_key: str):
        self.api_key = api_key

    def _build_prompt(
        self,
        message: str,
        language: str,
        business_context: Dict[str, Any],
        conversation_history: List[Dict[str, Any]],
    ) -> str:
        products = json.dumps(business_context.get("products", []), ensure_ascii=False)
        knowledge = json.dumps(business_context.get("knowledge", []), ensure_ascii=False)
        business_name = business_context.get("business_name", "the business")

        history = "\n".join(
            f"{h.get('role', 'customer')}: {h.get('content', '')}"
            for h in conversation_history[-6:]
        )

        return f"""
You are the AI customer assistant for {business_name}, a Nigerian business.
You support English, Hausa, and mixed Hausa+English. Detect the customer's
language and reply in the same language.

STRICT RULES:
- Only use the business knowledge and products provided below.
- NEVER invent prices, products, stock availability, delivery timelines,
  payment policies, return policies, business hours, or promises.
- If information is unavailable, say you need to confirm with the business.
- If you do not understand (low confidence), ask for clarification in Hausa:
  "Yi hakuri, ban fahimci sakon sosai ba. Za ka iya sake turo min?"

Business name: {business_name}
Products: {products}
Knowledge base: {knowledge}

Conversation history:
{history}

Customer message: {message}
Detected language: {language}

Respond naturally in the customer's language.
"""

    def generate_response(
        self,
        message: str,
        language: str,
        business_context: Dict[str, Any],
        conversation_history: List[Dict[str, Any]],
    ) -> AIResponse:
        prompt = self._build_prompt(message, language, business_context, conversation_history)
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.4, "maxOutputTokens": 500},
        }
        headers = {"Content-Type": "application/json"}
        resp = httpx.post(
            f"{GEMINI_ENDPOINT}?key={self.api_key}",
            json=payload,
            headers=headers,
            timeout=30.0,
        )
        resp.raise_for_status()
        data = resp.json()
        try:
            text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except (KeyError, IndexError, TypeError):
            raise RuntimeError("Unexpected Gemini response shape")
        return AIResponse(text=text, language=language, confidence=0.9)

    def generate_campaign(self, prompt: str, business_context: Dict[str, Any]) -> Dict[str, str]:
        business_name = business_context.get("business_name", "the business")
        system = (
            f"You are a marketing copywriter for {business_name}, a Nigerian business. "
            "Generate a campaign based on the request. Return JSON with keys: "
            "title, message, short_version, english_version, hausa_version. "
            "Do not invent prices or products not provided."
        )
        payload = {
            "contents": [{"parts": [{"text": f"{system}\n\nRequest: {prompt}"}]}],
            "generationConfig": {"temperature": 0.7, "maxOutputTokens": 800},
        }
        headers = {"Content-Type": "application/json"}
        resp = httpx.post(
            f"{GEMINI_ENDPOINT}?key={self.api_key}",
            json=payload,
            headers=headers,
            timeout=30.0,
        )
        resp.raise_for_status()
        data = resp.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        # Strip markdown fences if present
        text = text.strip().removeprefix("```json").removesuffix("```").strip()
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            parsed = {
                "title": "New Campaign",
                "message": text,
                "short_version": text[:120],
                "english_version": text,
                "hausa_version": text,
            }
        return {
            "title": parsed.get("title", "New Campaign"),
            "message": parsed.get("message", ""),
            "short_version": parsed.get("short_version", ""),
            "english_version": parsed.get("english_version", ""),
            "hausa_version": parsed.get("hausa_version", ""),
        }