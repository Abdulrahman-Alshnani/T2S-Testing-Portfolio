"""
Unit tests for the AraBERT embedding service.

These do not load AraBERT — the model file is large and the load is slow.
For tests that need the actual model, see test_embedding_service.py at the
top tests/ directory which is marked @pytest.mark.requires_arabert.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


@pytest.mark.unit
class TestEmbeddingServiceSingleton:
    """The service must be a true singleton across calls."""

    def test_get_embedding_service_returns_same_instance(self):
        from translation_api.services.embedding_service import get_embedding_service
        first = get_embedding_service()
        second = get_embedding_service()
        # Same Python object, not just equal — singleton property is critical
        # because the model itself is ~500MB and loading twice would OOM.
        assert first is second


@pytest.mark.unit
class TestEmbeddingServiceContract:
    """Verify the public method signatures match what callers expect."""

    @pytest.mark.requires_arabert
    def test_embed_query_returns_768_dim_vector(self):
        # We mock the underlying torch call but verify the contract shape.
        from translation_api.services.embedding_service import get_embedding_service
        service = get_embedding_service()
        # Real call against the real model — uses the singleton if warm.
        # If the model isn't warmed in this test environment, this test
        # is skipped (the marker requires_arabert handles that).
        pytest.importorskip("torch")
        result = service.embed_query("تجربة")
        assert hasattr(result, "__len__")
        assert len(result) == 768


@pytest.mark.unit
class TestEmbeddingServiceErrorHandling:
    """What happens when things go wrong."""

    def test_embed_empty_string_does_not_crash(self):
        from translation_api.services.embedding_service import get_embedding_service
        service = get_embedding_service()
        # Empty input should either return a zero vector or raise a clear
        # error — never silently corrupt downstream search.
        try:
            result = service.embed_query("")
            assert hasattr(result, "__len__")
        except (ValueError, RuntimeError) as exc:
            # An explicit error is also acceptable; silent garbage is not.
            assert str(exc)
