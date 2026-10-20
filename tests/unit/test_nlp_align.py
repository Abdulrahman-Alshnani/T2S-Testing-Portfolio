"""Unit tests for lexicon token alignment."""

import pytest

from translation_api.services.nlp_pipeline import (
    align_tokens_to_lexicon,
    are_plausible_synonyms,
    redirect_token_to_lexicon_synonym,
)


@pytest.mark.unit
class TestAlignTokensToLexicon:
    def test_restores_al_on_proper_nouns(self):
        known = ["الأردن", "الجمعة", "البتراء"]
        assert align_tokens_to_lexicon(["أردن"], known) == ["الأردن"]
        assert align_tokens_to_lexicon(["جمعة"], known) == ["الجمعة"]

    def test_strips_clitic_waw(self):
        known = ["الأردن", "العقبة"]
        assert align_tokens_to_lexicon(["والأردن"], known) == ["الأردن"]
        assert align_tokens_to_lexicon(["والعقبة"], known) == ["العقبة"]

    def test_curated_synonym_redirect(self):
        known = ["فوق", "بعد", "كتب"]
        assert redirect_token_to_lexicon_synonym("على", known) == "فوق"
        assert redirect_token_to_lexicon_synonym("ثم", known) == "بعد"
        assert redirect_token_to_lexicon_synonym("فوق", known) == "فوق"

    def test_are_plausible_synonyms(self):
        assert are_plausible_synonyms("على", "فوق")
        assert are_plausible_synonyms("ثم", "بعد")
        assert not are_plausible_synonyms("اخي", "أنا")
        assert not are_plausible_synonyms("يراجع", "يساند")
