"""Hausa / English / mixed language detection.

Detects language by intent and vocabulary, not word-for-word translation.
Returns one of: en, ha, ha-en, unknown.
"""
import re
from dataclasses import dataclass
from functools import lru_cache

# Common Hausa words and phrases (deduplicated, curated).
# NOTE: Common English function words like "so", "me", "in" are deliberately
# excluded to avoid false positives on English text.
HAUSA_WORDS = {
    "nawa", "wannan", "farashi", "farashin", "saya", "sayi", "sayan", "ina",
    "yana", "nan", "akwai", "baba", "sannu", "barka", "lafiya", "gida",
    "kudi", "ku", "na", "ni", "ka", "ki", "mu", "su", "shi", "ita", "da",
    "ba", "ko", "amma", "sai", "daga", "zuwa", "cikin", "wani", "wata",
    "wasu", "yaushe", "zan", "samu", "turo", "min", "mana", "maka", "miki",
    "hotuna", "hoto", "mutum", "magana", "tallafi", "tallace", "kayan",
    "kaya", "sako", "sakon", "gaskiya", "eh", "a'a", "yau", "gobe", "jibi",
    "daren", "rana", "lokaci", "wuri", "yaya", "menene", "don", "ne", "ce",
    "saboda", "sabon", "sabbin", "tayi", "kudin", "bashi", "bana", "ban",
    "zaka", "zaki", "zaku", "idan", "kana", "kina", "kuna", "sosai", "yi",
    "hakuri", "fahimci", "sake", "wanda", "wacce", "wadanda",
    "wadannan", "wancan", "waccan", "wadancan", "kamar", "yadda", "kafin",
    "kuma", "bayan", "yayin", "duk", "dukkan", "kowane", "kowace",
    "wane", "wace", "wadanne", "nagode", "godiya", "alhamdu", "alhamdulillah",
    "subhanallah", "wallahi", "balle", "kadan", "matuka",
    "matukar", "hakika", "lalle", "lallai", "tabbas", "tabbatacce", "babu",
    "komai", "kome",
    # Common multi-word phrases
    "nawa ne", "nawa ce", "ina so", "ina son", "ina bukatar", "ina neman",
    "zaka iya", "zaki iya", "za ka iya", "za ki iya", "taya muna",
    "barka da", "sannu da", "lafiya lau", "ina kwana", "ina wuni",
    "sai an jima", "sai gobe", "sai da safe", "barka da rana",
    "barka da yamma", "barka da dare", "allah ya sa", "allah ya ba mu",
    "na gode", "mun gode", "masha allah", "insha allah", "ko da",
    "ko da yake", "duk da", "duk da haka", "sai dai", "sai kawai",
    "kadan kadan", "da yawa", "da kadan", "da gaske", "da gaskiya",
    "yana da", "akwai da", "babu shakka", "babu wata", "babu wani",
    "babu komai", "duk abin", "duk wanda", "duk wacce", "duk wadanda",
    "duk wadannan", "duk wancan", "duk waccan", "duk wadancan",
}

# Precompute a version with only single-token (no-space) entries for
# fast per-word lookups.
HAUSA_SINGLE_WORDS = frozenset(w for w in HAUSA_WORDS if " " not in w)
HAUSA_PHRASES = frozenset(w for w in HAUSA_WORDS if " " in w)

_TOKEN_RE = re.compile(r"[a-zA-Z']+")

# PERF: a single compiled alternation, checked once per call, instead of
# looping `phrase in lowered` over every phrase in HAUSA_PHRASES (previously
# ~30+ full substring scans per message). Longest phrases first so a longer
# match isn't shadowed by a shorter prefix during alternation.
_PHRASE_RE = re.compile(
    "|".join(re.escape(p) for p in sorted(HAUSA_PHRASES, key=len, reverse=True))
)


@dataclass(frozen=True)
class LanguageDetectionResult:
    language: str          # one of: "en", "ha", "ha-en", "unknown"
    hausa_ratio: float      # fraction of tokens recognized as Hausa
    hausa_hits: int
    total_tokens: int


def _tokenize(text: str) -> tuple[str, ...]:
    return tuple(_TOKEN_RE.findall(text.lower()))


@lru_cache(maxsize=2048)
def _detect_language_cached(text: str) -> LanguageDetectionResult:
    """Cached core implementation, keyed on the raw text. Wrapped by
    detect_language() so callers keep a simple str -> result API. Caching
    pays off because webhook retries, duplicate inbound messages, and
    repeated short replies ("ok", "yes", "nawa ne?") are common in a
    chat/commerce context.
    """
    lowered = text.lower()
    phrase_hit = bool(_PHRASE_RE.search(lowered))

    tokens = _tokenize(text)
    total = len(tokens)
    if total == 0:
        return LanguageDetectionResult("unknown", 0.0, 0, 0)

    hausa_hits = sum(1 for t in tokens if t in HAUSA_SINGLE_WORDS)
    ratio = hausa_hits / total

    # A handful of Hausa words (na, da, ba...) can coincide with short
    # English tokens. A single such match in an otherwise English
    # sentence is noise, not evidence of Hausa — require either a
    # recognized phrase or at least two independent word matches
    # before leaning toward Hausa.
    if phrase_hit and ratio >= 0.6:
        language = "ha"
    elif ratio >= 0.7:
        language = "ha"
    elif hausa_hits <= 1 and not phrase_hit:
        language = "en"
    elif ratio > 0.15 or phrase_hit:
        language = "ha-en"
    else:
        language = "en"

    return LanguageDetectionResult(language, ratio, hausa_hits, total)


def detect_language(text: str) -> LanguageDetectionResult:
    """Detect whether `text` is English, Hausa, or a Hausa/English mix.

    Strategy:
      1. Check for known multi-word Hausa phrases first (strong signal),
         via one precompiled regex instead of per-phrase substring scans.
      2. Tokenize and count how many individual tokens are recognized
         Hausa words.
      3. Classify based on the ratio of Hausa tokens to total tokens.

    Results are cached (see _detect_language_cached) since repeated or
    duplicate inbound messages are common.
    """
    if not text or not text.strip():
        return LanguageDetectionResult("unknown", 0.0, 0, 0)
    return _detect_language_cached(text)


if __name__ == "__main__":
    samples = [
        "nawa ne farashin wannan?",
        "How much is this item?",
        "ina so na saya, but how much is the price?",
        "",
    ]
    for s in samples:
        print(s, "->", detect_language(s))
