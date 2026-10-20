# 🧪 T2S Testing Portfolio — QA & Test Engineering

> **Quality Assurance portfolio** for the **T2S (Text-to-Sign)** Arabic Sign Language translation system.  
> This repository showcases a comprehensive testing strategy covering **unit**, **integration**, **system**, **performance**, **scenario-based**, and **manual** testing levels.

---

## 📋 Project Context

**T2S** translates Arabic text into Jordanian Sign Language (ArSL) video sequences. The system uses:
- **Django REST API** backend
- **AraBERT** (Arabic BERT) for semantic embeddings
- **PostgreSQL + pgvector** for hybrid search
- **Hybrid translation pipeline**: compound → lemma → semantic → not_found

---

## 🏗️ Testing Architecture

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
│   ├── integration/             # Database + service integration
│   │   ├── test_database_integration.py
│   │   ├── test_frontend_bridge.py
│   │   ├── test_p1_ingestion_health.py
│   │   ├── test_rpc_function.py
│   │   ├── test_search_service.py
│   │   └── test_storage_urls.py
│   │
│   ├── subsystem/               # Multi-component pipeline tests
│   │   ├── test_fallback_chain.py
│   │   ├── test_nlp_to_search_pipeline.py
│   │   └── test_warmup_then_translate.py
│   │
│   ├── system/                  # End-to-end black-box API tests
│   │   ├── test_api_contract.py
│   │   ├── test_concurrency.py
│   │   ├── test_honesty_principle_system.py
│   │   ├── test_translation_view.py
│   │   └── test_warmup_endpoint.py
│   │
│   ├── performance/             # Latency budgets & benchmarks
│   │   ├── test_latency_budget.py
│   │   ├── test_latency_single.py
│   │   └── test_regression_suite.py
│   │
│   ├── scenarios/               # User-persona scenario tests
│   │   └── test_sara_persona.py
│   │
│   ├── coverage/                # Lexicon coverage analysis
│   │   └── test_lexicon_coverage.py
│   │
│   ├── manual/                  # Manual testing protocols
│   │   └── manual_testing_protocol.md
│   │
│   ├── reports/                 # Test execution reports
│   │   └── milestone_day1_report.md
│   │
│   └── conftest.py              # Shared fixtures & test configuration
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
└── pytest.ini                   # Test runner configuration
```

---

## 🎯 Testing Strategy

### Test Pyramid Implementation

```
                    ╔══════════════╗
                    ║   Manual     ║  ← Manual testing protocols
                    ║  Testing     ║    (exploratory, accessibility)
                    ╚══════╦═══════╝
                   ╔═══════╩════════╗
                   ║    System      ║  ← End-to-end API contract tests
                   ║    Tests       ║    (black-box, concurrency)
                   ╚═══════╦════════╝
                ╔══════════╩═══════════╗
                ║   Subsystem /        ║  ← Multi-component pipeline tests
                ║   Integration        ║    (DB, storage, fallback chains)
                ╚══════════╦═══════════╝
           ╔═══════════════╩════════════════╗
           ║         Unit Tests             ║  ← Isolated, fast, mocked
           ║   (NLP, embeddings, serializers)║    (10+ test modules)
           ╚════════════════════════════════╝
```

### Testing Levels

| Level | Count | Purpose | Tools |
|-------|-------|---------|-------|
| **Unit** | 10 modules | Isolated component validation with mocked dependencies | `pytest`, `unittest.mock` |
| **Integration** | 4 modules | Database, storage URL, and frontend bridge verification | `pytest-django`, PostgreSQL |
| **Subsystem** | 3 modules | Multi-component pipeline interaction testing | `pytest` |
| **System** | 4 modules | Black-box API contract and concurrency testing | `pytest`, OpenAPI |
| **Performance** | 3 modules | Latency budgets, single-request timing, regression | `pytest-benchmark` |
| **Scenario** | 1 module | User-persona based testing (Sara persona) | `pytest` |
| **Coverage** | 1 module | Lexicon coverage analysis across all entries | `pytest` |
| **Smoke** | 3 scripts | Deployment validation and live API verification | Custom scripts |
| **Manual** | 1 protocol | Human-executed exploratory testing checklist | Markdown protocol |

---

## 🔍 Key Testing Highlights

### 1. Honesty Principle Testing
Tests that verify the system **never returns a wrong sign** — when confidence is below threshold, the API returns `not_found` instead of guessing:

```python
# test_honesty_principle_system.py
def test_unknown_word_returns_not_found():
    """System must NOT hallucinate a sign for unknown words."""
    response = client.post("/api/v1/translate/", {"text": "فلسفة"})
    assert response.data["videos"][0]["match_type"] == "not_found"
```

### 2. Arabic NLP Pipeline Testing
Comprehensive tests for Arabic text normalization, diacritic stripping, and lemmatization:

```python
# test_arabic_normalize.py
@pytest.mark.parametrize("input_text,expected", [
    ("السَّلامُ", ["سلام"]),      # Diacritic stripping
    ("كرة القدم", ["كرة القدم"]),  # Compound preservation
    ("المدرسة", ["مدرسة"]),        # Article removal
])
def test_preprocessing(input_text, expected):
    assert preprocess_arabic_text(input_text) == expected
```

### 3. Performance Budget Testing
Ensures translation latency stays within acceptable bounds:

```python
# test_latency_budget.py
@pytest.mark.performance
def test_single_word_under_500ms():
    """Single-word translation must complete within 500ms budget."""
    start = time.perf_counter()
    response = client.post("/api/v1/translate/", {"text": "أنا"})
    elapsed = (time.perf_counter() - start) * 1000
    assert elapsed < 500, f"Latency {elapsed:.0f}ms exceeds 500ms budget"
```

### 4. Hallucination Filter Testing
Validates the semantic guard that prevents returning unrelated signs:

```python
# test_hallucination_filter.py
def test_rejects_unrelated_semantic_match():
    """Semantic match must be rejected if surface forms don't overlap."""
    # Prevents playing "cat" video when user searches "car"
```

### 5. User Scenario Testing (Sara Persona)
Real-world user journey tests based on a deaf student persona:

```python
# test_sara_persona.py
class TestSaraPersona:
    """Sara is a deaf university student browsing Arabic news articles."""
    
    def test_sara_highlights_paragraph(self):
        """Sara highlights a full paragraph — system returns ordered videos."""
    
    def test_sara_hovers_unknown_word(self):
        """Sara hovers over a word not in lexicon — sees helpful 'not found' message."""
```

---

## 🔧 Test Configuration

### pytest.ini — Test Markers

```ini
[pytest]
DJANGO_SETTINGS_MODULE = core.settings_test
markers =
    unit: Unit tests, no external dependencies
    integration: Integration tests requiring database
    performance: Performance benchmarks
    use_case: User scenario tests
    contract: Contract validation tests
    honesty: Honesty Principle verification tests
    subsystem: Tests that verify two or more components together
    system: Black-box tests against the full Django pipeline
    coverage: Tests that iterate over every lexicon entry
    scenario: Use case scenario tests (Sara persona)
    manual: Checklist for human execution only
```

### Running Tests

```bash
# All automated tests (excludes slow, network, manual)
pytest tests/

# By test level
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest tests/system/ -v
pytest tests/performance/ -v

# By marker
pytest -m critical          # Milestone-critical tests
pytest -m honesty           # Honesty principle verification
pytest -m "not slow"        # Quick feedback loop
pytest -m scenario          # User persona tests

# Smoke tests (against live API)
python scripts/smoke-tests/smoke_test_demo_sentences.py
python scripts/smoke-tests/smoke_test_arabic_lexicon.py
```

---

## 🛠️ Tools & Frameworks

| Tool | Purpose |
|------|---------|
| **pytest** | Test runner and assertion framework |
| **pytest-django** | Django integration for database and client fixtures |
| **pytest-benchmark** | Performance measurement and regression detection |
| **unittest.mock** | Dependency mocking for unit test isolation |
| **OpenAPI (YAML)** | API contract validation |
| **JSON Schema** | Lexicon data contract validation |

---

## 📊 Test Metrics

| Metric | Value |
|--------|-------|
| Total test modules | **25+** |
| Test levels covered | **7** (unit, integration, subsystem, system, performance, scenario, manual) |
| Custom pytest markers | **12** |
| Smoke test scripts | **3** |
| Smoke test sentences | **14** curated Arabic sentences |
| Lexicon entries tested | **327** sign words |
| Latency budget | **< 500ms** per single-word translation |

---

## 📝 Manual Testing Protocol

A structured manual testing checklist is provided in [`tests/manual/manual_testing_protocol.md`](tests/manual/manual_testing_protocol.md) for:
- Browser compatibility testing
- Chrome extension interaction testing
- Accessibility verification
- Arabic text rendering validation
- Video playback verification

---

## 👤 About

**Abdulrahman Alshnani** — QA Engineer & Backend Developer  

🔗 [GitHub Profile](https://github.com/Abdulrahman-Alshnani)
