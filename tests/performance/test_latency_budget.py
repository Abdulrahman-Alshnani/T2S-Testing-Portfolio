"""
Verify the latency budget claimed in the project documentation.

Day 1 milestone report claimed P50 ~190ms, P95 ~421ms on a warm server.
These tests verify that promise still holds after mBART integration.

Note: mBART adds inference time. The new budget after integration is
expected to be higher. We adjust the thresholds accordingly but they are
still bounded.
"""

from __future__ import annotations

import time

import pytest
from rest_framework.test import APIClient


@pytest.mark.system
@pytest.mark.slow
@pytest.mark.requires_mbart
class TestLatencyBudget:

    def test_warm_p50_under_1500ms(self, db):
        """
        Median of 20 warm requests must be under 1.5 seconds.
        Pre-mBART this was 200ms; mBART beam search adds latency.
        """
        client = APIClient()
        # Warmup
        for _ in range(2):
            client.post("/api/v1/translate/", {"text": "تجربة"}, format="json")

        latencies = []
        for _ in range(20):
            response = client.post(
                "/api/v1/translate/",
                {"text": "كرة السلة"},
                format="json",
            )
            latencies.append(response.json()["metadata"]["timing_ms"]["total"])

        latencies.sort()
        p50 = latencies[10]
        assert p50 < 1500, f"P50 latency was {p50}ms; expected <1500ms"

    def test_warm_p95_under_3000ms(self, db):
        """P95 of 20 warm requests must be under 3 seconds."""
        client = APIClient()
        for _ in range(2):
            client.post("/api/v1/translate/", {"text": "تجربة"}, format="json")

        latencies = []
        for _ in range(20):
            response = client.post(
                "/api/v1/translate/",
                {"text": "كرة السلة"},
                format="json",
            )
            latencies.append(response.json()["metadata"]["timing_ms"]["total"])

        latencies.sort()
        p95 = latencies[18]  # 95th percentile of 20 = index 18
        assert p95 < 3000, f"P95 latency was {p95}ms; expected <3000ms"


@pytest.mark.system
@pytest.mark.slow
@pytest.mark.requires_mbart
class TestSustainedLoad:

    def test_100_consecutive_requests_no_degradation(self, db):
        """
        After 100 requests, the 100th request should still be fast.
        Degradation past 10x baseline suggests a memory leak or cache thrash.
        """
        client = APIClient()
        # Warmup.
        for _ in range(3):
            client.post("/api/v1/translate/", {"text": "تجربة"}, format="json")

        # First 10 to establish baseline.
        baseline_latencies = []
        for _ in range(10):
            response = client.post(
                "/api/v1/translate/",
                {"text": "كرة السلة"},
                format="json",
            )
            baseline_latencies.append(response.json()["metadata"]["timing_ms"]["total"])
        baseline_median = sorted(baseline_latencies)[5]

        # Next 90 to detect degradation.
        late_latencies = []
        for _ in range(90):
            response = client.post(
                "/api/v1/translate/",
                {"text": "كرة السلة"},
                format="json",
            )
            late_latencies.append(response.json()["metadata"]["timing_ms"]["total"])
        late_median = sorted(late_latencies)[45]

        # Late requests should not be 10x slower than early ones.
        assert late_median < baseline_median * 10, (
            f"Latency degraded: baseline median {baseline_median}ms, "
            f"late median {late_median}ms (>10x slowdown). "
            "Possible memory leak or singleton cache thrash."
        )
