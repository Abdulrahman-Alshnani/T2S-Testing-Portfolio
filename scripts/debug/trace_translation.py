"""
Diagnostic: prints the full pipeline trace for a single input.

Usage:
    python scripts/trace_translation.py "وزارة المالية"
"""

from __future__ import annotations

import os
import sys

import django

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
os.environ.setdefault("T2S_SKIP_MBART_WARMUP", "1")
django.setup()

from translation_api.services.embedding_service import get_embedding_service  # noqa: E402
from translation_api.services.gloss_translator import (  # noqa: E402
    translate_to_gloss,
    translate_to_gloss_tokens,
)
from translation_api.services.nlp_pipeline import preprocess_arabic_text  # noqa: E402
from translation_api.services.search_service import (  # noqa: E402
    execute_hybrid_search,
    get_all_known_lemmas,
)


def trace(text: str) -> None:
    print(f"\n{'=' * 70}")
    print(f"INPUT: {text!r}")
    print("=" * 70)

    lemmas_preprocess = preprocess_arabic_text(text)
    print(f"\n[preprocess_arabic_text] lemmas: {lemmas_preprocess}")

    tokens = translate_to_gloss_tokens(text)
    print(f"\n[gloss_translator] tokens: {tokens}")

    gloss_raw = translate_to_gloss(text)
    print(f"\n[mBART path] gloss string: {gloss_raw!r}")

    known = get_all_known_lemmas()
    embedding = get_embedding_service().embed_query(text)
    results = execute_hybrid_search(
        lemmas=lemmas_preprocess,
        phrase=text,
        embedding=embedding,
        threshold=0.75,
        per_token_mode=False,
    )
    print("\n[hybrid_search] results:")
    for row in results:
        print(
            f"   seq={row.get('sequence_order')} "
            f"gloss={row.get('matched_lemma')!r} "
            f"type={row.get('match_type')} "
            f"conf={row.get('confidence')} "
            f"url={(row.get('storage_url') or '')[:60]}"
        )
    print()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/trace_translation.py '<arabic text>'")
        sys.exit(1)
    trace(sys.argv[1])
