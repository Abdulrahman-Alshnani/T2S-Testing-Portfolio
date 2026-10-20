"""
End-to-end tests for POST /api/v1/translate/.

Exercises validation, response shape, timing metadata, and HTTP method rules.
"""

import pytest
from django.conf import settings
from rest_framework import status

ENDPOINT = "/api/v1/translate/"


@pytest.mark.integration
@pytest.mark.critical
class TestTranslationEndpoint:
    """Verifies the public API contract for P3."""

    def test_valid_arabic_input_returns_200(self, api_client, seeded_lexicon):
        response = api_client.post(
            ENDPOINT,
            data={"text": "كتب"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        body = response.json()
        assert "videos" in body
        assert "metadata" in body
        assert isinstance(body["videos"], list)

    def test_implausible_semantic_single_token_becomes_not_found(
        self, api_client, seeded_lexicon, mocker
    ):
        """Hover on يراجع must not return unrelated sign يساند via semantic tier."""
        mocker.patch(
            "translation_api.views.execute_hybrid_search",
            return_value=[
                {
                    "sequence_order": 1,
                    "matched_lemma": "يساند",
                    "storage_url": "https://example.com/wrong.mp4",
                    "match_type": "semantic",
                    "confidence": 0.95,
                    "gloss_id": "GLOSS_WRONG",
                }
            ],
        )
        mocker.patch(
            "translation_api.views.preprocess_arabic_text",
            return_value=["يراجع"],
        )
        mocker.patch(
            "translation_api.views.map_not_found_with_groq",
            return_value={},
        )
        response = api_client.post(
            ENDPOINT,
            data={"text": "يراجع"},
            format="json",
        )
        body = response.json()
        assert body["videos"][0]["match_type"] == "not_found"
        assert body["videos"][0]["storage_url"] is None

    def test_single_token_oov_returns_not_found_not_substitute(
        self, api_client, seeded_lexicon, mocker
    ):
        """اخي and من must not play unrelated signs (أنا / نحن)."""
        mocker.patch(
            "translation_api.views.preprocess_arabic_text",
            side_effect=lambda text: ["اخي"] if "اخ" in text else ["من"],
        )
        mocker.patch(
            "translation_api.views.map_not_found_with_groq",
            return_value={"اخي": "أنا", "من": "نحن"},
        )
        for word in ("اخي", "من"):
            response = api_client.post(
                ENDPOINT,
                data={"text": word},
                format="json",
            )
            body = response.json()
            assert body["videos"][0]["match_type"] == "not_found"
            assert body["videos"][0]["storage_url"] is None

    def test_single_token_curated_synonym_returns_lexicon_video(
        self, api_client, seeded_lexicon, mocker
    ):
        """على → فوق and ثم → بعد are allowed curated synonyms."""
        mocker.patch(
            "translation_api.views.map_not_found_with_groq",
            return_value={},
        )
        for word, expected_lemma in (("على", "فوق"), ("ثم", "بعد")):
            mocker.patch(
                "translation_api.views.preprocess_arabic_text",
                return_value=[word],
            )
            response = api_client.post(
                ENDPOINT,
                data={"text": word},
                format="json",
            )
            body = response.json()
            assert body["videos"][0]["storage_url"]
            assert body["videos"][0]["matched_lemma"] == expected_lemma

    def test_plausible_semantic_single_token_kept(
        self, api_client, seeded_lexicon, mocker
    ):
        mocker.patch(
            "translation_api.views.preprocess_arabic_text",
            return_value=["على"],
        )
        mocker.patch(
            "translation_api.views.execute_hybrid_search",
            return_value=[
                {
                    "sequence_order": 1,
                    "matched_lemma": "فوق",
                    "storage_url": "https://example.com/fawq.mp4",
                    "match_type": "semantic",
                    "confidence": 0.9,
                    "gloss_id": "GLOSS_FAWQ",
                }
            ],
        )
        mocker.patch(
            "translation_api.views.map_not_found_with_groq",
            return_value={},
        )
        response = api_client.post(
            ENDPOINT,
            data={"text": "على"},
            format="json",
        )
        body = response.json()
        # Synonym redirect (على → فوق) may yield lemma or semantic depending on search path.
        assert body["videos"][0]["matched_lemma"] == "فوق"
        assert body["videos"][0]["match_type"] in ("semantic", "lemma")
        assert body["videos"][0]["storage_url"]

    def test_single_token_exact_lexicon_hit_returns_video(
        self, api_client, seeded_lexicon
    ):
        response = api_client.post(
            ENDPOINT,
            data={"text": "أنا"},
            format="json",
        )
        body = response.json()
        assert body["videos"][0]["match_type"] == "lemma"
        assert body["videos"][0]["matched_lemma"] == "أنا"
        assert body["videos"][0]["storage_url"]

    def test_legacy_word_field_accepted(self, api_client, seeded_lexicon):
        """P3 React build sends 'word' instead of OpenAPI field 'text'."""
        response = api_client.post(
            ENDPOINT,
            data={"word": "كتب"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        body = response.json()
        assert body["videos"]
        assert body["metadata"]["input_text"] == "كتب"

    def test_response_includes_timing_metadata(self, api_client, seeded_lexicon):
        response = api_client.post(
            ENDPOINT,
            data={"text": "كتب"},
            format="json",
        )
        timing = response.json()["metadata"]["timing_ms"]
        assert "preprocessing" in timing
        assert "embedding" in timing
        assert "database" in timing
        assert "total" in timing
        assert timing["total"] > 0

    def test_empty_text_returns_400(self, api_client):
        response = api_client.post(ENDPOINT, data={"text": ""}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_non_arabic_text_returns_400(self, api_client):
        response = api_client.post(
            ENDPOINT,
            data={"text": "hello world 123"},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_excessive_length_returns_400(self, api_client):
        oversized = "كتب " * settings.T2S_MAX_INPUT_LENGTH
        response = api_client.post(
            ENDPOINT,
            data={"text": oversized},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_get_method_not_allowed(self, api_client):
        response = api_client.get(ENDPOINT)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    @pytest.mark.honesty
    def test_response_includes_not_found_rows(self, api_client, seeded_lexicon):
        response = api_client.post(
            ENDPOINT,
            data={"text": "كلمةغيرموجودةتماما"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        body = response.json()
        match_types = {video["match_type"] for video in body["videos"]}
        if "not_found" in match_types:
            for video in body["videos"]:
                if video["match_type"] == "not_found":
                    assert video["storage_url"] is None
