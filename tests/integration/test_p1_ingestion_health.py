"""
Post-ingestion health checks for the P1 lexicon delivery.

Verifies row counts, compound flag distribution, and absence of placeholder URLs.
Expected counts come from data/lexicon_counts.json (written by post_upload_sync.py).
Falls back to 327 / 58 when that file is absent (legacy MVP lexicon).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

_COUNTS_FILE = (
    Path(__file__).resolve().parent.parent.parent / "data" / "lexicon_counts.json"
)


def _expected_counts() -> dict[str, int]:
    if _COUNTS_FILE.is_file():
        data = json.loads(_COUNTS_FILE.read_text(encoding="utf-8"))
        return {
            "total": int(data["total"]),
            "compounds": int(data["compounds"]),
        }
    return {"total": 327, "compounds": 58}


@pytest.mark.integration
class TestPostIngestionHealth:
    """Confirms the database state after P1 ingestion."""

    def test_lexicon_row_count_matches_manifest(self, db):
        from translation_api.models import SignWord

        expected = _expected_counts()["total"]
        production_count = SignWord.objects.exclude(category="__test__").count()
        assert production_count == expected, (
            f"Expected exactly {expected} lexicon rows after ingestion, "
            f"found {production_count}. Run scripts/post_upload_sync.py and commit "
            f"data/lexicon_counts.json, or refresh counts after a larger upload."
        )

    def test_compound_count_matches_manifest(self, db):
        from translation_api.models import SignWord

        expected = _expected_counts()["compounds"]
        compound_count = (
            SignWord.objects.filter(is_compound=True)
            .exclude(category="__test__")
            .count()
        )
        assert compound_count == expected, (
            f"Expected {expected} compound entries, found {compound_count}."
        )

    def test_no_placeholder_urls_remain(self, db):
        from translation_api.models import VideoMapping

        placeholders = VideoMapping.objects.filter(
            storage_url__icontains="placeholder.local"
        ).count()
        assert placeholders == 0, (
            f"Found {placeholders} VideoMapping row(s) with placeholder URLs. "
            "Run scripts/cleanup_placeholders.py."
        )

    def test_non_compound_entries_have_embeddings(self, db):
        from translation_api.models import SignWord

        missing_embeddings = (
            SignWord.objects.filter(is_compound=False, embedding__isnull=True)
            .exclude(category="__test__")
            .count()
        )
        assert missing_embeddings == 0, (
            f"{missing_embeddings} non-compound entries lack embeddings. "
            "Run scripts/seed_embeddings.py."
        )

    def test_every_signword_has_video_mapping(self, db):
        from translation_api.models import SignWord

        orphans = (
            SignWord.objects.exclude(category="__test__")
            .filter(video_mappings__isnull=True)
            .count()
        )
        assert orphans == 0, (
            f"{orphans} SignWord rows have no VideoMapping. "
            "Re-run scripts/seed_lexicon_from_json.py."
        )
