# T2S Integration Notes (P1 and P3)

## For P1 (Data Pipeline)

### Lexicon delivery

Deliver a JSON array conforming to `contracts/lexicon_schema.json`. Required fields per entry:

- `lemma`, `arabic_text`, `gloss_id`, `video_filename`, `is_compound`, `word_count`

### Video files

Upload validated clips to the Supabase bucket `sign-videos`. The filename in JSON must match the object key exactly.

### Embedding generation (offline)

Use the same model as runtime: `aubmindlab/bert-base-arabertv02`. P2's `scripts/seed_embeddings.py` can populate vectors after lexicon import.

### Seed commands

```bash
python scripts/seed_compound_dictionary.py
python scripts/seed_lexicon_from_json.py path/to/lexicon.json
python scripts/seed_embeddings.py
```

### NLP replacement

Replace `translation_api/services/nlp_pipeline.py` with CAMeL Tools while preserving:

`preprocess_arabic_text(text: str) -> List[str]`

## For P3 (Chrome Extension)

### Endpoint

`POST http://localhost:8000/api/v1/translate/`

Request (canonical field is `text`; legacy React build may send `word` — backend accepts both):

```json
{"text": "السلام عليكم"}
```

Response envelope (do **not** treat the body as a top-level array):

```json
{
  "videos": [
    {
      "sequence_order": 1,
      "matched_lemma": "أنا",
      "storage_url": "https://...",
      "match_type": "lemma",
      "confidence": 1.0,
      "gloss_id": "GLOSS_ME"
    }
  ],
  "metadata": { "input_text": "...", "lemma_count": 1, "timing_ms": {} }
}
```

Use `response.videos[0].storage_url` for the first clip URL.

### match_type UI treatment

| match_type | Meaning | Recommended UI |
|------------|---------|----------------|
| `compound` | Full phrase matched | Play single clip at sequence_order 1 |
| `lemma` | Exact dictionary hit | Play clip with full confidence indicator |
| `semantic` | Vector fallback above 0.75 | Play clip with similarity badge |
| `not_found` | Honesty principle failure | Show explicit not-found card; do not substitute |

### Preloading

Use `metadata.timing_ms.total` and clip `duration_ms` when present to schedule preload of `videos[n+1]` while playing `videos[n]`.

### CORS

Development server allows `chrome-extension://*` and `http://localhost:<port>` / `127.0.0.1` via regex (`CORS_ALLOW_ALL_ORIGINS` is **false**). Restrict patterns in production deployment.
