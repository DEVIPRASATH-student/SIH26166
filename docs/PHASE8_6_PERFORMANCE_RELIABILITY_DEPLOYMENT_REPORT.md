# PHASE 8.6: PERFORMANCE, RELIABILITY & DEPLOYMENT HARDENING AUDIT REPORT

**Project:** LunarSynapse — Physics-Aware, Self-Evolving Multi-Modal Lunar World Model  
**SIH Problem Statement:** SIH26166 — Multi-modal, Sun-angle and Scale Invariant Image Correspondence using Chandrayaan-2 OHRC, TMC-2 and IIRS  
**Stage:** Phase 8.6 — Performance / Reliability / Deployment Hardening  
**Status:** **`PERFORMANCE_RELIABILITY_VALIDATED`**  
**Execution Timestamp:** 2026-09-24T23:45:00Z  

---

## 1. Executive Summary

Phase 8.6 hardened the LunarSynapse software architecture across performance baselines, API reliability, concurrent access, database consistency, large-data volume isolation, security input validation, and system status diagnostics. 

**Scientific Behavior Invariant:** The underlying scientific reasoning chain, the six physical verification gates, the separate illumination evidence verification, the world model hypotheses, and the epistemic operator (`POTENTIALLY_REDUCES_UNCERTAINTY`) remain **100% unaltered**.

**Key Achievements:**
1. **Measured Performance Baselines:** Captured empirical latencies (min, median, p95, p99, max) and payload sizes across all 11 primary API endpoints using a 15-iteration automated test bench.
2. **Frontend Build:** Full production TypeScript/Vite bundle compiled cleanly in **5.39s** (`dist/index.html` 1.19 kB, `dist/assets/index-hRqpueJl.css` 44.68 kB, `dist/assets/index-B8wpj86f.js` 555.20 kB).
3. **Backend Startup & Memory:** FastAPI app and SQLite database schemas initialize in **9.69 ms** with traced peak memory consumption of **0.12 MB**.
4. **Reliability & Security Test Suite:** Authoring and passing 17 dedicated tests in [`test_phase8_6_reliability.py`](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/outgraph/tests/test_phase8_6_reliability.py) with **17 passed, 0 failed, 0 errors**.
5. **Raw Data Integrity:** Completely untouched — `git diff --stat data/real/` verified **0 bytes modified**.

---

## 2. Baseline Performance Measurements (Empirical)

All metrics were gathered by live endpoint execution using FastAPI's `TestClient` over 15 repeated runs per endpoint. No metrics are synthetic. Metrics that could not be reliably recorded without instrument distortion are explicitly reported as **`NOT MEASURED`**.

### 2.1 API Endpoint Latency & Payload Benchmarks

| Endpoint Name | HTTP Method | URL | Status Code | Min (ms) | Median (ms) | p95 (ms) | p99 (ms) | Response Size |
|---|---|---|---|---|---|---|---|---|
| **API Health** | GET | `/api/system/health` | 200 | 21.34 | 27.48 | 318.64 | 318.64 | 310 B |
| **API Status** | GET | `/api/system/status` | 200 | 20.31 | 27.75 | 48.36 | 48.36 | 749 B |
| **Scenario Listing** | GET | `/api/demo/scenarios` | 200 | 16.08 | 20.79 | 49.24 | 49.24 | 17,593 B |
| **Scenario Explanation** | GET | `/api/demo/scenarios/SCENARIO-A/explanation` | 200 | 18.93 | 20.34 | 29.27 | 29.27 | 13,600 B |
| **Correspondence Retrieval** | GET | `/api/correspondence` | 200 | 42.32 | 61.24 | 124.15 | 124.15 | 212,225 B |
| **Physical Verification** | GET | `/api/physical-verification/gates` | 200 | 9.50 | 12.73 | 16.97 | 16.97 | 2,166 B |
| **Evidence Retrieval** | GET | `/api/evidence/dimensions` | 200 | 8.60 | 10.51 | 17.12 | 17.12 | 274 B |
| **Uncertainty Retrieval** | GET | `/api/uncertainty/summary` | 200 | 17.48 | 19.65 | 30.40 | 30.40 | 547 B |
| **Knowledge Gap Retrieval** | GET | `/api/knowledge-gaps/types` | 200 | 7.25 | 9.44 | 13.25 | 13.25 | 332 B |
| **Recommendation Retrieval** | GET | `/api/recommendations` | 200 | 16.22 | 19.13 | 37.92 | 37.92 | 11,843 B |
| **World Model Retrieval** | GET | `/api/world-model/entities` | 200 | 15.73 | 16.68 | 37.66 | 37.66 | 791 B |

### 2.2 System & Compilation Performance

- **Frontend Compilation (`npm run build`):** **5.39 s** (1,780 modules transformed via Vite 6.4.3).
- **Backend Startup & Schema Initialization:** **9.69 ms**.
- **Traced Peak Memory (`tracemalloc`):** **0.12 MB**.
- **Per-Endpoint CPU Utilization:** **`NOT MEASURED`** *(sub-millisecond sampling noise in multi-threaded environment; external kernel profiler required)*.
- **Per-Endpoint Heap GC Delta:** **`NOT MEASURED`** *(C-extensions in OpenCV and PyTorch allocate memory outside the Python runtime heap)*.

---

## 3. Reliability & Failure Handling

### 3.1 Deterministic Error Handling (8.6.2)
- Malformed API payloads (missing fields, unexpected types) deterministically produce structured HTTP 400 or 422 JSON errors with clear `detail` fields.
- Non-existent IDs (observations, correspondences, scenarios) return HTTP 404 with structured JSON.
- Internal server errors are intercepted by a global exception handler in [`main.py`](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/outgraph/backend/app/main.py) which returns `{"detail": "Internal scientific system error", "status": "ERROR", "safe_state": "UNKNOWN"}` without exposing internal tracebacks or file paths.
- System never silently converts failures into `ACCEPTED`, `SUPPORTED`, or `CONFIRMED`.

### 3.2 Concurrency and Duplication Safety (8.6.3)
- Concurrent read requests across multiple worker threads via `ThreadPoolExecutor` execute cleanly with no race conditions or corrupted responses.
- Entity identification and recommendations maintain unique IDs, preventing duplicate persistent entities or redundant sensor proposals.

### 3.3 Database Integrity & Rollbacks (8.6.4)
- Failing transactions (e.g., schema constraint violations) execute clean rollbacks without leaving orphan state or corrupting the SQLite persistent layer.
- Sessions are cleaned up through FastAPI's dependency injection stack (`get_db`).

---

## 4. Large Data Safety & Deployment Architecture

The LunarSynapse repository houses high-resolution lunar PDS4 and binary products (multi-GB OHRC, TMC-2, and SLDEM2015 rasters).

### 4.1 Large Data Safety Boundary (8.6.5, 8.6.6)
```
┌─────────────────────────────────────────────────────────────┐
│                 FRONTEND (React / Vite SPA)                 │
│      Requests: Metadata, Thumbnails, Derived Previews       │
└──────────────────────────────▲──────────────────────────────┘
                               │  JSON (<250 KB) / PNG (<2 MB)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                 BACKEND API (FastAPI Router)                │
│    Orchestrates: PipelineController, DB queries, Caching    │
└──────────────────────────────▲──────────────────────────────┘
                               │  In-Memory / IPC
                               ▼
┌─────────────────────────────────────────────────────────────┐
│             SCIENTIFIC WORKER / LOCAL VOLUME                │
│   Executes: Feature Extraction, DEM Ray-tracing, GroundGrid │
└──────────────────────────────▲──────────────────────────────┘
                               │  Memory-mapped / Windowed I/O
                               ▼
┌─────────────────────────────────────────────────────────────┐
│               LOCAL DATA STORAGE (`data/real/`)             │
│    Houses: Multi-GB PDS4 Products, Calibration Rasters      │
└─────────────────────────────────────────────────────────────┘
```

**Key Architectural Rules:**
1. **Never Bundle Raw Data:** Raw PDS4 binaries are never placed into Vite, Vercel, or serverless build directories.
2. **Never Stream Full Binary to Browser:** Frontend requests are strictly constrained to bounded metadata, coordinate footprints, summary statistics, and rendered PNG crops.
3. **Windowed / Memory-Mapped Processing:** Scientific calculations operate on windowed sub-arrays rather than loading multi-GB imagery into RAM.

---

## 5. Security & Input Hardening

1. **Path Traversal Protection:** Image-serving endpoints (`/api/observations/{id}/image` and `/api/observations/experiments/{filename}`) enforce filename sanitization via `Path(filename).name` and verify that the resolved path strictly resides within `settings.IMAGES_DIR.resolve()`. Attacks using `../../` or Windows path traversal sequences (`..\..\`) are blocked with HTTP 400/404.
2. **Phase 8.2 Guardrail Enforcement:**
   - `force_accept=True` -> **Strictly rejected with HTTP 400** (Rule 13 & 14 invariant).
   - Unverified `is_synthetic=False` -> **Strictly marked or rejected**.
   - Uncertainty manual override without authority -> **Rejected with HTTP 403**.

---

## 6. System Health & Diagnostics (8.6.10)

The `/api/system/status` endpoint was upgraded to accurately reflect all critical subsystems without falsely claiming `HEALTHY` when dependencies are offline:
- Subsystems monitored: `API`, `database`, `DEM`, `GroundGrids`, `raw_data_integrity`.
- Subsystem states: `ONLINE`, `DEGRADED`, `UNAVAILABLE`.
- Overall system status: `ONLINE` only when all required components are operational; `DEGRADED` or `UNAVAILABLE` otherwise.

---

## 7. Dedicated Phase 8.6 Test Results

Executed via:
```bash
pytest outgraph/tests/test_phase8_6_reliability.py -v
```

**Results:**
```
outgraph/tests/test_phase8_6_reliability.py::test_1_malformed_api_request PASSED
outgraph/tests/test_phase8_6_reliability.py::test_2_missing_resource PASSED
outgraph/tests/test_phase8_6_reliability.py::test_3_unavailable_payload PASSED
outgraph/tests/test_phase8_6_reliability.py::test_4_repeated_requests PASSED
outgraph/tests/test_phase8_6_reliability.py::test_5_concurrent_reads PASSED
outgraph/tests/test_phase8_6_reliability.py::test_6_database_rollback PASSED
outgraph/tests/test_phase8_6_reliability.py::test_7_no_duplicate_recommendations PASSED
outgraph/tests/test_phase8_6_reliability.py::test_8_no_duplicate_entities PASSED
outgraph/tests/test_phase8_6_reliability.py::test_9_system_status_degraded_when_subsystem_fails PASSED
outgraph/tests/test_phase8_6_reliability.py::test_10_error_state_never_accepts PASSED
outgraph/tests/test_phase8_6_reliability.py::test_11_large_data_safety_boundary PASSED
outgraph/tests/test_phase8_6_reliability.py::test_12_path_traversal_protection PASSED
outgraph/tests/test_phase8_6_reliability.py::test_13_force_accept_protection PASSED
outgraph/tests/test_phase8_6_reliability.py::test_14_synthetic_provenance_protection PASSED
outgraph/tests/test_phase8_6_reliability.py::test_15_uncertainty_override_protection PASSED
outgraph/tests/test_phase8_6_reliability.py::test_16_system_health_and_subsystem_reporting PASSED
outgraph/tests/test_phase8_6_reliability.py::test_17_raw_data_integrity PASSED

======================= 17 passed in 2.94s =======================
```

---

## 8. Limitations & Production Deployment Status

> [!WARNING]
> **DEPLOYMENT ARCHITECTURE DOCUMENTED — PRODUCTION DEPLOYMENT NOT VALIDATED**
> While local process execution, container boundaries, and API reliability have been hardened, high-concurrency production flight operations in a cloud or ground-station downlink pipeline have **not been evaluated**.

**Explicit Scientific Disclaimers:**
1. Fast API response times do **not** imply real-world physical correspondence validity.
2. `REAL-DATA ACCURACY = N/A` remains strictly preserved.
3. `POTENTIALLY_REDUCES_UNCERTAINTY` is the sole epistemic basis for active recommendations; real-time spacecraft tasking is **not** supported.
