"""Quick test: verify backend returns per-word videos for sentences."""
import requests

def test(text, use_per_token=False):
    url = "http://127.0.0.1:8000/api/v1/translate/"
    if use_per_token:
        url += "?mode=per_token"
    r = requests.post(url, json={"text": text}, timeout=120)
    d = r.json()
    v = d.get("videos", d if isinstance(d, list) else [])
    mode = "per_token" if use_per_token else "normal"
    print(f"[{mode}] '{text}' -> {len(v)} videos:")
    for i, vid in enumerate(v):
        lemma = vid.get("matched_lemma", "?")
        mt = vid.get("match_type", "?")
        has_url = bool(vid.get("storage_url"))
        print(f"  [{i}] {lemma} | {mt} | url={has_url}")
    print()

if __name__ == "__main__":
    test("أب أم أخ أخت جد", use_per_token=True)
    test("وزارة المالية", use_per_token=False)
    test("أب أم", use_per_token=False)
