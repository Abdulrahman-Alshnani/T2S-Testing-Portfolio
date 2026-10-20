"""Unit tests for greedy compound span detection before mBART."""

from unittest.mock import patch

import pytest

from translation_api.views import _greedy_compound_spans, _span_is_known_lexicon_phrase


@pytest.mark.unit
def test_greedy_returns_full_phrase_when_whole_input_known():
    with patch(
        "translation_api.views._span_is_known_lexicon_phrase",
        side_effect=lambda s: s == "وزارة المالية",
    ):
        assert _greedy_compound_spans("وزارة المالية") == ["وزارة المالية"]


@pytest.mark.unit
def test_greedy_returns_none_when_only_prefix_is_known():
    """Partial scan must not emit a lone prefix when the full compound is OOV."""
    with patch(
        "translation_api.views._span_is_known_lexicon_phrase",
        side_effect=lambda s: s == "وزارة",
    ):
        assert _greedy_compound_spans("وزارة المالية") is None


@pytest.mark.unit
def test_conjunction_phrase_splits_into_two_spans_when_both_known():
    with patch(
        "translation_api.views._span_is_known_lexicon_phrase",
        side_effect=lambda s: s in {"الأحمر", "الأسود"},
    ), patch(
        "translation_api.services.lemma_cache.resolve_token_to_lemma",
        side_effect=lambda s: s,
    ):
        assert _greedy_compound_spans("الأحمر والأسود") == ["الأحمر", "الأسود"]


@pytest.mark.critical
def test_span_known_delegates_to_lemma_cache():
    with patch(
        "translation_api.services.lemma_cache.contains_exact_lexicon_phrase",
        return_value=True,
    ) as mock_contains:
        assert _span_is_known_lexicon_phrase("test") is True
        mock_contains.assert_called()
