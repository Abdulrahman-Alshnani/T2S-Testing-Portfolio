"""
Unit tests for the AraBERT embedding service.

Verifies singleton behavior, output dimension, normalization, validation,
and deterministic inference for the same input text.
"""

import numpy as np
import pytest

from translation_api.services.embedding_service import get_embedding_service

EXPECTED_DIM = 768
UNIT_NORM_TOLERANCE = 1e-5


@pytest.mark.unit
@pytest.mark.critical
class TestEmbeddingServiceSingleton:
    """Verifies the embedding service singleton pattern."""

    def test_get_embedding_service_returns_same_instance(self, real_embedding_service):
        first = get_embedding_service()
        second = get_embedding_service()
        assert first is second, "Singleton pattern broken: instances differ"


@pytest.mark.unit
@pytest.mark.critical
class TestEmbeddingServiceOutput:
    """Verifies embed_query output contract."""

    def test_output_dimension_is_768(self, real_embedding_service):
        vector = real_embedding_service.embed_query("اللغة العربية")
        assert len(vector) == EXPECTED_DIM

    def test_output_is_unit_normalized(self, real_embedding_service):
        vector = real_embedding_service.embed_query("مرحبا")
        norm = np.linalg.norm(vector)
        assert abs(norm - 1.0) < UNIT_NORM_TOLERANCE

    def test_empty_input_raises_value_error(self, real_embedding_service):
        with pytest.raises(ValueError):
            real_embedding_service.embed_query("")
        with pytest.raises(ValueError):
            real_embedding_service.embed_query("   ")

    def test_deterministic_output(self, real_embedding_service):
        vector_one = real_embedding_service.embed_query("الذكاء الاصطناعي")
        vector_two = real_embedding_service.embed_query("الذكاء الاصطناعي")
        assert np.allclose(vector_one, vector_two, atol=1e-6)
