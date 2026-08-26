import re
from typing import Optional


def detect_language(message: str) -> str:
    hausa_words = ["nawa", "wannan", "ina", "yaya", "sannu", "ina", "don", "ko", "ban", "za", "ka", "ta", "ne", "ce", "da", "kuma", "suna", "yi"]
    message_lower = message.lower()
    hausa_count = sum(1 for word in hausa_words if word in message_lower.split())
    if hausa_count >= 2:
        return "ha"
    return "en"


def extract_product_query(message: str) -> Optional[str]:
    # Common product-related keywords to strip out
    stop_words_ha = ["nawa", "ne", "wannan", "wanan", "ina", "yaya", "sannu", "don", "ko", "ban", "za", "ka", "ta", "ce", "da", "kuma", "suna", "yi", "wa", "su", "mu", "ni"]
    stop_words_en = ["how", "much", "what", "price", "cost", "the", "is", "this", "that", "a", "an", "for", "of", "in", "do", "you", "have", "i", "want"]

    words = message.split()
    product_words = []
    for word in words:
        clean = re.sub(r"[^a-zA-Z0-9]", "", word).lower()
        if clean and clean not in stop_words_ha and clean not in stop_words_en:
            product_words.append(clean)

    if product_words:
        return " ".join(product_words)
    return None


def parse_message(message: str) -> dict:
    language = detect_language(message)
    message_lower = message.lower()

    # Detect intent
    intent = "general"
    price_keywords_ha = ["nawa", "farashin", "farashi", "tsadar"]
    price_keywords_en = ["price", "cost", "how much", "amount"]
    order_keywords_ha = ["ina", "so", "sayi", "sai", "nemi"]
    order_keywords_en = ["buy", "order", "want", "purchase"]
    stock_keywords_ha = ["akwai", "suna", "kuna"]
    stock_keywords_en = ["stock", "available", "have"]

    if any(kw in message_lower for kw in price_keywords_ha + price_keywords_en):
        intent = "price_enquiry"
    elif any(kw in message_lower for kw in order_keywords_ha + order_keywords_en):
        intent = "order"
    elif any(kw in message_lower for kw in stock_keywords_ha + stock_keywords_en):
        intent = "stock_enquiry"

    # Extract product query
    product_query = extract_product_query(message)

    # Build reply
    if intent == "price_enquiry" and product_query:
        if language == "ha":
            reply_message = f"Bari in duba farashin {product_query} a kan."
        else:
            reply_message = f"Let me check the price of {product_query} for you."
    elif intent == "price_enquiry":
        if language == "ha":
            reply_message = "Ban saitin da kuma. Za ka iya turo min?"
        else:
            reply_message = "I don't have that in stock. Can you send me details?"
    elif intent == "order" and product_query:
        if language == "ha":
            reply_message = f"To, za a yi odar {product_query}. Ina da bukatar adireshin ka."
        else:
            reply_message = f"Great, I'll place an order for {product_query}. I need your delivery address."
    elif intent == "order":
        if language == "ha":
            reply_message = "Me kake so ka saya?"
        else:
            reply_message = "What would you like to buy?"
    elif intent == "stock_enquiry" and product_query:
        if language == "ha":
            reply_message = f"Bari in duba ko {product_query} yana nan."
        else:
            reply_message = f"Let me check if {product_query} is available."
    else:
        if language == "ha":
            reply_message = "Sannu! Yaya zan iya taimaka maka?"
        else:
            reply_message = "Hello! How can I help you?"

    return {
        "intent": intent,
        "language": language,
        "confidence": 0.8,
        "product_query": product_query,
        "quantity": 1,
        "delivery_address": None,
        "reply_message": reply_message,
        "detected_language": language
    }
