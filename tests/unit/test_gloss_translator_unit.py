"""
Unit tests for GlossTranslator with mocked mBART weights.

Service-level test bodies live in test_gloss_translator_service.py; this module
holds pytest-marked registration checks only.
"""

import pytest


@pytest.mark.unit
class TestGlossTranslatorRegistered:
    """Sanity check that gloss_translator helpers are importable from tests/."""

    def test_gloss_to_words_function_exists(self):
        from translation_api.services.gloss_translator import gloss_to_words

        assert callable(gloss_to_words)

    def test_translate_to_gloss_function_exists(self):
        from translation_api.services.gloss_translator import translate_to_gloss

        assert callable(translate_to_gloss)
