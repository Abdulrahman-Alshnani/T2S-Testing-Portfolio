"""
Diagnostic: per-stage timing breakdown from live translate API responses.

Run with Django on http://127.0.0.1:8000. Read-only.
"""

from __future__ import annotations

import json
import statistics
import time
from typing import Any

import requests

API_URL = "http://127.0.0.1:8000/api/v1/translate/"
WARMUP_URL = "http://127.0.0.1:8000/api/v1/health/warmup/"

DIAGNOSTIC_INPUTS = [
    ("يكتب", "single-word (bug input)"),
    ("يأكل", "single-word verb"),
    ("هو", "single-word pronoun"),
    ("كرة السلة", "two-word compound"),
    ("أنا يكتب", "two-word sentence"),
    ("الولد يكتب", "sentence with article"),
    ("أنا يشاهد كرة السلة", "sentence with compound"),
    ("زوكربيرغ", "OOV"),
    ("الولد يقرأ الكتاب", "three-word sentence"),
    ("يتعلم يدرس يحفظ", "three-word verbs"),
]


def warm_server() -> None:
    print("Warming the server...")
    response = requests.get(WARMUP_URL, timeout=120)
    response.raise_for_status()
    print(f"  Server warm: {response.json()}")
    print()


def run_one(text: str, label: str) -> dict[str, Any]:
    started = time.perf_counter()
    response = requests.post(API_URL, json={"text": text}, timeout=30)
    wall_clock_ms = (time.perf_counter() - started) * 1000
    response.raise_for_status()
    body = response.json()
    timings = body.get("metadata", {}).get("timing_ms", {})
    videos = body.get("videos", [])
    nlp_ms = timings.get("preprocessing") or timings.get("nlp")
    return {
        "input": text,
        "label": label,
        "wall_clock_ms": wall_clock_ms,
        "server_total_ms": timings.get("total"),
        "nlp_ms": nlp_ms,
        "embedding_ms": timings.get("embedding"),
        "database_ms": timings.get("database"),
        "video_count": len(videos),
        "match_types": [v.get("match_type") for v in videos],
        "matched_lemmas": [v.get("matched_lemma") for v in videos],
    }


def main() -> None:
    warm_server()

    print("Pass 1 (priming caches):")
    for text, label in DIAGNOSTIC_INPUTS:
        try:
            run_one(text, label)
        except Exception as exc:
            print(f"  WARN: {text!r}: {exc}")
    print()

    print("Pass 2 (measurement):")
    print("=" * 110)
    print(
        f"{'Input':<35} {'Label':<25} {'Wall':>7} {'Total':>7} "
        f"{'NLP':>7} {'Embed':>7} {'DB':>7} {'Match types'}"
    )
    print("=" * 110)

    results = []
    for text, label in DIAGNOSTIC_INPUTS:
        try:
            result = run_one(text, label)
            results.append(result)
            print(
                f"{text:<35} {label:<25} "
                f"{result['wall_clock_ms']:>6.0f}ms "
                f"{result['server_total_ms'] or 0:>6.0f}ms "
                f"{result['nlp_ms'] or 0:>6.0f}ms "
                f"{result['embedding_ms'] or 0:>6.0f}ms "
                f"{result['database_ms'] or 0:>6.0f}ms "
                f"{result['match_types']}"
            )
        except Exception as exc:
            print(f"  ERROR: {text!r}: {exc}")
    print("=" * 110)

    wall_clocks = [r["wall_clock_ms"] for r in results]
    nlp_times = [r["nlp_ms"] or 0 for r in results]
    embed_times = [r["embedding_ms"] or 0 for r in results]
    db_times = [r["database_ms"] or 0 for r in results]

    if wall_clocks:
        print()
        print(f"Summary (n={len(results)}):")
        print(f"  Wall-clock median:   {statistics.median(wall_clocks):.0f}ms")
        p95_idx = max(0, int(len(wall_clocks) * 0.95) - 1)
        print(f"  Wall-clock P95:      {sorted(wall_clocks)[p95_idx]:.0f}ms")
        print(f"  NLP median:          {statistics.median(nlp_times):.0f}ms")
        print(f"  Embedding median:    {statistics.median(embed_times):.0f}ms")
        print(f"  Database median:     {statistics.median(db_times):.0f}ms")

    output = {
        "wall_clock_median_ms": statistics.median(wall_clocks) if wall_clocks else 0,
        "wall_clock_p95_ms": sorted(wall_clocks)[p95_idx] if wall_clocks else 0,
        "nlp_median_ms": statistics.median(nlp_times) if nlp_times else 0,
        "embedding_median_ms": statistics.median(embed_times) if embed_times else 0,
        "database_median_ms": statistics.median(db_times) if db_times else 0,
        "raw_results": results,
    }
    out_path = "scripts/diagnostic_pipeline_timing.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print()
    print(f"Detailed results saved to {out_path}")


if __name__ == "__main__":
    main()
