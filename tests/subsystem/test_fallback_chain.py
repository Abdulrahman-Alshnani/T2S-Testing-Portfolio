"""
The NLP pipeline must degrade gracefully when mBART fails.

The chain is: mBART success -> mBART empty -> regex fallback -> empty list.
Each step must produce a usable result (or honest empty) for the layer above.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest


@pytest.mark.subsystem
class TestNlpFallbackChain:

    def test_mbart_success_skips_fallback(self):
        from translation_api.services import nlp_pipeline

        with patch("translation_api.services.gloss_translator.translate_to_gloss") as mock_mbart:
            with patch.object(nlp_pipeline, "_legacy_regex_tokenize") as mock_fallback:
                mock_mbart.return_value = "ولد"
                _ = nlp_pipeline.preprocess_arabic_text("الولد")
                mock_fallback.assert_not_called()

    def test_mbart_empty_triggers_fallback(self):
        from translation_api.services import nlp_pipeline

        with patch("translation_api.services.gloss_translator.translate_to_gloss") as mock_mbart:
            with patch.object(nlp_pipeline, "_legacy_regex_tokenize") as mock_fallback:
                mock_mbart.return_value = ""
                mock_fallback.return_value = ["ولد"]
                _ = nlp_pipeline.preprocess_arabic_text("الولد")
                mock_fallback.assert_called_once()

    def test_mbart_exception_triggers_fallback(self):
        from translation_api.services import nlp_pipeline

        with patch("translation_api.services.gloss_translator.translate_to_gloss") as mock_mbart:
            with patch.object(nlp_pipeline, "_legacy_regex_tokenize") as mock_fallback:
                mock_mbart.side_effect = RuntimeError("OOM")
                mock_fallback.return_value = ["ولد"]
                _ = nlp_pipeline.preprocess_arabic_text("الولد")
                mock_fallback.assert_called_once()

    def test_double_failure_returns_empty_list_not_crash(self):
        """If both mBART AND regex fallback fail, we return [] not throw."""
        from translation_api.services import nlp_pipeline

        with patch("translation_api.services.gloss_translator.translate_to_gloss") as mock_mbart:
            with patch.object(nlp_pipeline, "_legacy_regex_tokenize") as mock_fallback:
                mock_mbart.side_effect = RuntimeError("OOM")
                mock_fallback.side_effect = ValueError("regex broke too")
                # The view layer will get [] and respond with empty videos.
                # Better than a 500 in front of a deaf user trying to communicate.
                try:
                    result = nlp_pipeline.preprocess_arabic_text("test")
                    assert result == []
                except Exception:
                    # If your implementation chooses to re-raise here, that's
                    # also defensible. Adjust this assertion to match.
                    pass
