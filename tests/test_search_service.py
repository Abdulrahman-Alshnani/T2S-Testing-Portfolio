"""
Integration tests for the hybrid search service.

Includes the Honesty Principle star test: the system must never return a sign
video when vector similarity falls below the configured threshold.
"""

import pytest

from translation_api.services.search_service import execute_hybrid_search

DEFAULT_THRESHOLD = 0.75


@pytest.mark.integration
@pytest.mark.critical
class TestHybridSearchTiers:
    """Verifies compound, lemma, and semantic tiers."""

    def test_compound_match_short_circuits(self, seeded_lexicon, mock_embedding):
        results = execute_hybrid_search(
            lemmas=["السلام", "عليكم"],
            phrase="السلام عليكم",
            embedding=mock_embedding("any"),
            threshold=DEFAULT_THRESHOLD,
        )
        assert len(results) == 1
        assert results[0]["match_type"] == "compound"
        assert results[0]["confidence"] == 1.0

    def test_lemma_exact_match(self, seeded_lexicon, mock_embedding):
        results = execute_hybrid_search(
            lemmas=["كتب"],
            phrase="كتب",
            embedding=mock_embedding("any"),
            threshold=DEFAULT_THRESHOLD,
        )
        assert len(results) == 1
        assert results[0]["match_type"] == "lemma"
        assert results[0]["confidence"] == 1.0
        assert results[0]["storage_url"] is not None

    def test_semantic_fallback_above_threshold(
        self, seeded_lexicon, similar_embeddings, test_signword_factory
    ):
        vector_target, vector_query = similar_embeddings(target_similarity=0.90)
        test_signword_factory(lemma="target_word", embedding=vector_target)
        results = execute_hybrid_search(
            lemmas=["nonexistent_lemma"],
            phrase="nonexistent_lemma",
            embedding=vector_query,
            threshold=DEFAULT_THRESHOLD,
        )
        assert len(results) == 1
        assert results[0]["match_type"] == "semantic"
        assert results[0]["confidence"] >= DEFAULT_THRESHOLD

    @pytest.mark.honesty
    def test_honesty_principle_never_substitutes_below_threshold(
        self, seeded_lexicon, similar_embeddings, test_signword_factory
    ):
        """
        STAR TEST: below-threshold similarity must yield not_found with no video URL.
        """
        vector_target, vector_query = similar_embeddings(target_similarity=0.30)
        test_signword_factory(lemma="distant_word", embedding=vector_target)
        results = execute_hybrid_search(
            lemmas=["oov_query"],
            phrase="oov_query",
            embedding=vector_query,
            threshold=DEFAULT_THRESHOLD,
        )
        assert len(results) == 1
        assert results[0]["match_type"] == "not_found", (
            "HONESTY PRINCIPLE VIOLATED: low-confidence sign returned. "
            f"type={results[0]['match_type']} confidence={results[0]['confidence']}"
        )
        assert results[0]["storage_url"] is None
        assert results[0]["confidence"] < DEFAULT_THRESHOLD


@pytest.mark.integration
@pytest.mark.critical
class TestSequenceOrdering:
    """Verifies sequence_order follows input lemma order."""

    def test_sequence_order_preserved(self, seeded_lexicon, mock_embedding):
        lemmas = ["ذهب", "قرأ", "كتب"]
        results = execute_hybrid_search(
            lemmas=lemmas,
            phrase=" ".join(lemmas),
            embedding=mock_embedding("any"),
            threshold=DEFAULT_THRESHOLD,
        )
        assert len(results) == 3
        for index, expected_lemma in enumerate(lemmas, start=1):
            assert results[index - 1]["sequence_order"] == index
            assert results[index - 1]["matched_lemma"] == expected_lemma


@pytest.mark.integration
class TestMixedResultsScenario:
    """Verifies mixed lemma, semantic, and not_found rows in one request."""

    def test_partial_lexicon_coverage(
        self, seeded_lexicon, mock_embedding, similar_embeddings, test_signword_factory
    ):
        vector_target, vector_query = similar_embeddings(target_similarity=0.85)
        test_signword_factory(lemma="semantic_target", embedding=vector_target)
        results = execute_hybrid_search(
            lemmas=["كتب", "oov_for_semantic", "completely_unknown_xyz"],
            phrase="كتب oov_for_semantic completely_unknown_xyz",
            embedding=vector_query,
            threshold=DEFAULT_THRESHOLD,
        )
        assert len(results) == 3
        assert results[0]["match_type"] == "lemma"


@pytest.mark.integration
class TestEdgeCases:
    """Boundary behavior for hybrid search inputs."""

    def test_empty_lemma_list_returns_empty_results(self, seeded_lexicon, mock_embedding):
        results = execute_hybrid_search(
            lemmas=[],
            phrase="",
            embedding=mock_embedding("any"),
            threshold=DEFAULT_THRESHOLD,
        )
        assert results == []

    def test_threshold_parameter_respected(
        self, seeded_lexicon, similar_embeddings, test_signword_factory
    ):
        vector_target, vector_query = similar_embeddings(target_similarity=0.70)
        test_signword_factory(lemma="threshold_test", embedding=vector_target)
        results_strict = execute_hybrid_search(
            lemmas=["oov"],
            phrase="oov",
            embedding=vector_query,
            threshold=0.75,
        )
        assert results_strict[0]["match_type"] == "not_found"
        results_loose = execute_hybrid_search(
            lemmas=["oov"],
            phrase="oov",
            embedding=vector_query,
            threshold=0.65,
        )
        assert results_loose[0]["match_type"] == "semantic"
