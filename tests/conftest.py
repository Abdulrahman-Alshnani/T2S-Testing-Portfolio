"""
Pytest fixtures shared across the T2S test suite.

Test data is isolated with category='__test__' and removed after each test.
Integration tests use the production Supabase database (mirrored TEST config).
"""

from __future__ import annotations

import logging
import random
from typing import Callable, List

import numpy as np
import pytest
from django.conf import settings

logger = logging.getLogger(__name__)

EMBEDDING_DIM = 768
TEST_CATEGORY = "__test__"
TEST_PREFIX = "test_"
RANDOM_SEED = 42


@pytest.fixture(autouse=True)
def cleanup_test_data(db, request):
    """
    Remove all SignWord rows tagged with the test category after each test.

    Every factory-created row must set category=TEST_CATEGORY or cleanup will miss it.
    """
    yield
    from translation_api.models import SignWord

    deleted_count, _ = SignWord.objects.filter(category=TEST_CATEGORY).delete()
    if deleted_count:
        logger.debug("Cleaned up %d test SignWord rows", deleted_count)


@pytest.fixture
def test_signword_factory(db) -> Callable:
    """
    Factory for SignWord rows with test isolation markers.

    Lemmas are stored without a prefix so RPC lookups match real user input.
    gloss_id carries the test_ prefix for traceability.
    """
    from translation_api.models import SignWord, VideoMapping

    def _factory(
        lemma: str,
        is_compound: bool = False,
        word_count: int = 1,
        embedding: List[float] | None = None,
        with_video: bool = True,
        gloss_id: str | None = None,
    ) -> SignWord:
        storage_url = f"https://test.example.com/{lemma}.mp4"
        sign_word, _ = SignWord.objects.update_or_create(
            lemma=lemma,
            defaults={
                "word": lemma,
                "arabic_text": lemma,
                "video_url": storage_url,
                "gloss_id": gloss_id or f"{TEST_PREFIX}GLOSS_{lemma}",
                "is_compound": is_compound,
                "word_count": word_count,
                "embedding": embedding,
                "category": TEST_CATEGORY,
            },
        )
        if with_video:
            VideoMapping.objects.update_or_create(
                signword=sign_word,
                sequence_order=1,
                defaults={
                    "storage_url": storage_url,
                    "duration_ms": 1500,
                },
            )
        return sign_word

    return _factory


@pytest.fixture
def mock_embedding() -> Callable:
    """Deterministic normalized 768-dimensional vectors from a seed string."""

    def _generate(seed_text: str = "default") -> List[float]:
        rng = random.Random(seed_text)
        vector = np.array([rng.gauss(0, 1) for _ in range(EMBEDDING_DIM)])
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        return vector.tolist()

    return _generate


@pytest.fixture
def similar_embeddings(mock_embedding) -> Callable:
    """Build two unit vectors with approximately target cosine similarity."""

    def _generate(target_similarity: float) -> tuple:
        vector_one = np.array(mock_embedding("base"))
        noise = np.array(mock_embedding("noise"))
        noise = noise - np.dot(noise, vector_one) * vector_one
        noise = noise / np.linalg.norm(noise)
        alpha = target_similarity
        beta = np.sqrt(max(0.0, 1 - target_similarity**2))
        vector_two = alpha * vector_one + beta * noise
        vector_two = vector_two / np.linalg.norm(vector_two)
        return vector_one.tolist(), vector_two.tolist()

    return _generate


@pytest.fixture(scope="session")
def real_embedding_service():
    """
    AraBERT singleton loaded once per session.

    Requires torch and transformers to be installed.
    """
    pytest.importorskip("torch")
    pytest.importorskip("transformers")
    from translation_api.services.embedding_service import get_embedding_service

    return get_embedding_service()


@pytest.fixture
def seeded_lexicon(test_signword_factory, mock_embedding) -> dict:
    """Small known lexicon for integration and use-case tests."""
    lexicon = {}
    lexicon["كتب"] = test_signword_factory(
        lemma="كتب",
        embedding=mock_embedding("write_verb"),
    )
    lexicon["قرأ"] = test_signword_factory(
        lemma="قرأ",
        embedding=mock_embedding("read_verb"),
    )
    lexicon["ذهب"] = test_signword_factory(
        lemma="ذهب",
        embedding=mock_embedding("go_verb"),
    )
    lexicon["مدرسة"] = test_signword_factory(
        lemma="مدرسة",
        embedding=None,
    )
    lexicon["بيت"] = test_signword_factory(
        lemma="بيت",
        embedding=None,
    )
    lexicon["السلام عليكم"] = test_signword_factory(
        lemma="السلام عليكم",
        is_compound=True,
        word_count=2,
        embedding=mock_embedding("greeting"),
    )
    lexicon["رئيس الوزراء"] = test_signword_factory(
        lemma="رئيس الوزراء",
        is_compound=True,
        word_count=2,
        embedding=mock_embedding("prime_minister"),
    )
    lexicon["فوق"] = test_signword_factory(
        lemma="فوق",
        embedding=mock_embedding("above"),
    )
    lexicon["بعد"] = test_signword_factory(
        lemma="بعد",
        embedding=mock_embedding("after"),
    )
    lexicon["أنا"] = test_signword_factory(
        lemma="أنا",
        embedding=mock_embedding("i_pronoun"),
    )
    return lexicon


@pytest.fixture
def api_client():
    from rest_framework.test import APIClient

    return APIClient()


@pytest.fixture(scope="session")
def project_root_path():
    import os

    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture
def warm_client(api_client, db):
    """APIClient after warmup so models are loaded."""
    api_client.get("/api/v1/health/warmup/")
    return api_client


@pytest.fixture
def mock_arabert_singleton(monkeypatch):
    from unittest.mock import MagicMock

    fake_vector = [0.001] * EMBEDDING_DIM
    fake_service = MagicMock()
    fake_service.embed_query.return_value = fake_vector
    fake_service.encode.return_value = fake_vector

    monkeypatch.setattr(
        "translation_api.services.embedding_service.get_embedding_service",
        lambda: fake_service,
    )
    return fake_service


@pytest.fixture
def mock_mbart(monkeypatch):
    from unittest.mock import MagicMock

    fake_translate = MagicMock()
    fake_translate.return_value = "تجربة"

    monkeypatch.setattr(
        "translation_api.services.gloss_translator.translate_to_gloss",
        fake_translate,
    )
    return fake_translate
