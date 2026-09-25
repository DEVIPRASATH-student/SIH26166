# PHASE 5 STAGE 5.5 REPORT: KNOWLEDGE-GAP BENCHMARK
**Project:** LunarSynapse (SIH 26166)  
**Date:** September 2026  
**Status:** COMPLETE & VERIFIED  
**Stage:** 5.5 — Knowledge-Gap Systematic Benchmark Engine

---

## 1. Objective

Stage 5.5 executes a systematic, deterministic benchmark validating that all 8 categories of scientific knowledge gaps are accurately detected and structured with explicit blocking reasons, required evidence, and absence of false negatives.

---

## 2. Benchmark Architecture & Results

Implemented in [`outgraph/ml/world_model/gap_benchmark.py`](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/outgraph/ml/world_model/gap_benchmark.py). Results serialized to [`results/phase5/knowledge_gap_benchmark.json`](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/results/phase5/knowledge_gap_benchmark.json).

### Benchmark Matrix:
| Index | Target Knowledge Gap Type | Scenario Setup | Result | Blocking Reason / Key Evidence |
|---|---|---|:---:|---|
| **1** | `MISSING_SPECTRAL_VALIDATION` | Entity lacks attached hyperspectral IIRS data | **PASS** | `NO_SPECTRAL_DATA_ATTACHED` |
| **2** | `MISSING_TEMPORAL_OBSERVATION` | Entity observed only at a single epoch | **PASS** | Single-epoch observation recorded |
| **3** | `MISSING_GEOMETRIC_VALIDATION` | Unvalidated preliminary candidate entity | **PASS** | Unvalidated candidate feature |
| **4** | `MISSING_TERRAIN_VALIDATION` | Entity lacks 3D DEM or altimetry profile | **PASS** | Requires SLDEM2015 elevation or TMC-2 stereo |
| **5** | `MISSING_MODALITY` | Hyperspectral modality absent across payload | **PASS** | Hyperspectral modality missing |
| **6** | `INSUFFICIENT_CORRESPONDENCE` | Mono-sensor observation lacks cross-sensor corroboration | **PASS** | Mono-sensor observation lacks cross-sensor link |
| **7** | `FOOTPRINT_NON_OVERLAP` | Real OHRC vs TMC-2 Gate 3 rejection ($1.77\text{ km}$ gap) | **PASS** | `PHYSICAL_FOOTPRINT_SEPARATION` |
| **8** | `UNCERTAINTY_TOO_HIGH` | Entity spatial uncertainty ($75.0\text{ m}$) exceeds tolerance ($50.0\text{ m}$) | **PASS** | Uncertainty exceeds scientific tolerance |

### Summary Metrics:
- **Total Scenarios Evaluated:** 8
- **Passed Scenarios:** 8
- **Pass Rate:** 100.0%
- **False Negative Rate:** 0.0%

---

## 3. Verification & Test Results

The test in [`outgraph/tests/test_phase5_gap_benchmark.py`](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/outgraph/tests/test_phase5_gap_benchmark.py) verified:
1. `test_knowledge_gap_benchmark_execution`: Runs the full benchmark, asserts 100% pass rate, checks file persistence, and validates Scenario 7 (`FOOTPRINT_NON_OVERLAP`).

**Test Result:** 1 passed, 0 failed. Total test count: $148 + 1 = 149$.
