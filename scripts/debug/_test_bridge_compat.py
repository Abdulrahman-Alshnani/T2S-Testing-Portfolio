"""
AD-HOC DEBUG SCRIPT — not part of the maintained toolchain.

This script was written for a one-time investigation. It is kept for
reference only. Do not import it or run it as part of CI.
"""

"""Simulate legacy P3 parse vs api-bridge unwrap."""
import json
import sys

import requests

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

API = "http://127.0.0.1:8000/api/v1/translate/"
text = "ماء"
raw = requests.post(API, json={"word": text}, timeout=120).json()

# Legacy bundle: e[0]?.storage_url on full JSON body
legacy_url = None
if isinstance(raw, list) and raw:
    legacy_url = raw[0].get("storage_url")
elif isinstance(raw, dict):
    # Buggy: treat dict like array (always undefined in JS)
    try:
        legacy_url = raw[0].get("storage_url")  # type: ignore[index]
    except (KeyError, TypeError, AttributeError):
        legacy_url = None

# After bridge: body is videos array
bridged = raw.get("videos", raw) if isinstance(raw, dict) else raw
fixed_url = bridged[0].get("storage_url") if bridged else None
playable = next((v.get("storage_url") for v in bridged if v.get("storage_url")), None)

print("input:", text)
print("legacy_parse_url:", legacy_url)
print("bridge_parse_url:", fixed_url)
print("first_playable:", playable)
