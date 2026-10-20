#!/usr/bin/env python
"""Debug which sign video the API returns for single-word hover queries."""
from __future__ import annotations

import os
import sys

import django

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from django.conf import settings  # noqa: E402

from translation_api.services.embedding_service import get_embedding_service  # noqa: E402
from translation_api.services.nlp_pipeline import preprocess_arabic_text  # noqa: E402
from translation_api.services.search_service import execute_hybrid_search  # noqa: E402

# Words from the bundled demo article (hover targets)
WORDS = [
    "جلس",
    "الطالب",
    "يراجع",
    "دروسه",
    "بعدين",
    "يراقب",
    "الأستاذ",
    "زوكربيرغ",
    "تكنولوجيا",
    "عقدت.",
    "المتحدة",
]


def main() -> None:
    svc = get_embedding_service()
    print(f"Threshold: {settings.T2S_SIMILARITY_THRESHOLD}\n")
    for word in WORDS:
        lemmas = preprocess_arabic_text(word)
        emb = svc.embed_query(word)
        rows = execute_hybrid_search(
            lemmas, word, emb, settings.T2S_SIMILARITY_THRESHOLD
        )
        row = rows[0] if rows else {}
        conf = row.get("confidence")
        conf_s = f"{conf:.3f}" if conf is not None else "n/a"
        print(
            f"{word!r:12} lemmas={lemmas!r:15} "
            f"type={row.get('match_type')!s:10} "
            f"matched={row.get('matched_lemma')!r} conf={conf_s}"
        )


if __name__ == "__main__":
    main()
