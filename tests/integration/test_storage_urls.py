"""
Verify that the storage URLs in the database actually serve files.

A storage_url that returns 404 is worse than not_found — the user sees a
broken video player. These tests sample a subset of URLs and confirm they
are reachable.

Marked @pytest.mark.network because they make real HTTP calls. Skipped in
the default test run; run explicitly with `pytest -m network`.
"""

from __future__ import annotations

import random

import pytest
import requests


@pytest.mark.integration
@pytest.mark.network
@pytest.mark.slow
class TestStorageURLs:

    @pytest.fixture
    def sample_video_urls(self, db):
        from translation_api.models import VideoMapping
        urls = list(
            VideoMapping.objects
            .exclude(signword__category="__test__")
            .exclude(storage_url__isnull=True)
            .values_list("storage_url", flat=True)
        )
        # Sample 30 URLs randomly so the test runs in reasonable time.
        # Pass a fixed seed for reproducibility across CI runs.
        random.seed(42)
        return random.sample(urls, min(30, len(urls)))

    def test_sampled_urls_return_200(self, sample_video_urls):
        """30 random storage URLs should all serve their video."""
        failures = []
        for url in sample_video_urls:
            try:
                response = requests.head(url, timeout=10, allow_redirects=True)
                if response.status_code != 200:
                    failures.append((url, response.status_code))
            except requests.RequestException as exc:
                failures.append((url, f"connection error: {exc}"))

        assert not failures, (
            f"{len(failures)}/{len(sample_video_urls)} storage URLs failed:\n"
            + "\n".join(f"  {url}: {status}" for url, status in failures[:10])
        )

    def test_storage_urls_use_correct_bucket_name(self, db):
        """All URLs must use sign_videos (underscore), not sign-videos (hyphen)."""
        from translation_api.models import VideoMapping
        wrong_bucket = (
            VideoMapping.objects
            .filter(storage_url__icontains="/sign-videos/")
            .count()
        )
        assert wrong_bucket == 0, (
            f"{wrong_bucket} VideoMappings use the wrong bucket name 'sign-videos'. "
            "The correct bucket is 'sign_videos' (underscore)."
        )
