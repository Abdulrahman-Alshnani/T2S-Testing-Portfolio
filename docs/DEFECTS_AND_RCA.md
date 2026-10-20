# Defects & Root-Cause Analysis (RCA)

This document provides a comprehensive log of production and milestone defects identified, analyzed, and verified through automated regression suites in the T2S Arabic Sign Language Translation System.

Each defect listed below is backed by explicit automated test cases within the repository.

---

## Defect Summary Registry

| ID | Title | Test Case | Marker | Status |
|---|---|---|---|---|
| **DEF-01** | Hallucinated Gloss "موت" in Sports Context | `test_no_mawt_in_basketball_sentence` | `critical` | Resolved |
| **DEF-02** | Hallucinated Gloss "مليون" in Education Context | `test_no_million_in_education_sentence` | `critical` | Resolved |
| **DEF-03** | Semantic Drift on Color Selection ("الأحمر" returning "الأصفر") | `test_red_does_not_become_yellow` | `critical` | Resolved |
| **DEF-04** | Coordination Waw Dropping Conjoined Tokens | `test_conjunction_keeps_both_sides` | `critical` | Resolved |
| **DEF-05** | Translation Hallucination Emitting "يأكل" and "هو" for "يكتب" | `test_yiktub_does_not_return_yakul_and_huwa` | `system` | Resolved |
| **DEF-06** | Out-of-Vocabulary (OOV) Words Returning Misleading Videos | `test_oov_word_returns_not_found` | `system`, `honesty`, `integration` | Resolved |
| **DEF-07** | Implausible Semantic Substitution on Single Hover Token | `test_implausible_semantic_single_token_becomes_not_found` | `integration`, `critical` | Resolved |
| **DEF-08** | Dishonest Pronoun Substitutions on Single OOV Words | `test_single_token_oov_returns_not_found_not_substitute` | `integration`, `critical` | Resolved |
| **DEF-09** | Erroneous Stripping of Root Letter 'و' in Vocabulary Lemmas | `test_wazir_not_stripped_to_zir` | `unit` | Resolved |
| **DEF-10** | Video Storage Delivery 404 from Bucket Naming Hyphenation | `test_storage_urls_use_correct_bucket_name` | `integration`, `network`, `slow` | Resolved |
| **DEF-11** | Compound Prescan Emitting Incomplete Prefix on Partial Match | `test_greedy_returns_none_when_only_prefix_is_known` | `unit` | Resolved |

---

## Detailed Defect Logs

### DEF-01: Hallucinated Gloss "موت" in Sports Context

- **Description**: Autoregressive neural sequence generation introduced ungrounded tokens into the gloss sequence during sentence-level translation.
- **Symptom**: Input sentence `ثم راقب الأبناء وهم يلعبون كرة السلة في الملعب` produced the hallucinated gloss `موت` (death) alongside basketball terms.
- **Root Cause**: The translation language model generated out-of-context gloss tokens with high language model probability but zero grounding in source Arabic input text.
- **Resolution**: Implementation of `_filter_grounded` to validate generated gloss tokens against input lexical roots, dropping ungrounded tokens before lexicon lookup.
- **Test Details**:
  - **Test Name**: `test_no_mawt_in_basketball_sentence`
  - **File**: `tests/unit/test_hallucination_filter.py`
  - **Marker**: `@pytest.mark.critical`
  - **Status**: Resolved
- **How to verify**: Execute `pytest tests/unit/test_hallucination_filter.py -k test_no_mawt_in_basketball_sentence`.
- **Code Snippet**:
```python
glosses = ["راقب", "أبناء", "موت", "سلة"]
text = "ثم راقب الأبناء وهم يلعبون كرة السلة في الملعب"
result = _filter_grounded(glosses, text)
assert "موت" not in result
```

---

### DEF-02: Hallucinated Gloss "مليون" in Education Context

- **Description**: Spurious numerical glosses generated during administrative sentence translation.
- **Symptom**: Input sentence `تفقد وزير التعليم المدرسة وجلس في صف العلوم` produced ungrounded numerical token `مليون` (million).
- **Root Cause**: Statistical bias in translation training corpus frequently co-occurred government ministry phrases with budget figures.
- **Resolution**: Grounding filter checks semantic alignment with source sentence tokens, discarding spurious numeric tokens.
- **Test Details**:
  - **Test Name**: `test_no_million_in_education_sentence`
  - **File**: `tests/unit/test_hallucination_filter.py`
  - **Marker**: `@pytest.mark.critical`
  - **Status**: Resolved
- **How to verify**: Execute `pytest tests/unit/test_hallucination_filter.py -k test_no_million_in_education_sentence`.
- **Code Snippet**:
```python
glosses = ["وزير", "تعليم", "مدرسة", "مليون"]
text = "تفقد وزير التعليم المدرسة وجلس في صف العلوم"
result = _filter_grounded(glosses, text)
assert "مليون" not in result
```

---

### DEF-03: Semantic Drift on Color Selection ("الأحمر" returning "الأصفر")

- **Description**: Close vector proximity between color representations caused substitution of distinct visual signs.
- **Symptom**: Selecting `اللون الأحمر` (red) returned `الأصفر` (yellow).
- **Root Cause**: Embedding vectors for basic color terms cluster tightly in semantic vector space, leading vector search to match alternative colors when direct match is bypassed.
- **Resolution**: Strict lexical grounding validates selected colors against input tokens, ensuring color fidelity.
- **Test Details**:
  - **Test Name**: `test_red_does_not_become_yellow`
  - **File**: `tests/unit/test_hallucination_filter.py`
  - **Marker**: `@pytest.mark.critical`
  - **Status**: Resolved
- **How to verify**: Execute `pytest tests/unit/test_hallucination_filter.py -k test_red_does_not_become_yellow`.
- **Code Snippet**:
```python
glosses = ["الأحمر", "الأصفر"]
text = "اللون الأحمر"
result = _filter_grounded(glosses, text)
assert "الأصفر" not in result
assert "الأحمر" in result
```

---

### DEF-04: Coordination Waw Dropping Conjoined Tokens

- **Description**: Arabic phrases connected by coordination waw (`و`) failed to preserve both conjoined items.
- **Symptom**: Highlighting `الأحمر والأسود` produced only one color sign instead of both colors.
- **Root Cause**: Tokenizer treated the conjoined string as an unbroken single phrase and failed to segment coordinated components.
- **Resolution**: `_split_on_conjunctions` handles coordination conjunctions and splits phrases into independent sequential items.
- **Test Details**:
  - **Test Name**: `test_conjunction_keeps_both_sides`
  - **File**: `tests/unit/test_hallucination_filter.py`
  - **Marker**: `@pytest.mark.critical`
  - **Status**: Resolved
- **How to verify**: Execute `pytest tests/unit/test_hallucination_filter.py -k test_conjunction_keeps_both_sides`.
- **Code Snippet**:
```python
parts = _split_on_conjunctions("الأحمر والأسود")
assert len(parts) == 2
assert "الأحمر" in parts[0]
assert "الأسود" in parts[1]
```

---

### DEF-05: Translation Hallucination Emitting "يأكل" and "هو" for "يكتب"

- **Description**: Standalone single-word verb lookups triggered unexpected multi-token outputs from sequence generation model.
- **Symptom**: Submitting `يكتب` returned sign videos for `يأكل` (eat) and `هو` (he).
- **Root Cause**: Sequence-to-sequence translation models perform unpredictably when given single isolated word tokens without sentential context.
- **Resolution**: Single known lemma bypass directly checks lexicon entries before delegating to sequence generation.
- **Test Details**:
  - **Test Name**: `test_yiktub_does_not_return_yakul_and_huwa`
  - **File**: `tests/system/test_honesty_principle_system.py`
  - **Marker**: `@pytest.mark.system`
  - **Status**: Resolved
- **How to verify**: Execute `pytest tests/system/test_honesty_principle_system.py -k test_yiktub_does_not_return_yakul_and_huwa`.
- **Code Snippet**:
```python
response = client.post("/api/v1/translate/", {"text": "يكتب"}, format="json")
matched_lemmas = [v.get("matched_lemma") for v in response.json()["videos"]]
assert not ("يأكل" in matched_lemmas and "هو" in matched_lemmas)
```

---

### DEF-06: Out-of-Vocabulary (OOV) Words Returning Misleading Videos

- **Description**: Unknown named entities and out-of-vocabulary words matched nearest vector neighbors, playing incorrect sign videos.
- **Symptom**: Inputting named entities like `زوكربيرغ`, `تشومسكي`, `آينشتاين`, `نيتشه` returned unrelated sign clips.
- **Root Cause**: Vector distance lookups without threshold enforcement always return the mathematical nearest neighbor regardless of absolute similarity.
- **Resolution**: Honesty Principle enforcement: matches below similarity threshold (0.75) strictly return `match_type="not_found"` with `storage_url=null`.
- **Test Details**:
  - **Test Name**: `test_oov_word_returns_not_found`
  - **File**: `tests/system/test_honesty_principle_system.py`
  - **Marker**: `@pytest.mark.system`, `@pytest.mark.honesty`, `@pytest.mark.integration`
  - **Status**: Resolved
- **How to verify**: Execute `pytest tests/system/test_honesty_principle_system.py -k test_oov_word_returns_not_found`.
- **Code Snippet**:
```python
response = client.post("/api/v1/translate/", {"text": oov_word}, format="json")
not_found_rows = [v for v in response.json()["videos"] if v["match_type"] == "not_found"]
assert len(not_found_rows) >= 1
```

---

### DEF-07: Implausible Semantic Substitution on Single Hover Token

- **Description**: Hovering over single words on web pages triggered ungrounded semantic substitutions.
- **Symptom**: User hovered over `يراجع` (review/check) and system returned the sign for `يساند` (support).
- **Root Cause**: Semantic vector search tier permitted broad conceptual similarities for single-word queries without semantic guard.
- **Resolution**: Implementation of `_apply_single_token_semantic_guard` ensuring single-word queries only accept exact lemma, known compound, or validated curated synonyms.
- **Test Details**:
  - **Test Name**: `test_implausible_semantic_single_token_becomes_not_found`
  - **File**: `tests/system/test_translation_view.py`
  - **Marker**: `@pytest.mark.integration`, `@pytest.mark.critical`
  - **Status**: Resolved
- **How to verify**: Execute `pytest tests/system/test_translation_view.py -k test_implausible_semantic_single_token_becomes_not_found`.
- **Code Snippet**:
```python
response = api_client.post(ENDPOINT, data={"text": "يراجع"}, format="json")
body = response.json()
assert body["videos"][0]["match_type"] == "not_found"
assert body["videos"][0]["storage_url"] is None
```

---

### DEF-08: Dishonest Pronoun Substitutions on Single OOV Words

- **Description**: External semantic fallback mappings substituted unrelated pronouns for missing words.
- **Symptom**: Submitting `اخي` or `من` resulted in playback of `أنا` or `نحن` sign videos.
- **Root Cause**: Secondary fallback service mapped ungrounded words to high-frequency pronouns.
- **Resolution**: Semantic guard intercepts fallback output on single tokens and forces explicit `not_found` with `storage_url=null`.
- **Test Details**:
  - **Test Name**: `test_single_token_oov_returns_not_found_not_substitute`
  - **File**: `tests/system/test_translation_view.py`
  - **Marker**: `@pytest.mark.integration`, `@pytest.mark.critical`
  - **Status**: Resolved
- **How to verify**: Execute `pytest tests/system/test_translation_view.py -k test_single_token_oov_returns_not_found_not_substitute`.
- **Code Snippet**:
```python
for word in ("اخي", "من"):
    response = api_client.post(ENDPOINT, data={"text": word}, format="json")
    body = response.json()
    assert body["videos"][0]["match_type"] == "not_found"
    assert body["videos"][0]["storage_url"] is None
```

---

### DEF-09: Erroneous Stripping of Root Letter 'و' in Vocabulary Lemmas

- **Description**: Words starting with the root consonant `و` had their initial letter stripped as if it were a conjunction.
- **Symptom**: Sentence containing `تفقد وزير التعليم المدرسة` stripped `و` from `وزير` (minister), yielding invalid token `زير`.
- **Root Cause**: Regular expression prefix strip rule indiscriminately removed leading `و` without consulting the dictionary of root lemmas.
- **Resolution**: Lemma lookahead verifies whether token is an established lexicon entry before applying coordination clitic stripping.
- **Test Details**:
  - **Test Name**: `test_wazir_not_stripped_to_zir`
  - **File**: `tests/unit/test_nlp_pipeline_unit.py`
  - **Marker**: `@pytest.mark.unit`
  - **Status**: Resolved
- **How to verify**: Execute `pytest tests/unit/test_nlp_pipeline_unit.py -k test_wazir_not_stripped_to_zir`.
- **Code Snippet**:
```python
result = _legacy_regex_tokenize("تفقد وزير التعليم المدرسة")
assert "زير" not in result
assert "وزير" in result
```

---

### DEF-10: Video Storage Delivery 404 from Bucket Naming Hyphenation

- **Description**: Video playback in web extension failed with 404 errors due to URL path mismatch.
- **Symptom**: Video player in client application displayed broken video state on valid lexicon matches.
- **Root Cause**: Data ingestion pipelines generated URLs containing `/sign-videos/` (hyphen) whereas the storage bucket was named `sign_videos` (underscore).
- **Resolution**: Ingestion schema and URL generators standardized on `sign_videos`, verified by automated database assertion.
- **Test Details**:
  - **Test Name**: `test_storage_urls_use_correct_bucket_name`
  - **File**: `tests/integration/test_storage_urls.py`
  - **Marker**: `@pytest.mark.integration`, `@pytest.mark.network`, `@pytest.mark.slow`
  - **Status**: Resolved
- **How to verify**: Execute `pytest tests/integration/test_storage_urls.py -k test_storage_urls_use_correct_bucket_name`.
- **Code Snippet**:
```python
wrong_bucket = VideoMapping.objects.filter(storage_url__icontains="/sign-videos/").count()
assert wrong_bucket == 0
```

---

### DEF-11: Compound Prescan Emitting Incomplete Prefix on Partial Match

- **Description**: Prescan span detector emitted incomplete initial words when a compound expression was only partially available.
- **Symptom**: Query `وزارة المالية` would return a lone prefix `وزارة` if the full compound was not recognized.
- **Root Cause**: Greedy span detection emitted partial matching sub-slices rather than requiring full compound recognition.
- **Resolution**: Prescan ensures multi-word compound detection is atomic; if the full compound is not matched, the scanner returns `None` to allow individual token processing.
- **Test Details**:
  - **Test Name**: `test_greedy_returns_none_when_only_prefix_is_known`
  - **File**: `tests/unit/test_compound_prescan.py`
  - **Marker**: `@pytest.mark.unit`
  - **Status**: Resolved
- **How to verify**: Execute `pytest tests/unit/test_compound_prescan.py -k test_greedy_returns_none_when_only_prefix_is_known`.
- **Code Snippet**:
```python
with patch("translation_api.views._span_is_known_lexicon_phrase", side_effect=lambda s: s == "وزارة"):
    assert _greedy_compound_spans("وزارة المالية") is None
```
