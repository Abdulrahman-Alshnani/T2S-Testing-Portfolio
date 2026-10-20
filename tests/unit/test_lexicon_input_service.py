"""Unit tests for lexicon_input helpers — verifies JSON normalisation and field extraction."""

import os
import unittest
from unittest.mock import patch

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

import django

django.setup()

from translation_api.services.lexicon_input import (
    _lemma_lookup_sets,
    is_known_lexicon_gloss,
    normalize_english_gloss,
    preprocess_lexicon_gloss,
)


class LexiconInputTests(unittest.TestCase):
    @patch("translation_api.services.search_service.get_all_lexicon_surface_forms")
    def test_financial_ministry_alias(self, mock_lemmas):
        mock_lemmas.return_value = ["Ministry Of Finance", "بعد"]
        _lemma_lookup_sets.cache_clear()
        self.assertTrue(is_known_lexicon_gloss("financial ministry"))
        self.assertEqual(
            normalize_english_gloss("financial ministry"),
            "Ministry Of Finance",
        )

    @patch("translation_api.services.lexicon_input._lemma_lookup_sets")
    def test_exact_compound_match(self, mock_sets):
        mock_sets.return_value = (
            {"ministry of finance".casefold()},
            ["Ministry Of Finance"],
        )
        self.assertTrue(is_known_lexicon_gloss("Ministry of Finance"))

    def test_preprocess_tokens(self):
        tokens = preprocess_lexicon_gloss("Ministry Of Finance")
        self.assertEqual(tokens, ["Ministry", "Of", "Finance"])


if __name__ == "__main__":
    unittest.main()
