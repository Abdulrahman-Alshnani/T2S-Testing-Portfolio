"""
Diagnostic: raw mBART gloss output vs lexicon membership.

Read-only. Writes scripts/diagnostic_mbart_outputs.json.
"""

from __future__ import annotations

import json
import os
import sys

import django

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from translation_api.models import SignWord  # noqa: E402
from translation_api.services.gloss_translator import (  # noqa: E402
    gloss_to_words,
    translate_to_gloss,
)

DIAGNOSTIC_INPUTS = [
    "يكتب",
    "يأكل",
    "هو",
    "يقرأ",
    "يدرس",
    "أنا",
    "كرة السلة",
    "الولد يكتب",
    "أنا يكتب",
    "زوكربيرغ",
    "سيارة",
]


def lemma_exists_in_lexicon(token: str) -> bool:
    return SignWord.objects.filter(lemma=token).exclude(category="__test__").exists()


def main() -> None:
    print("Loading mBART (first call paid here)...")
    _ = translate_to_gloss("تهيئة")
    print("Ready.")
    print()

    print("=" * 110)
    print(f"{'Input':<25} {'mBART output':<35} {'Gloss tokens':<40} {'In lexicon?'}")
    print("=" * 110)

    results = []
    for text in DIAGNOSTIC_INPUTS:
        try:
            gloss = translate_to_gloss(text)
            tokens = gloss_to_words(gloss)
            in_lex = [(t, lemma_exists_in_lexicon(t)) for t in tokens]
            in_lex_marks = "".join("Y" if found else "N" for _, found in in_lex)
        except Exception as exc:
            gloss = f"ERROR: {exc}"
            tokens = []
            in_lex = []
            in_lex_marks = "-"

        results.append({
            "input": text,
            "mbart_gloss": gloss,
            "tokens": tokens,
            "tokens_in_lexicon": in_lex,
        })
        print(f"{text:<25} {gloss:<35} {str(tokens):<40} {in_lex_marks}")

    print("=" * 110)
    out_path = "scripts/diagnostic_mbart_outputs.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print()
    print(f"Detailed results saved to {out_path}")

    yiktub = next((r for r in results if r["input"] == "يكتب"), None)
    if yiktub:
        print()
        print("BUG REPORT ANALYSIS — input 'يكتب':")
        print(f"  mBART output: {yiktub['mbart_gloss']!r}")
        print(f"  Tokens produced: {yiktub['tokens']}")
        if "يأكل" in yiktub["tokens"] or "هو" in yiktub["tokens"]:
            print("  CONCLUSION: mBART hallucination — bypass single known lemmas.")
        elif not yiktub["tokens"]:
            print("  CONCLUSION: empty gloss — regex fallback path.")
        else:
            print("  CONCLUSION: mBART reasonable — check search ranking.")


if __name__ == "__main__":
    main()
