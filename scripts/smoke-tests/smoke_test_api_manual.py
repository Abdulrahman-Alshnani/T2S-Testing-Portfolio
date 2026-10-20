"""
Manual HTTP smoke test script for T2S Translation API.

Run directly with `python scripts/smoke-tests/smoke_test_api_manual.py`
to verify live backend response, CORS headers, and payload structure.
Not collected by pytest.
"""

from __future__ import annotations

import json
import os
import time

import requests

URL = os.environ.get("T2S_API_URL", "http://localhost:8000/api/v1/translate/")

# Sample test text containing compound phrases and words requiring semantic resolution
payload = {
    "text": "السلام عليكم ورحمة الله وبركاته كرة السلة"
}

# Emulate Chrome extension origin headers
headers = {
    "Content-Type": "application/json",
    "Origin": "chrome-extension://abcdefghijklmnopqrstuvwxyz"
}

print("Sending smoke test request to Translation API...")
start_time = time.time()

try:
    response = requests.post(URL, data=json.dumps(payload), headers=headers, timeout=30)
    execution_time = time.time() - start_time

    print("\n" + "=" * 50)
    print(f"Status Code: {response.status_code}")
    print(f"Total Response Time: {execution_time:.3f}s")
    print("=" * 50)

    # CORS header verification
    cors_header = response.headers.get("Access-Control-Allow-Origin")
    print(f"Access-Control-Allow-Origin: {cors_header}")
    if cors_header:
        print("PASS: CORS header received successfully.")
    else:
        print("FAIL: Server did not return Access-Control-Allow-Origin header.")

    print("\nResponse Payload:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))

except requests.exceptions.ConnectionError:
    print(f"\nConnection Error: Could not connect to {URL}. Ensure Django server is running.")
except Exception as exc:
    print(f"\nUnexpected error during smoke test: {exc}")
