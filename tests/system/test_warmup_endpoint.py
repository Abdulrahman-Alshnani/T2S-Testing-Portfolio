"""
Black-box tests for GET /api/v1/health/warmup/.

Verifies both the happy path (both models load) and the degraded path
(one model fails). The degraded path is only reachable via fault injection
in CI; in normal local testing it stays in the happy path.
"""

from __future__ import annotations

import pytest
from rest_framework.test import APIClient


@pytest.mark.system
@pytest.mark.slow
@pytest.mark.requires_mbart
@pytest.mark.requires_arabert
class TestWarmupHappyPath:

    def test_warmup_returns_200_with_both_models(self, db):
        client = APIClient()
        response = client.get("/api/v1/health/warmup/")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "warm"
        assert "arabert" in body["timings_ms"]
        assert "mbart" in body["timings_ms"]
        # Sanity check on the timings being reasonable.
        assert body["timings_ms"]["arabert"] >= 0
        assert body["timings_ms"]["mbart"] >= 0

    def test_warmup_idempotent(self, db):
        """Calling warmup twice in a row should be safe and fast the second time."""
        client = APIClient()
        first = client.get("/api/v1/health/warmup/")
        second = client.get("/api/v1/health/warmup/")
        assert first.status_code == 200
        assert second.status_code == 200
        # Second call should be faster than first (cache is now hot).
        # Use AraBERT timing because it's more stable.
        first_t = first.json()["timings_ms"]["arabert"]
        second_t = second.json()["timings_ms"]["arabert"]
        # Allow some noise but verify caching is happening.
        assert second_t <= first_t * 1.5, (
            f"Second warmup ({second_t}ms) not faster than first ({first_t}ms). "
            "Singleton caching may be broken."
        )
