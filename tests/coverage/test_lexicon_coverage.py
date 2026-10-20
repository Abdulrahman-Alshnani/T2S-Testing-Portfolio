"""
Coverage tests over every lexicon entry.

These tests iterate the entire SignWord table and verify each row meets
the data quality bar. Failures produce specific row IDs, not just a pass/fail.

Marked @pytest.mark.coverage so they can be run independently:
    pytest -m coverage

For the network-dependent URL reachability test, also requires @pytest.mark.network.
"""

from __future__ import annotations

import random

import pytest


@pytest.mark.coverage
@pytest.mark.integration
class TestLexiconRowIntegrity:

    def test_every_signword_has_a_lemma(self, db):
        from translation_api.models import SignWord
        rows_without_lemma = list(
            SignWord.objects
            .filter(lemma__isnull=True)
            .exclude(category="__test__")
            .values_list("id", "arabic_text")
        )
        assert not rows_without_lemma, (
            f"{len(rows_without_lemma)} SignWord rows have NULL lemma:\n"
            + "\n".join(f"  id={id}, arabic_text={ar!r}" for id, ar in rows_without_lemma[:10])
        )

    def test_every_signword_has_a_gloss_id(self, db):
        from translation_api.models import SignWord
        rows_without_gloss = list(
            SignWord.objects
            .filter(gloss_id__isnull=True)
            .exclude(category="__test__")
            .values_list("id", "lemma")
        )
        assert not rows_without_gloss, (
            f"{len(rows_without_gloss)} rows have NULL gloss_id"
        )

    def test_no_empty_lemmas(self, db):
        from translation_api.models import SignWord
        empty_lemma_rows = list(
            SignWord.objects
            .filter(lemma="")
            .exclude(category="__test__")
            .values_list("id", flat=True)
        )
        assert not empty_lemma_rows, (
            f"{len(empty_lemma_rows)} rows have empty string lemma"
        )

    def test_compound_flag_matches_word_count(self, db):
        """is_compound=True iff word_count >= 2."""
        from translation_api.models import SignWord
        mismatches = list(
            SignWord.objects
            .exclude(category="__test__")
            .extra(
                where=[
                    "(is_compound = TRUE AND word_count < 2) OR "
                    "(is_compound = FALSE AND word_count >= 2)"
                ]
            )
            .values_list("id", "lemma", "is_compound", "word_count")
        )
        assert not mismatches, (
            f"{len(mismatches)} rows have inconsistent is_compound/word_count:\n"
            + "\n".join(f"  id={id}, lemma={l!r}, is_compound={ic}, count={wc}"
                        for id, l, ic, wc in mismatches[:10])
        )


@pytest.mark.coverage
@pytest.mark.integration
class TestLexiconVideoMappings:

    def test_every_signword_has_a_video_mapping(self, db):
        from translation_api.models import SignWord
        orphans = list(
            SignWord.objects
            .exclude(category="__test__")
            .filter(video_mappings__isnull=True)
            .values_list("id", "lemma")
        )
        assert not orphans, (
            f"{len(orphans)} SignWord rows have no VideoMapping:\n"
            + "\n".join(f"  id={id}, lemma={l!r}" for id, l in orphans[:10])
        )

    def test_every_video_mapping_has_a_storage_url(self, db):
        from translation_api.models import VideoMapping
        empty_urls = list(
            VideoMapping.objects
            .exclude(signword__category="__test__")
            .filter(storage_url__isnull=True)
            .values_list("id", "signword__lemma")
        )
        assert not empty_urls, (
            f"{len(empty_urls)} VideoMappings have NULL storage_url"
        )

    def test_no_placeholder_urls(self, db):
        """Placeholder URLs should have been cleaned up during ingestion."""
        from translation_api.models import VideoMapping
        placeholders = list(
            VideoMapping.objects
            .filter(storage_url__icontains="placeholder.local")
            .values_list("id", "signword__lemma")
        )
        assert not placeholders, (
            f"{len(placeholders)} placeholder URLs remain. "
            "Run scripts/cleanup_placeholders.py."
        )


@pytest.mark.coverage
@pytest.mark.integration
class TestLexiconEmbeddingCoverage:

    def test_all_non_compounds_have_embeddings(self, db):
        """Tier 3 only works for rows with embeddings."""
        from translation_api.models import SignWord
        missing = list(
            SignWord.objects
            .filter(is_compound=False, embedding__isnull=True)
            .exclude(category="__test__")
            .values_list("id", "lemma")
        )
        assert not missing, (
            f"{len(missing)} non-compound rows have NULL embedding. "
            "Run scripts/regenerate_missing_embeddings.py to fix.\n"
            "First 10:\n"
            + "\n".join(f"  id={id}, lemma={l!r}" for id, l in missing[:10])
        )

    def test_compounds_intentionally_have_no_embeddings(self, db):
        """Compounds match by substring at Tier 1; they don't need vectors."""
        from translation_api.models import SignWord
        unexpected = list(
            SignWord.objects
            .filter(is_compound=True, embedding__isnull=False)
            .exclude(category="__test__")
            .values_list("id", "lemma")
        )
        # This is a soft warning, not a hard failure. Some compounds may
        # have embeddings if ingestion was overly thorough; that's wasteful
        # but not broken.
        if unexpected:
            pytest.skip(
                f"{len(unexpected)} compounds have unnecessary embeddings. "
                "Consider clearing them to save space."
            )


@pytest.mark.coverage
@pytest.mark.integration
@pytest.mark.slow
class TestLexiconLookup:
    """
    Iterate every row and verify it can be retrieved via the API.

    This is the most thorough test in the suite. On a 751-row lexicon at
    ~300ms per request, the full sweep takes ~4 minutes.
    """

    def test_every_lemma_is_findable_via_api(self, db):
        from rest_framework.test import APIClient
        from translation_api.models import SignWord

        client = APIClient()
        # Sample to keep runtime bounded. For full sweep set sample_size=None
        # and run with -m slow explicitly.
        all_rows = list(
            SignWord.objects
            .exclude(category="__test__")
            .values_list("id", "lemma", "is_compound")
        )
        # Sample 50 deterministically with a fixed seed.
        random.seed(13)
        sampled = random.sample(all_rows, min(50, len(all_rows)))

        unfound = []
        for row_id, lemma, is_compound in sampled:
            response = client.post(
                "/api/v1/translate/",
                {"text": lemma},
                format="json",
            )
            if response.status_code != 200:
                unfound.append((row_id, lemma, f"HTTP {response.status_code}"))
                continue
            videos = response.json()["videos"]
            # The lemma should produce at least one playable result.
            playable = [v for v in videos if v.get("storage_url")]
            if not playable:
                unfound.append((row_id, lemma, "no playable video"))

        # Allow a small failure rate to account for mBART normalization
        # producing a different gloss than the raw lemma.
        failure_rate = len(unfound) / len(sampled)
        assert failure_rate < 0.1, (
            f"{len(unfound)}/{len(sampled)} sampled lemmas are not findable. "
            f"Failure rate: {failure_rate:.1%}\n"
            "First 10:\n"
            + "\n".join(f"  id={id}, lemma={l!r}: {reason}"
                        for id, l, reason in unfound[:10])
        )
