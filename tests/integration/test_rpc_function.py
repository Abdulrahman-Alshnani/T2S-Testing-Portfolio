"""
Direct SQL tests for hybrid_translate_search and database prerequisites.

Bypasses the Django service layer to verify RPC logic and schema indexes.
"""

import pytest
from django.db import connection


@pytest.mark.integration
@pytest.mark.critical
class TestRPCFunctionDirect:
    """Calls hybrid_translate_search via raw SQL."""

    def _call_rpc(self, lemmas, phrase, embedding, threshold=0.75, per_token_mode=False):
        embedding_string = "[" + ",".join(f"{value:.6f}" for value in embedding) + "]"
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT sequence_order, matched_lemma, storage_url,
                       match_type, confidence, gloss_id
                FROM hybrid_translate_search(
                    %s::TEXT[], %s::TEXT, %s::VECTOR(768), %s::FLOAT, %s::BOOLEAN
                )
                ORDER BY sequence_order ASC
                """,
                [lemmas, phrase, embedding_string, threshold, per_token_mode],
            )
            return cursor.fetchall()

    def test_rpc_function_exists(self):
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT proname FROM pg_proc WHERE proname = 'hybrid_translate_search'"
            )
            assert cursor.fetchone() is not None

    def test_pgvector_extension_enabled(self):
        with connection.cursor() as cursor:
            cursor.execute("SELECT extname FROM pg_extension WHERE extname = 'vector'")
            assert cursor.fetchone() is not None

    def test_required_indexes_exist(self):
        expected_indexes = {
            "signword_embedding_idx",
            "signword_lemma_idx",
            "signword_compound_idx",
        }
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT indexname FROM pg_indexes "
                "WHERE tablename = 'translation_api_signword'"
            )
            actual = {row[0] for row in cursor.fetchall()}
        missing = expected_indexes - actual
        assert not missing, f"Missing indexes: {missing}"

    def test_rpc_handles_null_embeddings_gracefully(
        self, seeded_lexicon, mock_embedding
    ):
        rows = self._call_rpc(
            lemmas=["totally_unknown_query"],
            phrase="totally_unknown_query",
            embedding=mock_embedding("random"),
        )
        assert len(rows) == 1
        assert rows[0][3] in ("semantic", "not_found")

    def test_rpc_compound_takes_priority_over_lemma(
        self, test_signword_factory, mock_embedding
    ):
        test_signword_factory(
            lemma="الذكاء الاصطناعي",
            is_compound=True,
            word_count=2,
            embedding=mock_embedding("AI"),
        )
        test_signword_factory(
            lemma="الذكاء",
            is_compound=False,
            embedding=mock_embedding("intelligence"),
        )
        rows = self._call_rpc(
            lemmas=["الذكاء", "الاصطناعي"],
            phrase="الذكاء الاصطناعي",
            embedding=mock_embedding("AI"),
        )
        assert len(rows) == 1
        assert rows[0][3] == "compound"
