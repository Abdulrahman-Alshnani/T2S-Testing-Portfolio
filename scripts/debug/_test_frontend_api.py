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

ORIGIN = "http://127.0.0.1:5500"
API = "http://127.0.0.1:8000/api/v1/translate/"
headers = {"Origin": ORIGIN, "Content-Type": "application/json"}

# Preflight
opt = requests.options(
    API,
    headers={
        "Origin": ORIGIN,
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type",
    },
    timeout=30,
)
print("OPTIONS", opt.status_code, opt.headers.get("access-control-allow-origin"))

for text in ["كرة السلة", "كتب", "مرحبا"]:
    r = requests.post(API, json={"text": text}, headers=headers, timeout=120)
    playable = 0
    if r.ok:
        videos = r.json().get("videos", [])
        playable = sum(1 for v in videos if v.get("storage_url"))
    print(
        repr(text),
        "->",
        r.status_code,
        "ACAO:",
        r.headers.get("access-control-allow-origin"),
        "playable:",
        playable,
    )
