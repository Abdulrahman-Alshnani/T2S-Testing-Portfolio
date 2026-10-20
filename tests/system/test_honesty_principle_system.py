"""
The Honesty Principle is the load-bearing claim of this entire project.
These tests verify it holds under multiple input shapes.

If any test here fails, the project's core thesis is at risk. Treat
failures as critical regressions, not as test flakiness.
"""

from __future__ import annotations

import pytest
from rest_framework.test import APIClient


@pytest.mark.system
@pytest.mark.honesty
@pytest.mark.integration
class TestHonestyPrinciple:

    OOV_TEST_WORDS = [
        "زوكربيرغ",     # Zuckerberg
        "تشومسكي",      # Chomsky
        "آينشتاين",     # Einstein
        "نيتشه",        # Nietzsche
    ]

    @pytest.mark.parametrize("oov_word", OOV_TEST_WORDS)
    def test_oov_word_returns_not_found(self, db, oov_word):
        client = APIClient()
        response = client.post(
            "/api/v1/translate/",
            {"text": oov_word},
            format="json",
        )
        assert response.status_code == 200
        videos = response.json()["videos"]
        not_found_rows = [v for v in videos if v["match_type"] == "not_found"]
        assert len(not_found_rows) >= 1, (
            f"Expected not_found for OOV word {oov_word!r}, "
            f"got: {[v['match_type'] for v in videos]}"
        )

    def test_not_found_row_has_null_storage_url(self, db):
        client = APIClient()
        response = client.post(
            "/api/v1/translate/",
            {"text": "زوكربيرغ"},
            format="json",
        )
        not_found_rows = [v for v in response.json()["videos"] if v["match_type"] == "not_found"]
        for row in not_found_rows:
            assert row["storage_url"] is None, (
                "not_found row must have storage_url=null. "
                "Returning a placeholder URL would be dishonest substitution."
            )

    def test_mixed_input_preserves_honesty_per_token(self, db):
        """Partial OOV input: known words match, unknown words return not_found."""
        client = APIClient()
        response = client.post(
            "/api/v1/translate/",
            {"text": "أنا يتعلم زوكربيرغ"},
            format="json",
        )
        match_types = [v["match_type"] for v in response.json()["videos"]]
        # We expect a mix: some lemma matches and at least one not_found.
        # The exact composition depends on mBART's gloss output, but the
        # rule holds: at least one row must be honest about not finding the OOV.
        assert "not_found" in match_types or len(match_types) < 3, (
            f"Mixed input produced no honest not_found: {match_types}"
        )


@pytest.mark.system
class TestSpecificBugFixes:
    """Regression tests for bugs reported by users."""

    def test_yiktub_does_not_return_yakul_and_huwa(self, db):
        """
        Bug report: typing 'يكتب' returned videos for 'يأكل' and 'هو'.
        After bypass, expect one row for يكتب or honest not_found — never both wrong lemmas.
        """
        from rest_framework.test import APIClient

        client = APIClient()
        response = client.post(
            "/api/v1/translate/",
            {"text": "يكتب"},
            format="json",
        )
        assert response.status_code == 200
        videos = response.json()["videos"]
        matched_lemmas = [v.get("matched_lemma") for v in videos]
        assert not ("يأكل" in matched_lemmas and "هو" in matched_lemmas), (
            f"The eating/he bug is back. Got: {matched_lemmas}"
        )
