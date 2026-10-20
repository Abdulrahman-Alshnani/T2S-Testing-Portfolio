"""
Unit tests for translation_api.services.nlp_pipeline.

Every test in this file mocks the mBART import so the real model never loads.
This keeps the suite fast (~50ms per test) and makes failures unambiguous —
if a test in here fails it is because of pipeline logic, not model behavior.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest


@pytest.mark.unit
class TestPreprocessArabicText:
    """Direct contract tests on the public preprocess_arabic_text function."""

    def test_empty_input_returns_empty_list(self):
        from translation_api.services.nlp_pipeline import preprocess_arabic_text
        assert preprocess_arabic_text("") == []

    def test_whitespace_only_input_returns_empty_list(self):
        from translation_api.services.nlp_pipeline import preprocess_arabic_text
        assert preprocess_arabic_text("   \t  \n ") == []

    def test_none_input_returns_empty_list(self):
        from translation_api.services.nlp_pipeline import preprocess_arabic_text

        assert preprocess_arabic_text(None) == []

    def test_mbart_success_path_returns_gloss_tokens(self):
        # When mBART produces a gloss, those tokens are what comes back.
        from translation_api.services import nlp_pipeline

        with patch.object(nlp_pipeline, "_legacy_regex_tokenize") as mock_fallback:
            with patch("translation_api.services.gloss_translator.translate_to_gloss") as mock_translate:
                with patch("translation_api.services.gloss_translator.gloss_to_words") as mock_split:
                    mock_translate.return_value = "ولد قرأ كتاب"
                    mock_split.return_value = ["ولد", "قرأ", "كتاب"]
                    result = nlp_pipeline.preprocess_arabic_text("الولد يقرأ الكتاب")

        assert result == ["ولد", "قرأ", "كتاب"]
        # Fallback must not have been called on the success path.
        mock_fallback.assert_not_called()

    def test_mbart_empty_gloss_falls_back_to_regex(self):
        # If mBART returns nothing useful, the legacy tokenizer takes over.
        from translation_api.services import nlp_pipeline

        with patch("translation_api.services.gloss_translator.translate_to_gloss") as mock_translate:
            with patch("translation_api.services.gloss_translator.gloss_to_words") as mock_split:
                mock_translate.return_value = ""
                mock_split.return_value = []
                result = nlp_pipeline.preprocess_arabic_text("كرة السلة")

        # The regex path should produce something for non-empty input.
        assert len(result) > 0

    def test_mbart_exception_falls_back_to_regex(self):
        # A model crash must not crash the API. Fallback is the safety net.
        from translation_api.services import nlp_pipeline

        with patch("translation_api.services.gloss_translator.translate_to_gloss") as mock_translate:
            mock_translate.side_effect = RuntimeError("CUDA out of memory")
            result = nlp_pipeline.preprocess_arabic_text("كرة السلة")

        # Some result must come back; the regex path handles it.
        assert isinstance(result, list)


@pytest.mark.unit
class TestLegacyRegexTokenize:
    """Tests for the regex fallback path directly."""

    def test_simple_arabic_tokenizes_correctly(self):
        from translation_api.services.nlp_pipeline import _legacy_regex_tokenize
        result = _legacy_regex_tokenize("الولد")
        # 'ال' prefix gets stripped; 'ولد' remains.
        assert "ولد" in result or "الولد" in result

    def test_punctuation_is_dropped(self):
        from translation_api.services.nlp_pipeline import _legacy_regex_tokenize
        result = _legacy_regex_tokenize("كرة ، السلة !")
        # Standalone punctuation must not be the only meaningful tokens.
        word_tokens = [t for t in result if any("\u0600" <= c <= "\u06FF" for c in t)]
        assert "كرة" in word_tokens or "السلة" in word_tokens or "سلة" in word_tokens
        for token in result:
            assert "!" not in token

    def test_diacritics_are_stripped(self):
        from translation_api.services.nlp_pipeline import _legacy_regex_tokenize
        # Input with fatha and shadda; output should not contain them.
        result = _legacy_regex_tokenize("كَتَبَ")
        for token in result:
            for char in token:
                # 0x064B through 0x065F are the tashkeel range.
                assert not (0x064B <= ord(char) <= 0x065F)

    def test_wazir_not_stripped_to_zir(self):
        """وزير is a lexicon lemma; legacy fallback must not strip its leading و."""
        from translation_api.services.nlp_pipeline import _legacy_regex_tokenize

        result = _legacy_regex_tokenize("تفقد وزير التعليم المدرسة")
        assert "زير" not in result
        assert "وزير" in result

    def test_conjunction_list_splits_waw_tokens(self):
        """والنسر / والقرد must become نسر / قرد in legacy fallback."""
        from translation_api.services.nlp_pipeline import _legacy_regex_tokenize

        result = _legacy_regex_tokenize("الأسد والنسر والقرد حيوانات الغابة")
        assert "والنسر" not in result
        assert "والقرد" not in result
        assert "نسر" in result
        assert "قرد" in result
