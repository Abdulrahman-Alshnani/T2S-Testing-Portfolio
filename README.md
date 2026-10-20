# 🧪 T2S Testing Portfolio — QA & Test Engineering

[![Static Checks](https://github.com/Abdulrahman-Alshnani/T2S-Testing-Portfolio/actions/workflows/ci.yml/badge.svg)](https://github.com/Abdulrahman-Alshnani/T2S-Testing-Portfolio/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python: 3.11](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![Test Framework: pytest](https://img.shields.io/badge/Tested%20with-pytest-0A9EDC.svg)](https://docs.pytest.org/)

> **Quality Assurance Portfolio** for the **T2S (Text-to-Sign)** Arabic Sign Language translation system.  
> Demonstrates a comprehensive multi-tier test pyramid covering **unit**, **integration**, **subsystem**, **system**, **performance**, **scenario-based**, and **manual** quality verification.

---

## 🔒 Scope & Confidentiality

This repository contains the **test suites, diagnostic tooling, and quality assurance documentation only**. The underlying proprietary production application codebase and trained neural model checkpoints are excluded. 

The test files, schemas, and diagnostics are presented for code review, architectural audit, and QA portfolio evaluation. They illustrate test architecture, regression coverage, and defect prevention strategies designed for production Arabic NLP and multimodal systems.

---

## 📋 Project Context

**T2S** translates Arabic text into Jordanian Sign Language (ArSL) video sequences. The system architecture consists of:
- **Django REST API** backend service
- **AraBERT** (Arabic BERT) for semantic vector embeddings
- **PostgreSQL + pgvector** for high-dimensional hybrid search
- **Four-Tier Hybrid Translation Pipeline**:
  $$\text{Input Text} \longrightarrow \text{Compound Scan} \longrightarrow \text{Lemma Match} \longrightarrow \text{Semantic Vector Match} \longrightarrow \text{Honest Not-Found}$$

---

## 🏗️ Repository Architecture

```
T2S-Testing-Portfolio/
├── tests/
│   ├── unit/                    # Isolated component tests (mocked dependencies)
│   │   ├── test_arabic_normalize.py
│   │   ├── test_compound_prescan.py
│   │   ├── test_embedding_service_real.py
│   │   ├── test_embedding_service_unit.py
│   │   ├── test_gloss_translator_service.py
│   │   ├── test_gloss_translator_unit.py
│   │   ├── test_hallucination_filter.py
│   │   ├── test_lexicon_input_service.py
│   │   ├── test_nlp_align.py
│   │   ├── test_nlp_pipeline_unit.py
│   │   ├── test_serializers_unit.py
│   │   └── test_warmup_view_unit.py
│   │
│   ├── integration/             # Database, RPC, and external boundary integration
│   │   ├── test_database_integration.py
│   │   ├── test_frontend_bridge.py
│   │   ├── test_p1_ingestion_health.py
│   │   ├── test_rpc_function.py
│   │   ├── test_search_service.py
│   │   └── test_storage_urls.py
│   │
│   ├── subsystem/               # Multi-component pipeline interaction tests
│   │   ├── test_fallback_chain.py
│   │   ├── test_nlp_to_search_pipeline.py
│   │   └── test_warmup_then_translate.py
│   │
│   ├── system/                  # End-to-end black-box API contract tests
│   │   ├── test_api_contract.py
│   │   ├── test_concurrency.py
│   │   ├── test_honesty_principle_system.py
│   │   ├── test_translation_view.py
│   │   └── test_warmup_endpoint.py
│   │
│   ├── performance/             # Latency budgets & regression benchmarks
│   │   ├── test_latency_budget.py
│   │   ├── test_latency_single.py
│   │   └── test_regression_suite.py
│   │
│   ├── scenarios/               # User-persona acceptance tests (Sara persona)
│   │   └── test_sara_persona.py
│   │
│   ├── coverage/                # Lexicon dictionary coverage validation
│   │   └── test_lexicon_coverage.py
│   │
│   ├── manual/                  # Exploratory & accessibility verification protocol
│   │   └── manual_testing_protocol.md
│   │
│   ├── reports/                 # Milestone test execution reports
│   │   └── milestone_day1_report.md
│   │
│   └── conftest.py              # Global fixtures, test isolation & markers
│
├── scripts/
│   ├── smoke-tests/             # Deployment & live API smoke validation
│   │   ├── smoke_results.json
│   │   ├── smoke_test_api_manual.py
│   │   ├── smoke_test_arabic_lexicon.py
│   │   ├── smoke_test_demo_sentences.py
│   │   └── smoke_test_mbart_pipeline.py
│   │
│   └── diagnostics/             # Pipeline diagnostics & troubleshooting
│       ├── README.md
│       ├── debug_word_match.py
│       ├── diagnose_mbart_outputs.py
│       ├── diagnose_pipeline_timing.py
│       ├── trace_translation.py
│       └── validate_demo_article.py
│
├── contracts/                   # API & data contracts used for contract testing
│   ├── api_openapi.yaml
│   ├── integration_notes.md
│   └── lexicon_schema.json
│
├── config/                      # Test configuration references
│   └── django_test_settings_reference.py
│
├── docs/                        # Root-Cause Analysis and defect registry
│   └── DEFECTS_AND_RCA.md
│
├── requirements.txt             # Testing dependencies
├── LICENSE                      # MIT License
└── pytest.ini                   # Test runner configuration
```

---

## 🎯 Testing Strategy & Metrics

### Test Suite Metrics

All metrics represent exact counts extracted directly from test modules via AST function inspection:

| Testing Level | Modules | Test Cases | Primary Scope | Primary Frameworks / Tools |
|---|:---:|:---:|---|---|
| **Unit** | 12 | 86 | Morphological normalization, compound prescan, tokenizer, embeddings | `pytest`, `unittest.mock` |
| **Integration** | 6 | 29 | Database connection, pgvector RPC queries, storage reachability, bridge | `pytest-django`, PostgreSQL |
| **Subsystem** | 3 | 7 | Fallback chains, token-to-search pipeline flow, warmup lifecycle | `pytest` |
| **System** | 5 | 33 | Black-box API contract verification, concurrency, Honesty Principle | `pytest`, Django REST Framework |
| **Performance** | 3 | 6 | Latency budgets (P50/P95), single-request budgets, regressions | `pytest-benchmark` |
| **Scenario** | 1 | 11 | End-to-end user journeys (deaf student Sara persona) | `pytest` |
| **Coverage** | 1 | 10 | Complete dictionary lexicon and embedding vector completeness | `pytest` |
| **Total Automated** | **31** | **182** | **Full Automated Test Pyramid** | `pytest` |
| **Manual Protocols** | 1 | 5 sections | Visual verification, accessibility (WCAG), community feedback | Protocol Checklist |

---

## 🐛 Defects & Root-Cause Analysis (RCA)

A cornerstone of this QA portfolio is systematic regression testing for documented defects. Full technical details, root cause analyses, and literal test assertions are maintained in [docs/DEFECTS_AND_RCA.md](docs/DEFECTS_AND_RCA.md).

### Summary of Documented Defects

| Defect ID | Description | Root Cause Category | Verified By |
|---|---|---|---|
| **DEF-01** | Hallucinated gloss "موت" in sports text | Sequence generator hallucination | `test_no_mawt_in_basketball_sentence` |
| **DEF-02** | Hallucinated numeric gloss "مليون" in school text | Contextual language model bias | `test_no_million_in_education_sentence` |
| **DEF-03** | Semantic drift: "الأحمر" returning "الأصفر" | Tight vector space clustering | `test_red_does_not_become_yellow` |
| **DEF-04** | Coordination waw dropping conjoined terms | Tokenizer single-span assumption | `test_conjunction_keeps_both_sides` |
| **DEF-05** | Standalone verb "يكتب" emitting "يأكل" and "هو" | Isolated token generation instability | `test_yiktub_does_not_return_yakul_and_huwa` |
| **DEF-06** | Out-of-vocabulary words matching nearest neighbor | Lack of similarity threshold floor | `test_oov_word_returns_not_found` |
| **DEF-07** | Implausible semantic match on single hover word | Over-permissive single-word vector tier | `test_implausible_semantic_single_token_becomes_not_found` |
| **DEF-08** | Inappropriate pronoun substitution for missing words | Unconstrained fallback service output | `test_single_token_oov_returns_not_found_not_substitute` |
| **DEF-09** | Stripping root letter 'و' from lemmas ("وزير" → "زير") | Naive conjunction prefix regex | `test_wazir_not_stripped_to_zir` |
| **DEF-10** | Video playback 404 from bucket hyphenation mismatch | Asset URL naming inconsistency | `test_storage_urls_use_correct_bucket_name` |
| **DEF-11** | Partial compound prescan emitting lone prefix | Greedy scanner without atomic match | `test_greedy_returns_none_when_only_prefix_is_known` |

---

## 🔍 Key Testing Implementations

### 1. Honesty Principle Verification
The system must never guess or substitute unrelated video clips. Out-of-vocabulary or low-similarity inputs must return `match_type="not_found"` with `storage_url=null`:

```python
# Literal test from tests/system/test_honesty_principle_system.py
@pytest.mark.parametrize("oov_word", ["زوكربيرغ", "تشومسكي", "آينشتاين", "نيتشه"])
def test_oov_word_returns_not_found(self, db, oov_word):
    client = APIClient()
    response = client.post("/api/v1/translate/", {"text": oov_word}, format="json")
    assert response.status_code == 200
    videos = response.json()["videos"]
    not_found_rows = [v for v in videos if v["match_type"] == "not_found"]
    assert len(not_found_rows) >= 1
```

### 2. Lexical Grounding & Hallucination Filtering
Verifies that generated translation glosses strictly correspond to words present in the source Arabic sentence:

```python
# Literal test from tests/unit/test_hallucination_filter.py
@pytest.mark.critical
def test_no_mawt_in_basketball_sentence():
    """The word 'موت' must never appear for a sentence about basketball."""
    glosses = ["راقب", "أبناء", "موت", "سلة"]
    text = "ثم راقب الأبناء وهم يلعبون كرة السلة في الملعب"
    result = _filter_grounded(glosses, text)
    assert "موت" not in result
```

### 3. Arabic Morphology & Conjunction Handling
Verifies proper segmentation of coordination conjunctions (`و`) without corrupting vocabulary roots:

```python
# Literal test from tests/unit/test_nlp_pipeline_unit.py
def test_wazir_not_stripped_to_zir(self):
    """وزير is a lexicon lemma; legacy fallback must not strip its leading و."""
    result = _legacy_regex_tokenize("تفقد وزير التعليم المدرسة")
    assert "زير" not in result
    assert "وزير" in result
```

### 4. Latency Budget Verification
Guarantees response times remain bounded under load:

```python
# Literal test from tests/performance/test_latency_budget.py
def test_warm_p50_under_1500ms(self, db):
    """Median of 20 warm requests must be under 1.5 seconds."""
    # ... execution loop ...
    assert p50 < 1500, f"P50 latency was {p50}ms; expected <1500ms"
```

---

## ⚙️ Test Execution & Configuration

### Registered Markers in `pytest.ini`

```ini
[pytest]
DJANGO_SETTINGS_MODULE = core.settings_test
markers =
    unit: Unit tests, no external dependencies
    integration: Integration tests requiring database
    performance: Performance benchmarks
    use_case: User scenario tests
    contract: Contract validation tests
    slow: Tests that take more than one second
    critical: Milestone-critical tests
    honesty: Honesty Principle verification tests
    subsystem: Tests that verify two or more components together
    system: Black-box tests against the full Django pipeline
    coverage: Tests that iterate over every lexicon entry
    scenario: Use case scenario tests (Sara persona)
    network: Tests that make external HTTP calls
    requires_mbart: Tests that load the real mBART model
    requires_arabert: Tests that load the real AraBERT model
    manual: Checklist for human execution only
```

### Execution Commands

```bash
# Run standard test suite (excluding slow, network, and manual tests)
pytest tests/

# Execute by test level
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest tests/system/ -v
pytest tests/performance/ -v

# Execute by marker
pytest -m critical          # Milestone-critical assertions
pytest -m honesty           # Honesty Principle enforcement
pytest -m scenario          # User persona acceptance journeys
```

---

## 👤 About

**Abdulrahman Alshnani** — QA Engineer & Backend Developer  

🔗 [GitHub Profile](https://github.com/Abdulrahman-Alshnani)
