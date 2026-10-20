"""
Verify the Django ORM can talk to PostgreSQL correctly.

These tests assume a populated database. They do not modify data.
"""

from __future__ import annotations

import pytest


@pytest.mark.integration
class TestDatabaseConnectivity:

    def test_can_connect_to_database(self, db):
        """Basic round trip: query the database, get a result back."""
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            row = cursor.fetchone()
            assert row[0] == 1

    def test_pgvector_extension_is_enabled(self, db):
        """The whole project depends on pgvector. Verify it loaded."""
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT extname FROM pg_extension WHERE extname = 'vector'")
            row = cursor.fetchone()
            assert row is not None, (
                "pgvector extension is not enabled in this database. "
                "Run: CREATE EXTENSION IF NOT EXISTS vector;"
            )

    def test_hybrid_search_function_exists(self, db):
        """The RPC function must be deployed in the database."""
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT proname FROM pg_proc WHERE proname = 'hybrid_translate_search'"
            )
            row = cursor.fetchone()
            assert row is not None, (
                "hybrid_translate_search PL/pgSQL function is not deployed. "
                "Run database/functions/hybrid_translate_search.sql in database SQL console."
            )

    def test_lexicon_has_at_least_300_rows(self, db):
        """Sanity check that the database is populated, not empty."""
        from translation_api.models import SignWord
        count = SignWord.objects.exclude(category="__test__").count()
        assert count >= 300, (
            f"Lexicon has only {count} rows. Expected at least 300. "
            "Run ingestion scripts to populate."
        )


@pytest.mark.integration
class TestEmbeddingIndexes:

    def test_signword_embedding_index_exists(self, db):
        """The IVFFlat index is what makes Tier 3 fast."""
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT indexname FROM pg_indexes "
                "WHERE tablename = 'translation_api_signword' "
                "AND indexname LIKE '%embedding%'"
            )
            indexes = [row[0] for row in cursor.fetchall()]
            assert len(indexes) > 0, (
                "No embedding index found on translation_api_signword. "
                "Without this, Tier 3 semantic search will be slow."
            )
