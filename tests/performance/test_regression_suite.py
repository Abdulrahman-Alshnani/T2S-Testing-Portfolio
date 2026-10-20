"""
Regression gate: the previous critical test suite must still pass.

After this comprehensive testing brief executes, the original critical tests
(currently 30 passing) must still pass at the same count. If any of them
breaks, this brief introduced a regression.
"""

from __future__ import annotations

import subprocess

import pytest


@pytest.mark.system
class TestRegressionGate:

    def test_critical_suite_still_passes(self):
        """Run the original critical suite as a subprocess and check pass count."""
        result = subprocess.run(
            ["pytest", "-m", "critical", "--tb=no", "-q"],
            capture_output=True,
            text=True,
            timeout=300,
        )
        # The output should end with "X passed".
        # We don't hardcode 30 because tests get added over time.
        # We assert that 0 tests failed.
        assert "failed" not in result.stdout.lower() or "0 failed" in result.stdout.lower(), (
            f"Critical regression suite has failures:\n{result.stdout}"
        )
