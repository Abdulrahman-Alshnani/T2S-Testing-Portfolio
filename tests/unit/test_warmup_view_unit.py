"""
Unit tests for the warm-up endpoint.

Verifies the response shape and the 503-on-failure contract without actually
loading the models. Real model loading is exercised in Suite 3 (system tests).
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from rest_framework.test import APIClient


@pytest.mark.unit
class TestWarmupView:

    def test_warmup_success_returns_200_with_timings(self):
        client = APIClient()
        with patch(
            "translation_api.services.embedding_service.get_embedding_service"
        ) as mock_emb:
            with patch(
                "translation_api.services.gloss_translator.translate_to_gloss"
            ) as mock_mbart:
                mock_emb.return_value.embed_query.return_value = [0.0] * 768
                mock_mbart.return_value = "تجربة"
                response = client.get("/api/v1/health/warmup/")

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "warm"
        assert "arabert" in body["timings_ms"]
        assert "mbart" in body["timings_ms"]

    def test_warmup_arabert_failure_returns_503(self):
        client = APIClient()
        with patch(
            "translation_api.services.embedding_service.get_embedding_service"
        ) as mock_emb:
            with patch(
                "translation_api.services.gloss_translator.translate_to_gloss"
            ) as mock_mbart:
                mock_emb.side_effect = RuntimeError("model not found")
                mock_mbart.return_value = "تجربة"
                response = client.get("/api/v1/health/warmup/")

        assert response.status_code == 503
        body = response.json()
        assert body["status"] == "degraded"
        assert "arabert" in body["errors"]

    def test_warmup_post_method_not_allowed(self):
        # The endpoint is GET-only. POST must be rejected with 405.
        client = APIClient()
        response = client.post("/api/v1/health/warmup/")
        assert response.status_code == 405
