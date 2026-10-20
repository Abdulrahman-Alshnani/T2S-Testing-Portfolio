"""
End-to-end check: after warmup runs, the next translate call is fast.

This is the user-visible promise of the warm-up feature. If warm-up runs but
the next translate request still pays the model load cost, warm-up is broken.
"""

from __future__ import annotations

import time

import pytest


@pytest.mark.subsystem
@pytest.mark.slow
@pytest.mark.requires_mbart
@pytest.mark.requires_arabert
class TestWarmupThenTranslate:

    def test_translate_after_warmup_is_fast(self, db):
        """Warm-up should eliminate the cold-start penalty."""
        from rest_framework.test import APIClient

        client = APIClient()

        # Hit warmup first. This is the "demo prep" path.
        warmup_response = client.get("/api/v1/health/warmup/")
        assert warmup_response.status_code == 200

        # Now translate something. This should be fast because models are loaded.
        started = time.perf_counter()
        response = client.post(
            "/api/v1/translate/",
            {"text": "بعد"},
            format="json",
        )
        elapsed_ms = (time.perf_counter() - started) * 1000

        assert response.status_code == 200
        # Generous threshold: a warm translate request should complete in
        # well under 3 seconds. The exact number depends on hardware.
        assert elapsed_ms < 3000, (
            f"Translate took {elapsed_ms:.0f}ms after warmup; expected <3000ms. "
            "Warm-up may not be doing what it claims."
        )
