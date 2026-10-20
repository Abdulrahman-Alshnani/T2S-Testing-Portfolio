#!/usr/bin/env python
"""Validate that every hover token in the demo article resolves to a lexicon hit."""
from __future__ import annotations

import os
import re
import sys

import django

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from django.conf import settings  # noqa: E402

from translation_api.models import SignWord  # noqa: E402
from translation_api.services.embedding_service import get_embedding_service  # noqa: E402
from translation_api.services.nlp_pipeline import preprocess_arabic_text  # noqa: E402
from translation_api.services.search_service import execute_hybrid_search  # noqa: E402
from translation_api.views import _apply_single_token_semantic_guard  # noqa: E402

ARTICLE = """
في العطلة الصيفية سافرتُ مع عائلتي إلى البتراء والعقبة في الأردن، وبعد عدة أيام زرنا البحر الميت واستمتعنا بالسباحة والتقاط الصور الجميلة طوال اليوم.

في يوم الجمعة اجتمع الأصدقاء في غرفة المعيشة لمشاهدة مباراة كرة القدم على التلفزيون، وبعد انتهاء المباراة لعبوا الشطرنج وتناولوا الطعام وشربوا العصير معًا.

ذهب المريض إلى طبيب الأسنان لأنه كان يعاني من صداع شديد ووجع قوي في الأسنان، وبعد الفحص أعطاه الطبيب دواءً مناسبًا ونصحه بالراحة والعناية بأسنانه يوميًا.
""".strip()

PUNCT = re.compile(r"[.,،؛:!?؟]+$")


def hover_tokens(text: str) -> list[str]:
    tokens = []
    for para in text.split("\n"):
        for raw in para.split():
            cleaned = PUNCT.sub("", raw.strip())
            if cleaned:
                tokens.append(cleaned)
    return tokens


def main() -> None:
    lemmas_in_db = set(
        SignWord.objects.exclude(category="__test__").values_list("lemma", flat=True)
    )
    svc = get_embedding_service()
    threshold = settings.T2S_SIMILARITY_THRESHOLD

    ok = 0
    skip = {"و"}  # conjunction — not in lexicon, acceptable not_found
    for token in hover_tokens(ARTICLE):
        if token in skip:
            print(f"SKIP  {token!r} (function word)")
            continue
        lemmas = preprocess_arabic_text(token)
        emb = svc.embed_query(token)
        rows = _apply_single_token_semantic_guard(
            lemmas,
            execute_hybrid_search(lemmas, token, emb, threshold),
        )
        row = rows[0] if rows else {}
        mt = row.get("match_type")
        matched = row.get("matched_lemma")
        has_url = bool(row.get("storage_url"))
        exact = matched in lemmas_in_db and mt in ("lemma", "compound")
        good = has_url and mt in ("lemma", "compound", "semantic")
        status = "OK" if good else "MISS"
        if good:
            ok += 1
        print(f"{status:4} {token!r:12} -> {mt:10} {matched!r} url={has_url}")

    total = len([t for t in hover_tokens(ARTICLE) if t not in skip])
    print(f"\n{ok}/{total} tokens produce a sign video")


if __name__ == "__main__":
    main()
