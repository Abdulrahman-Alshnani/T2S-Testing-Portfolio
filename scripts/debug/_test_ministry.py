"""
AD-HOC DEBUG SCRIPT — not part of the maintained toolchain.

This script was written for a one-time investigation. It is kept for
reference only. Do not import it or run it as part of CI.
"""

import json
import sys

import requests

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

API = "http://127.0.0.1:8000/api/v1/translate/"
tests = [
    "Ministry of Finance",
    "financial ministry",
    "Ministry Of Finance",
    "وزارة المالية",
]
out = []
for t in tests:
    r = requests.post(API, json={"text": t}, timeout=120)
    row = {"input": t, "status": r.status_code}
    if r.ok:
        v = r.json().get("videos", [])
        row["videos"] = [
            {
                "match_type": x.get("match_type"),
                "lemma": x.get("matched_lemma"),
                "has_url": bool(x.get("storage_url")),
            }
            for x in v
        ]
    else:
        row["error"] = r.text[:200]
    out.append(row)

print(json.dumps(out, ensure_ascii=False, indent=2))
