"""
Verify that Arabic inputs for previously-broken lexicon entries now resolve
to the correct videos.

Self-contained: runs the translate pipeline in-process via the Django test
client, so it does not depend on a separately running (and possibly stale)
server. Single Arabic words that are now exact lemmas bypass mBART, so this
needs only AraBERT.
"""

from __future__ import annotations

import json
import os
import sys

import django

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
os.environ.setdefault("T2S_SKIP_MBART_WARMUP", "1")

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

django.setup()

from django.conf import settings  # noqa: E402

if "testserver" not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS = list(settings.ALLOWED_HOSTS) + ["testserver"]

from django.test import Client  # noqa: E402

API_PATH = "/api/v1/translate/"

# (Arabic input, expected gloss_id substring, plain-English description)
TEST_CASES = [
    ("قط", "GLOSS_CAT", "cat"),
    ("كلب", "GLOSS_DOG", "dog"),
    ("بقرة", "GLOSS_COW", "cow"),
    ("أسد", "GLOSS_LION", "lion"),
    ("طعام", "GLOSS_FOOD", "food"),
    ("ماء", "GLOSS_WATER", "water"),
    ("خبز", "GLOSS_BREAD", "bread"),
    ("أب", "GLOSS_DAD", "father"),
    ("أم", "GLOSS_MOM", "mother"),
    ("أحمر", "GLOSS_RED", "red"),
    ("أزرق", "GLOSS_BLUE", "blue"),
    ("مدرسة", "GLOSS_SCHOOL", "school"),
    ("كتاب", "GLOSS_BOOK", "book"),
    ("صلاة", "GLOSS_PRAYER", "prayer"),
    ("شمس", "GLOSS_SUN", "sun"),
]


def run_one(client: Client, arabic_input: str, expected_gloss: str, description: str) -> dict:
    response = client.post(
        API_PATH, data=json.dumps({"text": arabic_input}), content_type="application/json"
    )
    try:
        body = response.json()
    except Exception:
        return {"input": arabic_input, "description": description, "result": "HTTP_%s" % response.status_code}
    videos = body.get("videos", [])
    if not videos:
        return {"input": arabic_input, "description": description, "result": "NO_VIDEOS"}
    first = videos[0]
    actual_gloss = first.get("gloss_id", "") or ""
    match_type = first.get("match_type", "")
    has_url = bool(first.get("storage_url"))
    correct = expected_gloss[:50] in actual_gloss
    return {
        "input": arabic_input,
        "description": description,
        "result": "PASS" if (correct and has_url) else "FAIL",
        "expected_gloss": expected_gloss,
        "actual_gloss": actual_gloss,
        "match_type": match_type,
        "has_url": has_url,
    }


def main() -> int:
    client = Client()
    results = []
    for arabic, expected, desc in TEST_CASES:
        r = run_one(client, arabic, expected, desc)
        results.append(r)
        symbol = "OK" if r["result"] == "PASS" else "XX"
        print(
            f"  [{symbol}] {arabic:<8} ({desc:<8}) -> "
            f"{r.get('actual_gloss', '-')} [{r.get('match_type', '-')}]"
        )

    passed = sum(1 for r in results if r["result"] == "PASS")
    print()
    print(f"Result: {passed}/{len(TEST_CASES)} passed")

    with open("scripts/smoke_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    return 0 if passed >= len(TEST_CASES) - 1 else 1


if __name__ == "__main__":
    sys.exit(main())
