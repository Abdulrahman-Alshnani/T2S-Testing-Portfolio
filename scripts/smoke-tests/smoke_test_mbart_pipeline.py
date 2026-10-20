"""
End-to-end smoke test for the post-integration pipeline.

Run with Django server running. Reports pass/fail per test case.
"""

from __future__ import annotations

import os
import sys
import time

import requests

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

API_URL = os.environ.get("T2S_API_URL", "http://127.0.0.1:8000/api/v1/translate/")
WARMUP_URL = API_URL.replace("/translate/", "/health/warmup/")

TEST_CASES = [
    {
        "input": "الولد يقرأ الكتاب",
        "expect_status": 200,
        "expect_at_least_one_match": True,
        "expect_honesty_pattern": False,
        "label": "simple sentence",
    },
    {
        "input": "كرة السلة",
        "expect_status": 200,
        "expect_at_least_one_match": True,
        "expect_honesty_pattern": False,
        "label": "known compound",
    },
    {
        "input": "زوكربيرغ",
        "expect_status": 200,
        "expect_at_least_one_match": False,
        "expect_honesty_pattern": True,
        "label": "OOV proper noun (honesty check)",
    },
]


def run() -> int:
    print("Warming up first...")
    warmup_response = requests.get(WARMUP_URL, timeout=120)
    print(f"  Warmup status: {warmup_response.status_code}")
    print(f"  Warmup body:   {warmup_response.json()}")
    print()

    failures = 0
    for case in TEST_CASES:
        label = case["label"]
        print(f"[{label}] input: {case['input']!r}")

        started = time.perf_counter()
        response = requests.post(
            API_URL,
            json={"text": case["input"]},
            timeout=120,
        )
        elapsed_ms = (time.perf_counter() - started) * 1000

        if response.status_code != case["expect_status"]:
            print(f"  FAIL: status {response.status_code} (expected {case['expect_status']})")
            failures += 1
            continue

        body = response.json()
        videos = body.get("videos", [])
        match_types = [v.get("match_type") for v in videos]
        print(f"  videos returned: {len(videos)}")
        print(f"  match_types:     {match_types}")
        print(f"  total latency:   {elapsed_ms:.0f}ms")
        print(f"  server timing:   {body.get('metadata', {}).get('timing_ms', {})}")

        playable = [v for v in videos if v.get("storage_url")]
        not_found_rows = [v for v in videos if v.get("match_type") == "not_found"]

        if case["expect_at_least_one_match"] and not playable:
            print("  FAIL: expected at least one playable result; got zero")
            failures += 1
            continue

        if case["expect_honesty_pattern"] and not not_found_rows:
            print("  FAIL: expected at least one not_found row; got zero")
            failures += 1
            continue

        print("  PASS")
        print()

    if failures:
        print(f"Smoke test: {failures} failure(s) out of {len(TEST_CASES)} cases")
        return 1
    print(f"Smoke test: all {len(TEST_CASES)} cases passed")
    return 0


if __name__ == "__main__":
    sys.exit(run())
