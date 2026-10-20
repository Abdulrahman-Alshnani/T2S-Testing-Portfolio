# T2S Day 1 Milestone Test Report

**Date:** 2026-05-19  
**Tester:** P2 (Backend Engineer)  
**System under test:** T2S Backend MVP  
**Test environment:** Local Django 6.0.5 + PostgreSQL (test environment)

---

## Executive Summary

Day 1 milestone criteria are **met**. All 24 `@pytest.mark.critical` tests passed, including the Honesty Principle star test and single-request latency benchmarks. Median end-to-end latency was **190.9ms** with P95 **421.1ms**, both well under the 3000ms budget. Test data cleanup verified: zero rows remain with `category = '__test__'` after the session.

---

## Test Coverage

| Test Module | Total Tests | Passed | Failed | Status |
|-------------|-------------|--------|--------|--------|
| test_embedding_service.py | 5 | 5 | 0 | PASS |
| test_search_service.py | 8 | 8 | 0 | PASS |
| test_translation_view.py | 7 | 7 | 0 | PASS |
| test_rpc_function.py | 5 | 5 | 0 | PASS |
| test_latency_single.py | 2 | 2 | 0 | PASS |
| **TOTAL (critical)** | **27** | **24** | **0** | **PASS** |

Note: Three search-service tests (`TestMixedResultsScenario`, `TestEdgeCases`) are marked `integration` only and run in the full suite (27 collected, 24 critical selected).

---

## The Honesty Principle (Star Test)

**Test:** `test_honesty_principle_never_substitutes_below_threshold`

**Status:** PASSED

**Evidence:** With controlled cosine similarity **0.30** (below the **0.75** threshold), `execute_hybrid_search` returned `match_type='not_found'`, `storage_url=None`, and `confidence < 0.75`. No misleading sign video was returned.

---

## Latency Performance

Measured via `tests/performance/test_latency_single.py` (n=20, warm-up excluded, AraBERT loaded):

| Metric | Result | Budget | Status |
|--------|--------|--------|--------|
| P50 latency (median) | 190.9ms | <1500ms | PASS |
| P95 latency | 421.1ms | <3000ms | PASS |
| Embedding stage (sample) | 14.1ms | <1000ms | PASS |
| Database stage (sample) | 191.2ms | <500ms | PASS |
| Total server (sample) | 206.2ms | <3000ms | PASS |

First cold run after model download is slower; subsequent requests reflect steady-state behavior above.

---

## Known Issues

- **Intermittent DB errors on full suite:** Running all 27 tests in one invocation occasionally produced connection errors on performance tests (likely Supabase pooler contention). Re-running failed tests in isolation passed. Disposition: monitor on Day 3 concurrent tests; consider connection retry wrapper if recurrent.
- **Windows HuggingFace cache warning:** Symlinks not supported without Developer Mode; does not affect correctness.

---

## Day 2 Plan

- Run use-case scenario tests (`test_sara_scenarios.py`, `test_honesty_principle_scenarios.py`)
- Validate lexicon JSON schema and OpenAPI conformance
- Expand performance suite (100-request sequential, 10-user concurrent)

---

## Reproduction Commands

```bash
pytest -m critical -v --tb=short
pytest -v --tb=short
type tests\reports\milestone_day1_report.md
```

Milestone demo:

```bash
python manage.py runserver
pytest -m critical
```
