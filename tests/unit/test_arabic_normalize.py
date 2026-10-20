"""Unit tests for Arabic surface normalization."""

from unittest.mock import patch

import pytest

from translation_api.services.arabic_normalize import (
    normalize_arabic_phrase,
    normalize_morphological_token,
    normalize_numbers_in_text,
    strip_leading_coordination_waw,
    strip_word_punctuation,
)
from translation_api.services.gloss_translator import _split_on_conjunctions
from translation_api.views import _greedy_compound_spans


@pytest.mark.unit
class TestMorphology:
    def test_dual_imperfect_maps_to_lemma(self):
        known = frozenset({"يمشي", "يأكل", "يناقش"})
        assert normalize_morphological_token("يمشيان", known) == "يمشي"
        assert normalize_morphological_token("يأكلان", known) == "يأكل"
        assert normalize_morphological_token("يناقشان", known) == "يناقش"


@pytest.mark.unit
class TestNumbers:
    def test_digit_one_becomes_arabic_word(self):
        assert normalize_numbers_in_text("1") == "واحد"

    def test_english_one_becomes_arabic_word(self):
        assert normalize_numbers_in_text("one") == "واحد"

    def test_digit_two_and_english_two(self):
        assert normalize_numbers_in_text("2") == "اثنان"
        assert normalize_numbers_in_text("two") == "اثنان"

    def test_multi_digit_numbers(self):
        assert normalize_numbers_in_text("20") == "عشرون"
        assert normalize_numbers_in_text("99") == "تسعة وتسعون"
        assert normalize_numbers_in_text("100") == "مائة"
        assert normalize_numbers_in_text("999") == "تسعمائة وتسعة وتسعون"
        assert normalize_numbers_in_text("1000") == "ألف"
        assert normalize_numbers_in_text("10000") == "عشرة آلاف"
        assert normalize_numbers_in_text("1000000") == "مليون"

    def test_english_compound_number_phrases(self):
        assert normalize_numbers_in_text("twenty") == "عشرون"
        assert normalize_numbers_in_text("ninety nine") == "تسعة وتسعون"
        assert normalize_numbers_in_text("nine hundred ninety nine") == "تسعمائة وتسعة وتسعون"
        assert normalize_numbers_in_text("ten thousand") == "عشرة آلاف"
        assert normalize_numbers_in_text("one million") == "مليون"

    def test_normalize_gloss_maps_digits_before_arabic_check(self):
        from translation_api.services.lexicon_input import normalize_gloss_input

        assert normalize_gloss_input("1") == "واحد"
        assert normalize_gloss_input("one") == "واحد"


@pytest.mark.unit
class TestPhraseAliases:
    def test_inshaallah_spelling(self):
        assert normalize_arabic_phrase("ان شاء الله") == "إن شاء الله"

    def test_alhamdulillah_compact(self):
        assert normalize_arabic_phrase("الحمدلله") == "الحمد لله"

    def test_good_and_bad_deeds_aliases(self):
        assert normalize_arabic_phrase("الحسنات") == "أعمال صالحة"
        assert normalize_arabic_phrase("السيئات") == "أعمال سيئة"


@pytest.mark.unit
class TestConjunctionSplit:
    def test_splits_parliament_and_senate(self):
        parts = _split_on_conjunctions("مجلس النواب ومجلس الأعيان")
        assert parts == ["مجلس النواب", "مجلس الأعيان"]

    def test_does_not_split_waw_inside_wazara_after_verb(self):
        parts = _split_on_conjunctions(
            "الوزير يطور وزارة الصحة ووزارة التربية والتعليم"
        )
        assert parts == [
            "الوزير يطور وزارة الصحة",
            "وزارة التربية والتعليم",
        ]

    def test_both_health_and_education_ministries(self):
        parts = _split_on_conjunctions("وزارة الصحة ووزارة التربية والتعليم")
        assert parts == ["وزارة الصحة", "وزارة التربية والتعليم"]


@pytest.mark.unit
class TestLeadingWaw:
    def test_strip_waw_before_known_ministry(self):
        assert (
            strip_leading_coordination_waw("ووزارة التربية والتعليم")
            == "وزارة التربية والتعليم"
        )


@pytest.mark.unit
class TestPunctuation:
    def test_strips_trailing_period_from_tokens(self):
        assert strip_word_punctuation("بيضة.") == "بيضة"
        assert "البيضة" in normalize_arabic_phrase("البيضة.")


@pytest.mark.unit
class TestParagraphSpanCounts:
    def test_food_paragraph_includes_meat_and_sweets(self):
        from translation_api.views import _greedy_compound_spans

        text = (
            "الأم تشتري اللحم والدجاج والسمك والبيضة. المنسف والمقلوبة "
            "والملوخية والفلافل طعام. الشوكولاتة والكعكة والبودنغ والمهلبية حلويات."
        )
        spans = _greedy_compound_spans(text)
        assert "لحم" in spans
        assert "فلافل" in spans
        assert "مهلبية" in spans
        assert len(spans) >= 14

    def test_school_paragraph_twelve_signs(self):
        from translation_api.views import _greedy_compound_spans

        text = (
            "الطالب يدرس مادة الرياضيات ومادة العلوم. المعلم يدرس مادة التاريخ "
            "ومادة الجغرافيا. الطالب يتعلم مادة اللغة العربية ومادة الفيزياء."
        )
        spans = _greedy_compound_spans(text)
        assert len(spans) == 12
        assert "طالب" in spans
        assert "مادة الفيزياء" in spans


@pytest.mark.unit
class TestAlefHamzaSpellings:
    def test_afghanistan_without_hamza_resolves(self):
        from translation_api.services.lemma_cache import (
            resolve_token_to_lemma,
            warm_lemma_cache,
        )

        warm_lemma_cache()
        assert resolve_token_to_lemma("افغانستان") == "أفغانستان"


@pytest.mark.unit
class TestGreedyCompoundSpans:
    def test_two_subject_phrases_in_one_highlight(self):
        with patch(
            "translation_api.views._span_is_known_lexicon_phrase",
            side_effect=lambda s: s
            in {
                "مادة الرياضيات",
                "مادة العلوم",
                "مادة التاريخ",
            },
        ):
            spans = _greedy_compound_spans("مادة الرياضيات مادة العلوم مادة التاريخ")
        assert spans == ["مادة الرياضيات", "مادة العلوم", "مادة التاريخ"]

    def test_conjoined_councils(self):
        with patch(
            "translation_api.views._span_is_known_lexicon_phrase",
            side_effect=lambda s: s in {"مجلس النواب", "مجلس الأعيان"},
        ):
            spans = _greedy_compound_spans("مجلس النواب ومجلس الأعيان")
        assert spans == ["مجلس النواب", "مجلس الأعيان"]
