"""
Regression tests: confirm hallucinated glosses are dropped.

Each test corresponds to a real bug reported during T2S graduation testing.
"""

import pytest

from translation_api.services.gloss_translator import (
    _filter_grounded,
    _split_on_conjunctions,
)


@pytest.mark.critical
def test_no_mawt_in_basketball_sentence():
    """The word 'موت' must never appear for a sentence about basketball."""
    glosses = ["راقب", "أبناء", "موت", "سلة"]
    text = "ثم راقب الأبناء وهم يلعبون كرة السلة في الملعب"
    result = _filter_grounded(glosses, text)
    assert "موت" not in result


@pytest.mark.critical
def test_no_million_in_education_sentence():
    """The word 'مليون' must never appear for a minister visiting a school."""
    glosses = ["وزير", "تعليم", "مدرسة", "مليون"]
    text = "تفقد وزير التعليم المدرسة وجلس في صف العلوم"
    result = _filter_grounded(glosses, text)
    assert "مليون" not in result


@pytest.mark.critical
def test_red_does_not_become_yellow():
    """Selecting 'الأحمر' must not return 'الأصفر'."""
    glosses = ["الأحمر", "الأصفر"]
    text = "اللون الأحمر"
    result = _filter_grounded(glosses, text)
    assert "الأصفر" not in result
    assert "الأحمر" in result


@pytest.mark.critical
def test_conjunction_keeps_both_sides():
    """'الأحمر والأسود' must produce results for both colors."""
    parts = _split_on_conjunctions("الأحمر والأسود")
    assert len(parts) == 2
    assert "الأحمر" in parts[0]
    assert "الأسود" in parts[1]
