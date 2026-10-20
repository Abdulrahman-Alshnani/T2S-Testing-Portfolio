"""
Input validation tests for the translation request serializer.

These guard the API surface against malformed clients, oversize payloads,
and injection-shaped inputs. Pure unit tests — no database, no models.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest


@pytest.mark.unit
class TestTranslationRequestSerializer:

    def _serializer(self, payload):
        from translation_api.serializers import TranslationRequestSerializer
        return TranslationRequestSerializer(data=payload)

    def test_valid_arabic_input_passes_validation(self):
        s = self._serializer({"text": "كرة السلة"})
        assert s.is_valid(), s.errors

    @patch(
        "translation_api.serializers.is_known_lexicon_gloss",
        return_value=True,
    )
    def test_english_lexicon_gloss_passes(self, _mock_known_gloss):
        s = self._serializer({"text": "Ministry Of Finance"})
        assert s.is_valid(), s.errors

    def test_digit_and_english_number_words_pass_validation(self):
        for value in ("1", "one", "2", "two", "10", "ten"):
            s = self._serializer({"text": value})
            assert s.is_valid(), (value, s.errors)

    def test_missing_text_field_fails_validation(self):
        s = self._serializer({})
        assert not s.is_valid()
        assert "text" in s.errors

    def test_empty_text_fails_validation(self):
        s = self._serializer({"text": ""})
        assert not s.is_valid()

    def test_whitespace_only_text_fails_validation(self):
        s = self._serializer({"text": "    "})
        assert not s.is_valid()

    def test_text_at_max_length_passes(self):
        # The settings default is 500. Anything at-or-under must pass.
        from django.conf import settings
        max_len = getattr(settings, "T2S_MAX_INPUT_LENGTH", 500)
        s = self._serializer({"text": "ا" * max_len})
        assert s.is_valid(), s.errors

    def test_text_over_max_length_fails(self):
        from django.conf import settings
        max_len = getattr(settings, "T2S_MAX_INPUT_LENGTH", 500)
        s = self._serializer({"text": "ا" * (max_len + 1)})
        assert not s.is_valid()

    def test_numeric_text_is_accepted_as_number(self):
        # Integers are coerced to strings and normalized to Arabic number words.
        s = self._serializer({"text": 12345})
        assert s.is_valid(), s.errors

    def test_html_injection_does_not_crash(self):
        # The serializer doesn't need to sanitize HTML — the response shape
        # makes XSS impossible — but it must not crash on it.
        s = self._serializer({"text": "<script>alert('xss')</script>"})
        # Either valid (and downstream handles it) or invalid (rejected).
        # Either is fine; crashing is not.
        s.is_valid()


@pytest.mark.unit
class TestTranslationResponseShape:
    """The OpenAPI contract says the response has certain required fields."""

    def test_response_serializer_accepts_full_payload(self):
        from translation_api.serializers import TranslationResponseSerializer
        payload = {
            "videos": [
                {
                    "sequence_order": 1,
                    "matched_lemma": "كرة السلة",
                    "storage_url": "https://example.com/basketball.mp4",
                    "match_type": "compound",
                    "confidence": 1.0,
                    "gloss_id": "GLOSS_BASKETBALL",
                }
            ],
            "metadata": {
                "input_text": "كرة السلة",
                "lemma_count": 1,
                "timing_ms": {"total": 250, "nlp": 50, "embedding": 100, "database": 100},
            },
        }
        s = TranslationResponseSerializer(data=payload)
        # If the serializer rejects this shape, the OpenAPI contract is broken.
        assert s.is_valid(), s.errors
