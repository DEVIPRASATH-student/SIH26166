# Phase 8.2 Unified Backend / API Integration Report
**System:** LunarSynapse — Physics-Aware, Self-Evolving Multi-Modal Lunar World Model  
**Project:** SIH26166 — Multi-modal, Sun-angle and Scale Invariant Image Correspondence using Chandrayaan-2 OHRC, TMC-2, and IIRS  
**Stage:** Phase 8.2 (Unified Backend / API Integration)  
**Execution Timestamp:** 2026-09-24T20:15:00+05:30  
**Status:** `PHASE8_2_API_INTEGRATED_VALIDATED`  

---

## 1. Executive Summary

Phase 8.2 successfully integrates the complete 15-step scientific pipeline from Phase 8.1 (`PipelineController`) into the FastAPI backend service layer.

The API serves as the single unified, validated, explainable, and tamper-resistant entry point for:
$$\text{Observation Ingestion} \to \text{Correspondence Analysis} \to \text{Physical Verification} \to \text{Multi-Pillar Evidence} \to \text{Uncertainty Quantification} \to \text{World Model Association} \to \text{Knowledge Gap Detection} \to \text{Next-Best Observation Targeting} \to \text{Explainable Decision}$$

### Key Architectural Deliverables:
1. **PipelineController Invocation at API Boundary:** `POST /api/correspondence/analyze` directly executes `PipelineController`, coordinating feature matching, RANSAC homography, SPICE GroundGrids, SLDEM2015 DEM elevation interpolation, pushbroom parallax ray-casting, Gates 1–6, multi-pillar evidence fusion, epistemic uncertainty quantification, persistent entity resolution, WorldGraph synchronization, knowledge gap scanning, and Expected Information Gain recommendations.
2. **Dedicated Physical Verification Domain:** Created `/api/physical-verification` exposing the six physical gates (`GATE1` through `GATE6`), failure criteria, thresholds, and detailed evaluation status for each correspondence pair.
3. **Dedicated Multi-Dimensional Evidence Domain:** Created `/api/evidence` exposing all 11 evidence dimensions with explicit `missing_evidence` tracking and preservation of the `UNKNOWN != NEGATIVE` invariant.
4. **Comprehensive Security & Guardrail Enforcement:**
   - **No Physical Bypass:** Attempting to bypass physical checks via parameters like `force_accept=true` is rejected with `HTTP 400 Bad Request`.
   - **Synthetic-to-Real Conversion Guardrail:** Clients cannot declare an arbitrary observation as `is_synthetic=False` without authenticated raw flight data (`HTTP 400 Bad Request`).
   - **Uncertainty Tampering Guardrail:** Client attempts to overwrite computed scientific uncertainty are rejected with `HTTP 403 Forbidden`.
   - **Payload Availability Fallback:** Requests for offline or unsupported instruments return `payload_status: PAYLOAD_UNAVAILABLE` without unhandled server exceptions.
   - **Language Guardrail:** Next-Best-Observation proposals strictly state `POTENTIALLY_REDUCES_UNCERTAINTY` and never `WILL_RESOLVE`.
5. **Full Repository Regression:** **327 passed, 0 failed** in 108.81s (100% pass rate across Phase 1 to Phase 8.2).
6. **Raw Lunar Data Immutability:** Exactly **0 bytes modified** in `data/real/`.

---

## 2. API Endpoints Specification

### 2.1 Observations Domain (`/api/observations`)
| HTTP Method | Route | Description | Validation & Safety Behavior |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/observations` | Ingests or registers observations with coordinates, sensor, and provenance. | Rejects `is_synthetic=False` if not backed by real flight data. Validates lat $[-90, 90]$ and lon $[-180, 360]$. |
| `GET` | `/api/observations/{id}` | Retrieves full flight/synthetic metadata for an observation. | Exposes `footprint`, `solar_geometry`, `spacecraft_geometry`, and `data_provenance`. |
| `GET` | `/api/observations` | Lists all registered observations in the system. | Idempotent read. |
| `POST` | `/api/observations/ingest` | Ingests authentic PDS4 Chandrayaan-2/LROC/SELENE data from disk. | Uses `ProductIngestionEngine`. |

### 2.2 Correspondence Domain (`/api/correspondence`)
| HTTP Method | Route | Description | Validation & Safety Behavior |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/correspondence/analyze` | Executes feature extraction, matching, and physical verification via `PipelineController`. | Rejects `force_accept=True` with `HTTP 400`. Validates observation IDs (404 if missing) and matcher algorithm (400 if unsupported). |
| `GET` | `/api/correspondence` | Lists all evaluated correspondence pairs. | Returns enriched metadata, evidence profiles, and gate summaries. |
| `GET` | `/api/correspondence/{id}` | Retrieves detailed correspondence record by ID. | Returns inliers, rejection reasons, uncertainty, and physical gate status. |

### 2.3 Physical Verification Domain (`/api/physical-verification`)
| HTTP Method | Route | Description | Validation & Safety Behavior |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/physical-verification/gates` | Exposes catalog, definitions, and thresholds for Gates 1–6. | Read-only scientific specification. |
| `GET` | `/api/physical-verification/{id}` | Returns Six-Gate evaluation status for a correspondence task. | Returns PASS / REJECTED / NOT_EVALUATED for each gate with physical explanation. |

### 2.4 Evidence Domain (`/api/evidence`)
| HTTP Method | Route | Description | Validation & Safety Behavior |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/evidence/dimensions` | Exposes all 11 scientific evidence dimensions and policy. | Reasserts `UNKNOWN != NEGATIVE`. |
| `GET` | `/api/evidence/{id}` | Returns multi-dimensional score profile for a correspondence. | Explicitly lists missing dimensions without converting them to negative evidence. |

### 2.5 Uncertainty Domain (`/api/uncertainty`)
| HTTP Method | Route | Description | Validation & Safety Behavior |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/uncertainty/summary` | Exposes system-wide epistemic/aleatoric metrics and limitations. | Reasserts real-lunar calibration limitation and $>4\text{ px}$ saturation limit. |
| `GET` | `/api/uncertainty/{id}` | Returns scalar, interval, covariance proxy, and qualitative semantics. | Preserves uncertainty semantics. |
| `POST` | `/api/uncertainty/override` | Intercepts client attempt to overwrite computed uncertainty. | Strictly returns `HTTP 403 Forbidden`. |

### 2.6 Knowledge Gaps Domain (`/api/knowledge-gaps`)
| HTTP Method | Route | Description | Validation & Safety Behavior |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/knowledge-gaps/types` | Lists the 8 supported epistemic gap taxonomies. | Read-only taxonomy list. |
| `GET` | `/api/knowledge-gaps` | Lists all active knowledge gaps in the world model. | Idempotent list. |
| `GET` | `/api/knowledge-gaps/{id}` | Retrieves specific gap by ID. | Returns 404 if gap ID is unknown. |

### 2.7 Recommendations Domain (`/api/recommendations`)
| HTTP Method | Route | Description | Validation & Safety Behavior |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/recommendations` | Lists active Next-Best-Observation proposals. | Read-only query. |
| `GET` | `/api/recommendations/{id}` | Retrieves specific recommendation by ID. | Returns 404 if recommendation ID is unknown. |
| `POST` | `/api/recommendations/next-observation` | Calculates Expected Information Gain and ranks sensors. | Enforces `POTENTIALLY_REDUCES_UNCERTAINTY`. Returns `PAYLOAD_UNAVAILABLE` if sensor is offline. |

### 2.8 System Diagnostics Domain (`/api/system`)
| HTTP Method | Route | Description | Validation & Safety Behavior |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/system/health` | Operational health check, DB ping, and ML backend readiness. | Safe diagnostics without exposing secrets. |
| `GET` | `/api/system/status` | Complete subsystem status (DEM, GroundGrids, raw data integrity). | Validates SLDEM2015 DEM, SPICE grids, and 0-byte raw data integrity. |

---

## 3. Scientific Invariants & Guardrails Ledger

| Guardrail Invariant | Enforced in Phase 8.2 API? | Verification Evidence |
| :--- | :--- | :--- |
| **NO PHYSICAL GATE BYPASS** | **ENFORCED** | `test_no_physical_gate_bypass`: `force_accept=True` returns `HTTP 400 Bad Request`. |
| **SYNTHETIC-REAL ISOLATION** | **ENFORCED** | `test_synthetic_real_separation`: Arbitrary `is_synthetic=False` returns `HTTP 400 Bad Request`. |
| **UNCERTAINTY TAMPERING PREVENTION** | **ENFORCED** | `test_invalid_uncertainty`: `POST /api/uncertainty/override` returns `HTTP 403 Forbidden`. |
| **PHYSICAL CORRESPONDENCE NOT VALIDATED** | **PRESERVED** | Real OHRC/TMC-2 negative control returns `status=REJECTED`, Gate 3 `REJECTED`, and includes limitation. |
| **REAL-DATA ACCURACY = N/A** | **PRESERVED** | Preserved unconditionally in `scientific_limitations` and API responses. |
| **UNKNOWN != NEGATIVE** | **PRESERVED** | Featureless terrain evaluates to `UNKNOWN`/`INSUFFICIENT_EVIDENCE` without asserting feature non-existence. |
| **FAILED CORRESPONDENCE != NEGATIVE ENTITY EVIDENCE** | **PRESERVED** | Real negative control correspondence rejection preserves persistent lunar entity. |
| **ENTITY ASSOCIATION != DIRECT CORRESPONDENCE** | **PRESERVED** | Associating observations to a shared lunar entity does not assert image correspondence. |
| **POTENTIALLY_REDUCES_UNCERTAINTY LANGUAGE** | **PRESERVED** | `test_potentially_reduces_uncertainty_language`: All NBO responses use this exact phrase; `WILL_RESOLVE` is forbidden. |
| **PAYLOAD_UNAVAILABLE HANDLING** | **PRESERVED** | `test_payload_unavailable`: Requests for offline payloads return `PAYLOAD_UNAVAILABLE` without crash. |

---

## 4. Test Verification Results

### 4.1 Targeted API Integration Tests (`test_phase8_2_api_integration.py`)
- Total tests: **20**
- Passed: **20**
- Failed: **0**
- Skipped: **0**
- Runtime: **26.55s**

| Test Case | Objective | Result |
| :--- | :--- | :--- |
| `test_health_endpoint` | Verifies `/api/system/health` and `/api/system/status` | **PASSED** |
| `test_real_observation_retrieval` | Ingests and inspects authentic real lunar observation | **PASSED** |
| `test_synthetic_observation_provenance` | Tests synthetic creation and explicit provenance tracking | **PASSED** |
| `test_correspondence_api_real_negative_control` | Exercises Scenario A (OHRC/TMC-2 Gate 3 rejection) | **PASSED** |
| `test_correspondence_api_synthetic_positive_control` | Exercises Scenario B (Synthetic controlled positive control) | **PASSED** |
| `test_physical_gate_results_exposed` | Verifies exposure of Gates 1–6 in API responses | **PASSED** |
| `test_unknown_state_preserved` | Exercises Scenario C (Featureless terrain evaluated to UNKNOWN) | **PASSED** |
| `test_contradictory_evidence_preserved` | Exercises Scenario D (Opposing illumination conflict) | **PASSED** |
| `test_entity_correspondence_non_transitivity` | Verifies non-transitivity guardrail across world model | **PASSED** |
| `test_knowledge_gap_api` | Verifies gap listing, 8 taxonomies, and 404 on missing ID | **PASSED** |
| `test_recommendation_api` | Tests NBO Expected Information Gain recommendation generation | **PASSED** |
| `test_potentially_reduces_uncertainty_language` | Validates strict reduction basis and absence of `WILL_RESOLVE` | **PASSED** |
| `test_payload_unavailable` | Tests graceful handling when instrument is offline | **PASSED** |
| `test_invalid_request` | Tests Pydantic rejection of out-of-bounds parameters (HTTP 422) | **PASSED** |
| `test_missing_observation` | Tests HTTP 404 response on nonexistent observation ID | **PASSED** |
| `test_invalid_uncertainty` | Tests HTTP 403 Forbidden on client uncertainty tampering | **PASSED** |
| `test_synthetic_real_separation` | Tests HTTP 400 Bad Request on false real-data claims | **PASSED** |
| `test_no_physical_gate_bypass` | Tests rejection of `force_accept=True` bypass attempts | **PASSED** |
| `test_duplicate_processing` | Tests idempotent re-execution without duplicate entity creation | **PASSED** |
| `test_explanation_matches_decision` | Validates that human explanation card matches machine status | **PASSED** |

### 4.2 Full Repository Regression
- Test collection: **327 items** (307 Phase 8.1 baseline + 20 Phase 8.2 API tests)
- Passed: **327**
- Failed: **0**
- Runtime: **108.81s**
- Pass rate: **100.0%**

---

## 5. Artifact Changes & Production Ledger

### Files Created:
1. `outgraph/backend/app/schemas/physical_verification.py` — Pydantic schemas for physical verification results and Six-Gate catalog.
2. `outgraph/backend/app/api/routes/physical_verification.py` — API routes for `/physical-verification/gates` and `/{id}`.
3. `outgraph/backend/app/api/routes/evidence.py` — API routes for `/evidence/dimensions` and `/{id}`.
4. `outgraph/tests/test_phase8_2_api_integration.py` — 20 rigorous HTTP API integration tests.
5. `results/phase8_2_api_results.json` — Structured JSON test results and scenario metrics.
6. `docs/PHASE8_2_API_INTEGRATION_REPORT.md` — This official report.

### Files Modified:
1. `outgraph/backend/app/schemas/observation.py` — Added footprint, solar/spacecraft geometry, and data provenance fields.
2. `outgraph/backend/app/schemas/correspondence.py` — Added Phase 8.2 top-level and grouped contract fields; added `force_accept` parameter for interception.
3. `outgraph/backend/app/schemas/evidence.py` — Added `EvidenceDetailResponse`.
4. `outgraph/backend/app/schemas/knowledge.py` — Added `SystemStatusResponse`; added requirements and provenance to `RecommendationResponse`.
5. `outgraph/backend/app/schemas/system.py` — Exported `SystemStatusResponse`.
6. `outgraph/backend/app/schemas/__init__.py` — Exported new schema models.
7. `outgraph/backend/app/api/routes/observations.py` — Added `POST /api/observations` with synthetic validation and safe fallback array generation.
8. `outgraph/backend/app/api/routes/correspondence.py` — Replaced internal stub with `PipelineController` execution, gate mapping, and bypass rejection.
9. `outgraph/backend/app/api/routes/knowledge.py` — Added `GET /knowledge-gaps/{gap_id}` and `GET /knowledge-gaps/types`.
10. `outgraph/backend/app/api/routes/recommendation.py` — Added `GET /recommendations`, `GET /recommendations/{id}`, and `PAYLOAD_UNAVAILABLE` fallback.
11. `outgraph/backend/app/api/routes/uncertainty.py` — Added `GET /uncertainty/{id}` and `POST /uncertainty/override` (403 Forbidden).
12. `outgraph/backend/app/api/routes/system.py` — Added `GET /system/status` verifying DEM, GroundGrid, and raw data integrity.
13. `outgraph/backend/app/api/routes/__init__.py` — Exported new routers.
14. `outgraph/backend/app/main.py` — Registered `physical_verification_router` and `evidence_router` with and without `/api` prefix.
15. `outgraph/backend/app/services/pipeline_service.py` — Added `"decision"` to explanation card.

### Raw Data Modification:
- `data/real/`: **0 bytes modified** (Verified via git status: clean).

---

## 6. Scientific Limitations & Invariants

1. **Independent Real Tie-Point Absence:** Real-data accuracy remains categorized strictly as `N/A`.
2. **Physical Footprint Separation:** Calibrated Chandrayaan-2 OHRC and TMC-2 products are separated by $1.49 - 2.04\text{ km}$; visual feature hypotheses are rejected at Gate 3.
3. **No Invariance Claims:** Universal sun-angle, scale, or sensor invariance is explicitly disclaimed.
4. **Saturation Boundary:** Feature dispersion uncertainty saturates at $>4\text{ px}$.
5. **No Spacecraft Tasking Simulation:** Active recommendations identify required observation characteristics but do not simulate orbital trajectory mechanics.

---

## 7. Next Phase Recommendation

Phase 8.2 is completely validated.  
**Recommended Next Stage:** **Phase 8.3 (Demonstration UI / Frontend)** upon explicit user authorization.
