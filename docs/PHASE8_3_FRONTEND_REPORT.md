# Phase 8.3 Demonstration UI / Frontend Integration Report
**System:** LunarSynapse — Physics-Aware, Self-Evolving Multi-Modal Lunar World Model  
**Problem Statement:** SIH26166 — Multi-modal, Sun-angle and Scale Invariant Image Correspondence using Chandrayaan-2 OHRC, TMC-2, and IIRS  
**Stage:** Phase 8.3 (Demonstration UI / Frontend Integration)  
**Execution Timestamp:** 2026-09-24T22:20:00+05:30  
**Status:** `PHASE8_3_FRONTEND_INTEGRATED_VALIDATED`  

---

## 1. Executive Summary

Phase 8.3 delivers the SIH-ready demonstration frontend for LunarSynapse, built as a modern, high-fidelity, aerospace-grade mission operations dashboard with React 18, Vite 6, and TailwindCSS.

### Key Architectural Invariants Enforced:
1. **Strict Client-Server Decoupling:** The frontend connects exclusively to the validated Phase 8.2 FastAPI backend through a typed TypeScript HTTP client (`fetchJson`). The frontend does **not** directly execute Python scientific modules, run local computer vision scripts, or alter scientific thresholds.
2. **Deterministic Scientific Traceability:** Visualizations present exact backend pipeline states without fabrication. Real flight data and synthetic controlled simulations are separated with prominent visual badges.
3. **Dedicated Negative Control Panel:** Features a primary SIH benchmark showcase: Chandrayaan-2 OHRC vs TMC-2 negative control, demonstrating 26 candidate visual matches correctly halted by Gate 3 (`TARGET_OUTSIDE_CALIBRATED_SWATH`) and Gate 4 (`TARGET_CLAMPED_TO_SWATH_BOUNDARY`) due to a ~1.49 km - 2.04 km footprint separation.
4. **Dedicated Synthetic Positive Control Panel:** Demonstrates end-to-end pipeline convergence under controlled ground-truth conditions, prominently labeled with the mandatory disclaimer: *"This controlled synthetic result demonstrates pipeline behavior under known conditions. It does not establish real-lunar accuracy."*
5. **Six Kinematic Gates View:** Dedicated interactive engine detailing Gates 1 through 6 (`INVALID_SOURCE_GROUNDGRID`, `DEM_OUT_OF_BOUNDS_OR_NODATA`, `TARGET_OUTSIDE_CALIBRATED_SWATH`, `TARGET_CLAMPED_TO_SWATH_BOUNDARY`, `TARGET_OUTSIDE_ELEVATION_CORRIDOR`, `BIDIRECTIONAL_RESIDUAL_TOO_LARGE`).
6. **11 Orthogonal Evidence Dimensions:** Displays all 11 pillars with prominent preservation of `UNKNOWN != NEGATIVE` and explicit `missing_evidence` tracking.
7. **Uncertainty Quantification View:** Visualizes scalar uncertainty, 95% confidence interval, 2x2 covariance proxy matrix, qualitative epistemic risk, and decomposition, preserving the `>4 px` saturation limit and `REAL-LUNAR EMPIRICAL UNCERTAINTY CALIBRATION NOT ESTABLISHED`.
8. **Relational World Model View:** Interactive ReactFlow ontology graph displaying persistent entities, observation streams, evidence, and hypotheses, guarded by `ENTITY ASSOCIATION != DIRECT IMAGE CORRESPONDENCE` and `SPATIAL PROXIMITY != ENTITY IDENTITY`.
9. **Next-Best Observation Targeting:** Renders Expected Information Gain $E[\Delta I]$ proposals strictly preserving `POTENTIALLY_REDUCES_UNCERTAINTY` (never `WILL_RESOLVE` or `GUARANTEED`) with `PAYLOAD UNAVAILABLE` fallback.
10. **System Telemetry & Raw Data Integrity:** Consumes `/api/system/status` to render live subsystem health for API, database, DEM, GroundGrids, and verifies `0 bytes modified in data/real/`.
11. **SIH Presentation Mode:** A guided 6-stage presentation tour designed for the SIH evaluation jury.

---

## 2. Frontend Components Architecture

### 2.1 Navigation & Global Shell
- [src/components/TopHeader.tsx](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/outgraph/frontend/src/components/TopHeader.tsx): Displays project branding, SIH26166 badge, live subsystem health (`ONLINE` / `DEGRADED` / `UNAVAILABLE`), global Data Mode selector (`ALL` / `REAL` / `SYNTHETIC`), and quick launch for SIH Presentation Mode.
- [src/components/DisclaimerBanner.tsx](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/outgraph/frontend/src/components/DisclaimerBanner.tsx): Persistent sticky disclaimer banner highlighting:
  - `Physical Correspondence: NOT VALIDATED`
  - `Real-Data Accuracy: N/A`
  - `REAL-LUNAR EMPIRICAL UNCERTAINTY CALIBRATION NOT ESTABLISHED`
  - `UNKNOWN != NEGATIVE`
  - `RAW DATA: 0 BYTES MODIFIED`
- [src/components/Sidebar.tsx](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/outgraph/frontend/src/components/Sidebar.tsx): Primary navigation bar grouping the 11 scientific pipeline modules and secondary research labs with badge counters.

### 2.2 Core Scientific Views
| Module | Component File | Description & Guardrail Features |
| :--- | :--- | :--- |
| **1. Dashboard** | [src/pages/MissionOverview.tsx](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/outgraph/frontend/src/pages/MissionOverview.tsx) | Mission control metrics, 9-stage pipeline visualization with exact backend states (`READY`, `SUPPORTED`, `AMBIGUOUS`, `REJECTED`, `UNKNOWN`), and quick launch for Real Negative Control vs Synthetic Positive Control. |
| **2. Observations** | [src/pages/ObservationWorkspace.tsx](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/outgraph/frontend/src/pages/ObservationWorkspace.tsx) | PDS4 metadata viewer, astronomical ephemeris (sun azimuth, elevation, incidence, phase), anti-solar shadow vector, and prominent `REAL LUNAR DATA` vs `SYNTHETIC CONTROLLED DATA` badges. |
| **3. Correspondence** | [src/pages/CorrespondenceAnalysis.tsx](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/outgraph/frontend/src/pages/CorrespondenceAnalysis.tsx) | Side-by-side keypoint visualizer with SVG matching vectors, toggle between raw visual candidates and physics-verified inliers, and mandatory banner: `VISUAL CORRESPONDENCE = HYPOTHESIS` $\to$ `PHYSICAL VERIFICATION REQUIRED`. |
| **4. Negative Control Panel** | [src/components/RealNegativeControlPanel.tsx](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/outgraph/frontend/src/components/RealNegativeControlPanel.tsx) | Dedicated panel for Chandrayaan-2 OHRC vs TMC-2 negative control. Visual flow: 26 candidates $\to$ Homography degenerate $\to$ Gate 3/4 rejection $\to$ `FOOTPRINT_NON_OVERLAP` (~1.49 km - 2.04 km). Wording: *"Visual candidates exist, but the evaluated physical geometry does not support correspondence for this pair."* |
| **5. Physical Verification** | [src/pages/PhysicalVerificationPage.tsx](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/outgraph/frontend/src/pages/PhysicalVerificationPage.tsx) | Detailed Six-Gate kinematic engine (Gates 1–6) rendering status, threshold, observed value, and reason for each gate, demonstrating `VISUAL MATCH` $\to$ `PHYSICS` $\to$ `DECISION`. |
| **6. Evidence Dashboard** | [src/pages/EvidenceDashboard.tsx](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/outgraph/frontend/src/pages/EvidenceDashboard.tsx) | Visualizes 11 orthogonal evidence dimensions (`GEOMETRIC`, `TERRAIN`, `ILLUMINATION`, `SPECTRAL`, `SCALE`, `TEMPORAL`, `TEXTURE`, `REGISTRATION`, `PHYSICAL`, `MANUAL`, `SYNTHETIC`) with explicit preservation of `UNKNOWN != NEGATIVE`. |
| **7. Uncertainty View** | [src/pages/UncertaintyView.tsx](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/outgraph/frontend/src/pages/UncertaintyView.tsx) | Visualizes scalar uncertainty, 95% confidence interval, 2x2 covariance proxy matrix, qualitative epistemic risk (`LOW`, `MODERATE`, `HIGH`, `SATURATED`), epistemic decomposition factors, and `>4 px` saturation limit. |
| **8. World Model** | [src/pages/EntityGraph.tsx](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/outgraph/frontend/src/pages/EntityGraph.tsx) | Interactive ReactFlow graph with node telemetry inspector, enforcing `ENTITY ASSOCIATION != DIRECT IMAGE CORRESPONDENCE` and `SPATIAL PROXIMITY != ENTITY IDENTITY`. |
| **9. Knowledge Gaps** | [src/pages/KnowledgeGaps.tsx](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/outgraph/frontend/src/pages/KnowledgeGaps.tsx) | Epistemic blind-spot scanner supporting 8 taxonomies, explaining that knowledge gaps represent missing information, not failed entities. |
| **10. Next-Best Observation** | [src/pages/NextObservation.tsx](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/outgraph/frontend/src/pages/NextObservation.tsx) | Expected Information Gain $E[\Delta I]$ scheduler, strictly enforcing `POTENTIALLY_REDUCES_UNCERTAINTY` (never `WILL_RESOLVE`), with explicit `PAYLOAD UNAVAILABLE` handling. |
| **11. Positive Control Panel** | [src/components/SyntheticPositiveControlPanel.tsx](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/outgraph/frontend/src/components/SyntheticPositiveControlPanel.tsx) | Dedicated synthetic demonstration validating controlled affine warps and full pipeline pass under known conditions, preserving the isolation from real-data accuracy claims. |
| **12. System Status** | [src/pages/SystemStatusPage.tsx](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/outgraph/frontend/src/pages/SystemStatusPage.tsx) | Real-time diagnostics for API, database, PipelineController, SLDEM2015 DEM cache, SPICE GroundGrids, and raw data integrity (`0 bytes modified`). |
| **13. SIH Presentation Mode**| [src/pages/PresentationMode.tsx](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/outgraph/frontend/src/pages/PresentationMode.tsx) | Guided 6-stage presentation tour tailored for the SIH evaluation jury. |

---

## 3. Typed API Client Specifications

The typed client in [src/services/api.ts](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/outgraph/frontend/src/services/api.ts) exposes comprehensive functions mapping 1-to-1 with Phase 8.2 backend schemas:
- `getHealth()`: `GET /api/system/health` $\to$ `SystemHealth`
- `getSystemStatus()`: `GET /api/system/status` $\to$ `SystemStatus`
- `runDemoMission()`: `POST /api/demo/run` $\to$ `DemoMissionResponse`
- `getObservations()`: `GET /api/observations` $\to$ `Observation[]`
- `getObservation(id)`: `GET /api/observations/{id}` $\to$ `Observation`
- `getCorrespondences()`: `GET /api/correspondence` $\to$ `Correspondence[]`
- `getCorrespondence(id)`: `GET /api/correspondence/{id}` $\to$ `Correspondence`
- `analyzeCorrespondence(srcId, tgtId, algo, question)`: `POST /api/correspondence/analyze` $\to$ `Correspondence`
- `getPhysicalGates()`: `GET /api/physical-verification/gates` $\to$ `GateCatalogResponse`
- `getPhysicalVerification(id)`: `GET /api/physical-verification/{id}` $\to$ `PhysicalVerificationResponse`
- `getEvidenceDimensions()`: `GET /api/evidence/dimensions` $\to$ `{ dimensions: string[]; policy: string }`
- `getEvidence(id)`: `GET /api/evidence/{id}` $\to$ `EvidenceDetailResponse`
- `getUncertaintySummary()`: `GET /api/uncertainty/summary` $\to$ `UncertaintySummaryResponse`
- `getUncertainty(id)`: `GET /api/uncertainty/{id}` $\to$ `UncertaintyResponse`
- `getKnowledgeGapTypes()`: `GET /api/knowledge-gaps/types` $\to$ `{ supported_gap_types: string[]; description: string }`
- `getKnowledgeGaps()`: `GET /api/knowledge-gaps` $\to$ `KnowledgeGap[]`
- `getKnowledgeGap(id)`: `GET /api/knowledge-gaps/{id}` $\to$ `KnowledgeGap`
- `getRecommendations()`: `GET /api/recommendations` $\to$ `Recommendation[]`
- `getRecommendation(id)`: `GET /api/recommendations/{id}` $\to$ `Recommendation`
- `getNextObservation(entityId, question)`: `POST /api/recommendations/next-observation` $\to$ `Recommendation`
- `getEntities()`: `GET /api/entities` $\to$ `LunarEntity[]`
- `getEntityDetail(id)`: `GET /api/entities/{id}` $\to$ `EntityDetail`
- `getFullGraph()`: `GET /api/graph/full` $\to$ `{ nodes: any[]; edges: any[] }`
- `runRedTeam()`: `POST /api/red-team/run` $\to$ `RedTeamResponse`
- `getBenchmarks()`, `runBenchmarks()`: `/api/benchmark/...`
- `getPhase2Benchmark(pairId, matcher)`: `GET /api/benchmark/phase2`

---

## 4. Frontend Scientific Language Audit

A full automated scan was conducted across `outgraph/frontend/src/` for forbidden misleading marketing phrases:
- `"100% accurate"`: 0 occurrences
- `"perfect match"`: 0 occurrences
- `"guaranteed"`: 0 occurrences (only cited in disclaimer context)
- `"confirmed lunar match"`: 0 occurrences
- `"AI proved"`: 0 occurrences
- `"universally invariant"`: 0 occurrences
- `"real-time spacecraft tasking"`: 0 occurrences

All active recommendation and scheduling terminology strictly uses `POTENTIALLY_REDUCES_UNCERTAINTY`.

---

## 5. Verification and Test Results

### 5.1 Frontend Build Compilation
- **Command:** `npm run build` (`tsc && vite build`)
- **Exit Code:** `0`
- **TypeScript Errors:** `0`
- **Modules Transformed:** `1,778`
- **Output Artifacts:**
  - `dist/index.html`: 1.19 kB
  - `dist/assets/index-CAwDSt9r.css`: 41.99 kB
  - `dist/assets/index-CH_q-UEt.js`: 485.88 kB
- **Compilation Time:** 39.10 seconds

### 5.2 Backend Regression Suite
- **Command:** `pytest outgraph/tests/ -v`
- **Exit Code:** `0`
- **Total Tests:** 327
- **Passed:** **327 passed** (100%)
- **Failed:** **0 failed**
- **Errors:** **0 errors**
- **Runtime:** 126.24 seconds

### 5.3 Raw Data Immutability Verification
- **Command:** `pytest outgraph/tests/test_phase7_6_real_benchmark.py -k "test_real_data_files_exist_and_unmodified" -v`
- **Result:** `1 passed in 2.42s`
- **Bytes Modified:** Exactly **0 bytes modified** in `data/real/`.

---

## 6. Scientific Limitations Preserved

1. **No Real-Flight Ground Truth:** The project preserves `REAL-DATA ACCURACY = N/A` because no sub-meter ground truth rover or retroreflector network exists across the evaluated Chandrayaan-2 OHRC/TMC-2 footprints.
2. **Empirical Calibration Limit:** Preserves `REAL-LUNAR EMPIRICAL UNCERTAINTY CALIBRATION NOT ESTABLISHED`. Computed uncertainty is an analytical Bayesian proxy combining dispersion and evidence disagreement.
3. **Saturation Limit:** Sub-pixel dispersion uncertainty saturates deterministically above `>4.0 px` to prevent divergent estimators.
4. **Epistemic Invariance:** Preserves `UNKNOWN != NEGATIVE`. Unobserved sensors create knowledge gaps, never negative entity evidence.
5. **Relational Invariance:** Preserves `ENTITY ASSOCIATION != DIRECT IMAGE CORRESPONDENCE` and `SPATIAL PROXIMITY != ENTITY IDENTITY`.
6. **Tasking Limitation:** Next-best observation targeting calculates Expected Information Gain; it does not simulate orbital flight mechanics or command spacecraft execution.

---

## 7. Artifacts Created & Modified

### Artifacts Created:
- [outgraph/frontend/src/components/RealNegativeControlPanel.tsx](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/outgraph/frontend/src/components/RealNegativeControlPanel.tsx)
- [outgraph/frontend/src/components/SyntheticPositiveControlPanel.tsx](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/outgraph/frontend/src/components/SyntheticPositiveControlPanel.tsx)
- [outgraph/frontend/src/pages/PhysicalVerificationPage.tsx](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/outgraph/frontend/src/pages/PhysicalVerificationPage.tsx)
- [outgraph/frontend/src/pages/EvidenceDashboard.tsx](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/outgraph/frontend/src/pages/EvidenceDashboard.tsx)
- [outgraph/frontend/src/pages/UncertaintyView.tsx](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/outgraph/frontend/src/pages/UncertaintyView.tsx)
- [outgraph/frontend/src/pages/SystemStatusPage.tsx](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/outgraph/frontend/src/pages/SystemStatusPage.tsx)
- [outgraph/frontend/src/pages/PresentationMode.tsx](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/outgraph/frontend/src/pages/PresentationMode.tsx)
- [results/phase8_3_frontend_results.json](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/results/phase8_3_frontend_results.json)
- [docs/PHASE8_3_FRONTEND_REPORT.md](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/docs/PHASE8_3_FRONTEND_REPORT.md)

### Artifacts Modified:
- [outgraph/frontend/src/types/index.ts](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/outgraph/frontend/src/types/index.ts)
- [outgraph/frontend/src/services/api.ts](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/outgraph/frontend/src/services/api.ts)
- [outgraph/frontend/src/components/TopHeader.tsx](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/outgraph/frontend/src/components/TopHeader.tsx)
- [outgraph/frontend/src/components/DisclaimerBanner.tsx](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/outgraph/frontend/src/components/DisclaimerBanner.tsx)
- [outgraph/frontend/src/components/Sidebar.tsx](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/outgraph/frontend/src/components/Sidebar.tsx)
- [outgraph/frontend/src/pages/MissionOverview.tsx](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/outgraph/frontend/src/pages/MissionOverview.tsx)
- [outgraph/frontend/src/pages/ObservationWorkspace.tsx](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/outgraph/frontend/src/pages/ObservationWorkspace.tsx)
- [outgraph/frontend/src/pages/CorrespondenceAnalysis.tsx](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/outgraph/frontend/src/pages/CorrespondenceAnalysis.tsx)
- [outgraph/frontend/src/pages/EntityGraph.tsx](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/outgraph/frontend/src/pages/EntityGraph.tsx)
- [outgraph/frontend/src/pages/KnowledgeGaps.tsx](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/outgraph/frontend/src/pages/KnowledgeGaps.tsx)
- [outgraph/frontend/src/pages/NextObservation.tsx](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/outgraph/frontend/src/pages/NextObservation.tsx)
- [outgraph/frontend/src/App.tsx](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/outgraph/frontend/src/App.tsx)

---

## 8. Status and Next Phase Recommendation

Phase 8.3 is **100% COMPLETE** and formally verified.

- **Status Code:** `PHASE8_3_FRONTEND_INTEGRATED_VALIDATED`
- **Backend Modifications:** **0** (backend was untouched; Phase 8.2 API was 100% sufficient and preserved).
- **Raw Real Data Modifications:** **0 bytes**.
- **Phase 3 Status:** Preserved.
- **Phase 7 Claim Ledger Status:** Preserved.
- **Next Phase:** Phase 8.4 (Real + Synthetic Demonstration Scenarios) is ready for authorization.
