"""
Verify the singleton model pattern survives concurrent requests.

If multiple threads try to load the model simultaneously, the singleton
might double-load (OOM) or the second loader might get a half-initialized
reference. Both are subtle bugs that only show up under load.
"""

from __future__ import annotations

import threading
import time

import pytest
from rest_framework.test import APIClient


@pytest.mark.system
@pytest.mark.slow
class TestConcurrentRequests:

    def test_ten_simultaneous_requests_all_succeed(self, db):
        client = APIClient()
        results = []
        errors = []
        threads = []

        def worker(idx):
            try:
                response = client.post(
                    "/api/v1/translate/",
                    {"text": "كرة السلة"},
                    format="json",
                )
                results.append((idx, response.status_code))
            except Exception as exc:
                errors.append((idx, exc))

        for i in range(10):
            t = threading.Thread(target=worker, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join(timeout=30)

        # All threads should have completed.
        assert len(results) == 10, f"Got {len(results)}/10 results; errors: {errors}"
        # All responses should be 200.
        for idx, status_code in results:
            assert status_code == 200, f"Thread {idx} got status {status_code}"
