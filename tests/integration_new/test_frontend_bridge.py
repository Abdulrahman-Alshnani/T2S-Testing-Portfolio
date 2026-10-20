"""
Verify the API surface that P3's React app (via api-bridge.js) consumes.

These tests do not execute JavaScript. They verify the API responds with
data the bridge can parse, in the shape the bridge expects.

The bridge fetches videos.json from dist/, then POSTs each Arabic key to
/api/v1/translate/. It expects a videos[] array with storage_url and
match_type fields. We verify those fields exist and have the right shapes.
"""

from __future__ import annotations

import pytest
from rest_framework.test import APIClient


@pytest.mark.integration
@pytest.mark.system
class TestFrontendBridgeContract:

    def test_response_has_videos_array(self, db):
        client = APIClient()
        response = client.post(
            "/api/v1/translate/",
            {"text": "مرحبا"},
            format="json",
        )
        body = response.json()
        assert "videos" in body
        assert isinstance(body["videos"], list)

    def test_each_video_has_required_bridge_fields(self, db):
        """The bridge reads: storage_url, match_type, matched_lemma."""
        client = APIClient()
        response = client.post(
            "/api/v1/translate/",
            {"text": "كرة السلة"},
            format="json",
        )
        for video in response.json()["videos"]:
            assert "storage_url" in video
            assert "match_type" in video
            assert "matched_lemma" in video

    def test_not_found_video_has_null_storage_url_for_bridge(self, db):
        """
        The bridge omits not_found rows from its mapping. For that to work,
        not_found rows must report storage_url=null so the bridge can detect
        them with a simple truthy check.
        """
        client = APIClient()
        response = client.post(
            "/api/v1/translate/",
            {"text": "زوكربيرغ"},
            format="json",
        )
        for video in response.json()["videos"]:
            if video["match_type"] == "not_found":
                assert video["storage_url"] is None


@pytest.mark.integration
class TestCORSConfiguration:

    def test_options_request_includes_cors_headers(self):
        """Preflight OPTIONS must include Access-Control-Allow-Origin."""
        client = APIClient()
        response = client.options(
            "/api/v1/translate/",
            HTTP_ORIGIN="http://127.0.0.1:5500",
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST",
        )
        # Either 200 or 204 is acceptable for OPTIONS.
        assert response.status_code in (200, 204)
        # The bridge runs from 127.0.0.1:5500, so that origin must be allowed.
        assert response.headers.get("Access-Control-Allow-Origin") is not None
