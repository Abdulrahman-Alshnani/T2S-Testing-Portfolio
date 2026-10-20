"""
Single-request latency benchmark against the 3000ms end-to-end budget.

Prints median and P95 values in pytest output for milestone demonstrations.
"""

import statistics
import time

import pytest
from rest_framework.test import APIClient

SAMPLE_SIZE = 20
P95_LATENCY_BUDGET_MS = 3000


@pytest.mark.performance
@pytest.mark.critical
@pytest.mark.slow
class TestSingleRequestLatency:
    """Measures single-request latency with real AraBERT inference."""

    def test_single_request_within_budget(self, seeded_lexicon, real_embedding_service):
        client = APIClient()
        client.post("/api/v1/translate/", data={"text": "كتب"}, format="json")

        samples = []
        for _ in range(SAMPLE_SIZE):
            start = time.perf_counter()
            response = client.post(
                "/api/v1/translate/",
                data={"text": "كتب"},
                format="json",
            )
            elapsed_ms = (time.perf_counter() - start) * 1000
            assert response.status_code == 200
            samples.append(elapsed_ms)

        median = statistics.median(samples)
        p95 = sorted(samples)[int(len(samples) * 0.95)]

        print(f"\n  Single-request latency (n={SAMPLE_SIZE}):")
        print(f"    Median: {median:.1f}ms")
        print(f"    P95:    {p95:.1f}ms")
        print(f"    Min:    {min(samples):.1f}ms")
        print(f"    Max:    {max(samples):.1f}ms")

        assert p95 < P95_LATENCY_BUDGET_MS

    def test_stage_breakdown_is_reasonable(self, seeded_lexicon, real_embedding_service):
        client = APIClient()
        client.post("/api/v1/translate/", data={"text": "كتب"}, format="json")
        response = client.post(
            "/api/v1/translate/",
            data={"text": "كتب"},
            format="json",
        )
        timing = response.json()["metadata"]["timing_ms"]

        print("\n  Stage breakdown:")
        for stage, milliseconds in timing.items():
            print(f"    {stage}: {milliseconds:.1f}ms")

        assert timing["preprocessing"] < 500
        assert timing["embedding"] < 1000
        assert timing["database"] < 500
        assert timing["total"] < P95_LATENCY_BUDGET_MS
