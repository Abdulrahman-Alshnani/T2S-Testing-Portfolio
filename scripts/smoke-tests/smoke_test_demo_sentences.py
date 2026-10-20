#!/usr/bin/env python
"""
Smoke test: hit the translation API with each curated demo sentence.

Prints a results table showing expected vs actual match_type for every sentence.
Exit code is non-zero if any verified sentence's first token returns the wrong match_type.

Run after seed_lexicon and seed_embeddings, with the Django server running.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

# Windows consoles may default to cp1252; UTF-8 is required for Arabic output.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEMO_FILE = PROJECT_ROOT / "data" / "demo_sentences.json"
API_URL = os.environ.get("T2S_API_URL", "http://localhost:8000/api/v1/translate/")
REQUEST_TIMEOUT_SECONDS = 15


def colorize(text: str, color_code: str) -> str:
    return f"\033[{color_code}m{text}\033[0m"


def status_label(passed: bool) -> str:
    return colorize("PASS", "32") if passed else colorize("FAIL", "31")


def compare_match_sequence(expected: list, actual_rows: list) -> bool:
    """Compare expected match_type sequence against the response rows."""
    if len(actual_rows) != len(expected):
        return False
    for expected_type, row in zip(expected, actual_rows):
        if row.get("match_type") != expected_type:
            return False
    return True


def run_smoke_test() -> int:
    with open(DEMO_FILE, encoding="utf-8") as demo_file:
        demo_data = json.load(demo_file)

    sentences = demo_data["demo_sentences"]
    print(f"Smoke testing {len(sentences)} demo sentences against {API_URL}")
    print("=" * 110)
    print(
        f"{'ID':<6} {'Arabic':<35} {'Expected sequence':<32} "
        f"{'Actual sequence':<28} {'Latency':<10} Status"
    )
    print("=" * 110)

    failures = 0
    total_latency_ms = 0.0
    samples = 0

    for sentence in sentences:
        sentence_id = sentence["id"]
        arabic = sentence["arabic_text"]
        expected_types = sentence["expected_match_types"]

        started_at = time.perf_counter()
        try:
            response = requests.post(
                API_URL,
                json={"text": arabic},
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
            elapsed_ms = (time.perf_counter() - started_at) * 1000
            total_latency_ms += elapsed_ms
            samples += 1

            if response.status_code != 200:
                actual_str = f"HTTP {response.status_code}"
                passed = False
            else:
                body = response.json()
                videos = body.get("videos", [])
                actual_types = [v.get("match_type", "?") for v in videos]
                actual_str = ",".join(actual_types) if actual_types else "empty"
                passed = compare_match_sequence(expected_types, videos)
        except requests.exceptions.RequestException as exc:
            actual_str = f"ERROR: {type(exc).__name__}"
            elapsed_ms = 0.0
            passed = False

        if not passed:
            failures += 1

        expected_str = ",".join(expected_types)
        print(
            f"{sentence_id:<6} {arabic:<35} {expected_str:<32} "
            f"{actual_str:<28} {elapsed_ms:>7.1f}ms {status_label(passed)}"
        )

    print("=" * 110)
    average_ms = total_latency_ms / samples if samples > 0 else 0.0
    print(
        f"Passed: {len(sentences) - failures}/{len(sentences)} | "
        f"Average latency: {average_ms:.1f}ms"
    )

    return 1 if failures > 0 else 0


if __name__ == "__main__":
    sys.exit(run_smoke_test())
