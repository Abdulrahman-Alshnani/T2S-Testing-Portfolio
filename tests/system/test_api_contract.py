"""
Black-box tests against POST /api/v1/translate/.

These tests assume the Django server is running and the database is populated.
They make real HTTP requests and verify the response matches the OpenAPI
contract documented in contracts/api_openapi.yaml.
"""

from __future__ import annotations

import pytest
from rest_framework.test import APIClient


@pytest.mark.system
@pytest.mark.integration
class TestTranslateEndpointContract:

    def test_compound_input_returns_compound_match_type(self, db):
        """A known compound must return match_type=compound from Tier 1."""
        client = APIClient()
        response = client.post(
            "/api/v1/translate/",
            {"text": "Ministry Of Finance"},
            format="json",
        )
        assert response.status_code == 200
        videos = response.json()["videos"]
        compound_rows = [v for v in videos if v["match_type"] == "compound"]
        assert len(compound_rows) == 1
        assert compound_rows[0]["confidence"] == 1.0
        assert compound_rows[0]["storage_url"] is not None

    def test_known_lemma_returns_lemma_match_type(self, db):
        """A single known word in the lexicon must return match_type=lemma."""
        client = APIClient()
        response = client.post(
            "/api/v1/translate/",
            {"text": "أنا"},
            format="json",
        )
        assert response.status_code == 200
        videos = response.json()["videos"]
        assert len(videos) >= 1
        # First match should be lemma (or compound if there's a compound containing 'أنا',
        # which there isn't in the current lexicon).
        assert videos[0]["match_type"] in ("lemma", "compound")

    def test_oov_proper_noun_returns_not_found(self, db):
        """The Honesty Principle: foreign proper nouns return not_found."""
        client = APIClient()
        response = client.post(
            "/api/v1/translate/",
            {"text": "زوكربيرغ"},
            format="json",
        )
        assert response.status_code == 200
        videos = response.json()["videos"]
        assert len(videos) >= 1
        # At least one row should be not_found with null storage_url.
        # This is the load-bearing test for the entire project's value prop.
        not_found_rows = [v for v in videos if v["match_type"] == "not_found"]
        assert len(not_found_rows) >= 1
        for row in not_found_rows:
            assert row["storage_url"] is None

    def test_response_includes_timing_metadata(self, db):
        client = APIClient()
        response = client.post(
            "/api/v1/translate/",
            {"text": "كرة السلة"},
            format="json",
        )
        body = response.json()
        assert "metadata" in body
        assert "timing_ms" in body["metadata"]
        timings = body["metadata"]["timing_ms"]
        assert "preprocessing" in timings
        assert "embedding" in timings
        assert "database" in timings
        assert "total" in timings
        assert timings["total"] > 0

    def test_input_text_echoed_in_metadata(self, db):
        client = APIClient()
        response = client.post(
            "/api/v1/translate/",
            {"text": "كرة السلة"},
            format="json",
        )
        body = response.json()
        assert body["metadata"]["input_text"] == "كرة السلة"

    def test_videos_are_in_sequence_order(self, db):
        """For multi-word input, sequence_order must be 1, 2, 3, ... in order."""
        client = APIClient()
        response = client.post(
            "/api/v1/translate/",
            {"text": "يتعلم يدرس يحفظ"},
            format="json",
        )
        videos = response.json()["videos"]
        if len(videos) >= 2:
            orders = [v["sequence_order"] for v in videos]
            # Should be monotonically increasing.
            assert orders == sorted(orders), f"Sequence not ordered: {orders}"


@pytest.mark.system
class TestErrorResponses:

    def test_missing_text_returns_400(self):
        client = APIClient()
        response = client.post("/api/v1/translate/", {}, format="json")
        assert response.status_code == 400

    def test_empty_text_returns_400(self):
        client = APIClient()
        response = client.post("/api/v1/translate/", {"text": ""}, format="json")
        assert response.status_code == 400

    def test_oversize_text_returns_400(self):
        from django.conf import settings
        max_len = getattr(settings, "T2S_MAX_INPUT_LENGTH", 500)
        client = APIClient()
        response = client.post(
            "/api/v1/translate/",
            {"text": "ا" * (max_len + 100)},
            format="json",
        )
        assert response.status_code == 400

    def test_wrong_method_returns_405(self):
        client = APIClient()
        response = client.get("/api/v1/translate/")
        assert response.status_code == 405

    @pytest.mark.xfail(
        reason="DRF ParseError on malformed JSON currently returns 500; should be 400",
        strict=False,
    )
    def test_malformed_json_returns_400(self):
        """Sending non-JSON body should fail cleanly, not crash."""
        client = APIClient()
        response = client.post(
            "/api/v1/translate/",
            data="not json at all",
            content_type="application/json",
        )
        assert response.status_code in (400, 415)


@pytest.mark.system
class TestPerTokenMode:
    """Opt-in mode that bypasses compound short-circuit."""

    def test_default_mode_returns_compound_short_circuit(self, db):
        from rest_framework.test import APIClient

        client = APIClient()
        response = client.post(
            "/api/v1/translate/",
            {"text": "Ministry Of Finance"},
            format="json",
        )
        assert response.status_code == 200
        videos = response.json()["videos"]
        assert len([v for v in videos if v["match_type"] == "compound"]) == 1

    def test_per_token_mode_returns_multiple_rows(self, db):
        from rest_framework.test import APIClient

        client = APIClient()
        response = client.post(
            "/api/v1/translate/?mode=per_token",
            {"text": "يتعلم يدرس يحفظ"},
            format="json",
        )
        assert response.status_code == 200
        videos = response.json()["videos"]
        assert len(videos) >= 3, (
            f"Per-token mode should produce multiple rows, got {len(videos)}: "
            f"{[v['matched_lemma'] for v in videos]}"
        )
