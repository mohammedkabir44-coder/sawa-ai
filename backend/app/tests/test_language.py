"""Tests for the Hausa / English language detection module.

These tests are self-contained — they do not require a database or any
external services, so they can run independently of the conftest fixtures.
"""
import pytest

from app.services.ai.language import (
    detect_language,
    HAUSA_SINGLE_WORDS,
    HAUSA_PHRASES,
    _PHRASE_RE,
)


# ---------------------------------------------------------------------------
# Basic classification
# ---------------------------------------------------------------------------
class TestBasicClassification:
    def test_pure_hausa(self):
        result = detect_language("nawa ne farashin wannan?")
        assert result.language == "ha"
        assert result.hausa_hits == 4
        assert result.total_tokens == 4
        assert result.hausa_ratio == 1.0

    def test_pure_english(self):
        result = detect_language("How much is this item?")
        assert result.language == "en"
        assert result.hausa_hits == 0
        assert result.total_tokens == 5

    def test_mixed_hausa_english(self):
        result = detect_language("ina so na saya, but how much is the price?")
        assert result.language == "ha-en"
        assert result.hausa_hits == 3
        assert result.total_tokens == 10

    def test_empty_string(self):
        result = detect_language("")
        assert result.language == "unknown"
        assert result.hausa_hits == 0
        assert result.total_tokens == 0

    def test_whitespace_only(self):
        result = detect_language("   \t\n  ")
        assert result.language == "unknown"
        assert result.hausa_hits == 0
        assert result.total_tokens == 0


# ---------------------------------------------------------------------------
# Edge cases — single Hausa word in English text should be "en"
# ---------------------------------------------------------------------------
class TestEdgeCases:
    def test_single_hausa_word_in_english(self):
        """A single Hausa word like 'na' or 'da' in an English sentence
        should not trigger ha-en — it's likely noise."""
        result = detect_language("I need na more items")
        assert result.language == "en"

    def test_single_hausa_word_no_phrase(self):
        """A single Hausa word alone is 100% Hausa, so it should be 'ha'."""
        result = detect_language("da")
        assert result.language == "ha"

    def test_two_hausa_words_no_phrase(self):
        """Two Hausa words alone are 100% Hausa, so it should be 'ha'."""
        result = detect_language("na da")
        assert result.language == "ha"

    def test_phrase_detection_triggers_ha_en(self):
        """A recognized Hausa phrase with low ratio should be ha-en."""
        result = detect_language("barka da rana, how are you?")
        assert result.language == "ha-en"

    def test_phrase_with_high_ratio_is_ha(self):
        """A recognized Hausa phrase with high ratio should be ha."""
        result = detect_language("barka da rana")
        assert result.language == "ha"

    def test_punctuation_and_numbers(self):
        result = detect_language("Nawa ne farashin wannan? 15,000 naira")
        assert result.language == "ha"

    def test_case_insensitive(self):
        result = detect_language("NAWA NE FARASHIN WANNAN?")
        assert result.language == "ha"

    def test_hausa_with_english_words(self):
        """Hausa sentence with some English loanwords."""
        result = detect_language("Ina son saya iPhone guda daya")
        assert result.language == "ha-en"


# ---------------------------------------------------------------------------
# Caching
# ---------------------------------------------------------------------------
class TestCaching:
    def test_cached_result_is_same_object(self):
        """lru_cache should return the same object for the same input."""
        from app.services.ai.language import _detect_language_cached
        _detect_language_cached.cache_clear()
        r1 = _detect_language_cached("nawa ne farashin wannan?")
        r2 = _detect_language_cached("nawa ne farashin wannan?")
        assert r1 is r2

    def test_different_inputs_different_results(self):
        from app.services.ai.language import _detect_language_cached
        _detect_language_cached.cache_clear()
        r1 = _detect_language_cached("How much is this?")
        r2 = _detect_language_cached("Nawa ne farashin wannan?")
        assert r1 is not r2
        assert r1.language == "en"
        assert r2.language == "ha"


# ---------------------------------------------------------------------------
# Data structure integrity
# ---------------------------------------------------------------------------
class TestDataIntegrity:
    def test_frozen_dataclass(self):
        """LanguageDetectionResult should be frozen (immutable)."""
        result = detect_language("hello")
        with pytest.raises(Exception):
            result.language = "ha"

    def test_hausa_single_words_are_frozenset(self):
        assert isinstance(HAUSA_SINGLE_WORDS, frozenset)

    def test_hausa_phrases_are_frozenset(self):
        assert isinstance(HAUSA_PHRASES, frozenset)

    def test_phrase_re_compiled(self):
        """_PHRASE_RE should be a compiled regex pattern."""
        import re
        assert isinstance(_PHRASE_RE, re.Pattern)

    def test_no_overlap_between_single_and_phrases(self):
        """No word should appear in both single words and phrases."""
        overlap = HAUSA_SINGLE_WORDS & HAUSA_PHRASES
        assert len(overlap) == 0

    def test_all_phrases_have_spaces(self):
        """All entries in HAUSA_PHRASES should contain a space."""
        for phrase in HAUSA_PHRASES:
            assert " " in phrase

    def test_all_single_words_have_no_spaces(self):
        """All entries in HAUSA_SINGLE_WORDS should not contain a space."""
        for word in HAUSA_SINGLE_WORDS:
            assert " " not in word
