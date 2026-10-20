# Diagnostics & Troubleshooting Tools

This directory contains standalone diagnostic utilities used by the QA and engineering team to profile, trace, and diagnose the translation pipeline.

## Script Catalog

| Script | Purpose |
|---|---|
| `diagnose_pipeline_timing.py` | Measures per-stage execution latency (validation, NLP, embedding, DB search, serialization) on a live or warm server. |
| `diagnose_mbart_outputs.py` | Analyzes mBART translation gloss outputs against known lexicon lemmas to detect and diagnose hallucination patterns. |
| `trace_translation.py` | End-to-end trace printing intermediate outputs across tokenization, embeddings, and hybrid SQL search for any input sentence. |
| `debug_word_match.py` | Inspects single-word hover queries and explains how the system resolves lemmas, synonyms, and similarity thresholds. |
| `validate_demo_article.py` | Batch validator that verifies every non-stopword token in the demo news article produces an accurate sign video clip. |
