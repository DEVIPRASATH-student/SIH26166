# PHASE 4 INITIAL AUDIT: READ-ONLY SYSTEM INSPECTION
**Project:** LunarSynapse (SIH 26166)  
**Date:** September 2026  
**Auditor:** Automated Scientific Gatekeeper (Phase 4 Initialization)  
**Status:** COMPLETE (READ-ONLY AUDIT)

---

## 1. Executive Summary

A comprehensive read-only audit of the LunarSynapse codebase was conducted prior to beginning Phase 4 implementation. The repository currently possesses a fully verified 97-test passing baseline covering Phases 0, 1, 2, 2.5, 2.5.1, and Phase 3 (Stages 3.1–3.7).

The goal of Phase 4 is to transition LunarSynapse from an episodic correspondence and geometry evaluation engine into a **Physics-Aware Persistent Lunar World Model**. This world model must explicitly maintain lunar observations, persistent lunar entities, multimodal evidence, hypotheses, contradictions, uncertainty, knowledge gaps, and recommended next observations without fabricating correspondence or confusing missing information with negative evidence.

Crucially, Phase 3 demonstrated that the selected real Chandrayaan-2 OHRC and TMC-2 products in `data/real/` have physically disjoint ground footprints (separated by $1.49 - 2.05\text{ km}$ on the reference datum, with max relief displacement $\le 246.4\text{ m}$). Phase 4 **must preserve this non-overlap finding** (`PHYSICAL CORRESPONDENCE NOT VALIDATED`) and represent the physical rejection as a scientific fact rather than forcing a synthetic match or corrupting the graph.

---

## 2. Inventory of Existing Implementations

### A. Observation Models
- **In-Memory ML Representation:** [`outgraph/ml/data/models.py`](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/outgraph/ml/data/models.py)
  - `LunarProduct`: Master container holding raster data, metadata, provenance, and validation.
  - `ProductMetadata`: Structured metadata distinguishing `KNOWN`, `UNKNOWN`, and `DERIVED` via `ValueStatus`.
  - `GeographicBounds`, `SolarIllumination`, `ViewingGeometry`, `BandInfo`.
  - `NOMINAL_REFERENCE_SPECS`: Guardrailed reference specs prevented from overwriting missing product data.
- **Relational Database Model:** [`outgraph/backend/app/models/observation.py`](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/outgraph/backend/app/models/observation.py)
  - `ObservationModel`: Persists sensor type, geodetic footprint bounds, solar angles, spatial resolution, and JSON metadata / provenance.

### B. Entity Models
- **Relational Database Model:** [`outgraph/backend/app/models/lunar_entity.py`](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/outgraph/backend/app/models/lunar_entity.py)
  - `LunarEntityModel`: Stores `entity_id`, `entity_type` (crater, boulder, ridge), coordinates, spatial extent, morphology, elevation, and spectral JSON.
  - `EntityObservationModel`: Associates `entity_id` to `observation_id` with sensor type and attachment confidence.
  - `WorldModelHypothesisModel`: Stores multi-modal properties with confidence, uncertainty, supporting evidence, and conflicting evidence JSON.
- **Entity Service:** [`outgraph/backend/app/services/entity_service.py`](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/outgraph/backend/app/services/entity_service.py)
  - Provides spatial entity resolution (`resolve_entity`) using a geodetic spatial threshold ($\approx 0.005^\circ$).
  - Initializes baseline morphology, terrain, and spectral hypotheses.

### C. Graph Model & NetworkX Infrastructure
- **NetworkX Graph Engine:** [`outgraph/backend/app/services/graph_service.py`](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/outgraph/backend/app/services/graph_service.py)
  - Uses `networkx.DiGraph`.
  - Node types present: `LunarEntity`, `Observation`, `Sensor`, `PhysicsEvidence`, `Hypothesis`.
  - Edge relations present: `ACQUIRED_BY`, `OBSERVED_BY`, `MATCHED_WITH`, `EVALUATED_BY`, `VERIFIES`, `BELIEVES`.
  - Converts directed graph to layered React Flow coordinates for UI visualization.

### D. Uncertainty Quantification Engine
- **ML Uncertainty Module:** [`outgraph/ml/uncertainty/uncertainty_engine.py`](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/outgraph/ml/uncertainty/uncertainty_engine.py)
  - `UncertaintyEngine`: Computes multi-factor uncertainty from physics evidence profiles:
    1. Evidence divergence (cross-module variance)
    2. Geometric instability (reprojection error and condition number)
    3. Feature ambiguity ($1.0 - \text{inlier\_ratio}$)
    4. Spatial sparsity (spatial keypoint distribution)
  - Decomposes into calibrated status: `CALIBRATED_LOW_UNCERTAINTY`, `HIGH_EPISTEMIC_RISK`, `GEOMETRIC_ALEATORIC_NOISE`, `MODERATE_UNCERTAINTY`.

### E. Provenance Tracking
- **ML Provenance Tracker:** [`outgraph/ml/data/provenance/tracker.py`](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/outgraph/ml/data/provenance/tracker.py)
  - `ProvenanceTracker`: Records file path, SHA-256 hashes, source name, timestamp, and processing history entries.

### F. Knowledge Gaps & Recommendations
- **Database Models:** [`outgraph/backend/app/models/recommendation.py`](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/outgraph/backend/app/models/recommendation.py)
  - `KnowledgeGapModel`: Tracks blind spots (`MISSING_SPECTRAL_EVIDENCE`, `HIGH_ILLUMINATION_UNCERTAINTY`, `UNVERIFIED_TERRAIN_RELATION`).
  - `RecommendationModel`: Stores sensor recommendation, expected information gain, and uncertainty reduction.
- **Services & Routes:**
  - `KnowledgeGapService` (`backend/app/services/knowledge_gap_service.py`)
  - `RecommendationService` (`backend/app/services/recommendation_service.py`)
  - API routes: `/api/knowledge-gaps`, `/api/recommendations/next-observation`

### G. Phase 3 Calibrated Geometry Infrastructure (Untouchable Base)
- `GroundGrid`: Inverts and projects via calibrated `_g_grd_d18.csv`.
- `DEMInterface`: Bilinear sampling of real SLDEM2015 PDS data.
- `TerrainGeometry`: DEM-aware coordinate mapping.
- `ParallaxModel`: Pushbroom optical relief displacement.
- `TargetCorridorCalculator`: Elevation-bounded target corridor intervals.
- `PhysicalCandidateEngine`: 6-gate physical candidate engine rejecting non-overlapping footprints.

---

## 3. Analysis: Reusable Components vs. Missing Components

| World Model Requirement | Existing Component | Gap / Missing Component for Phase 4 |
|---|---|---|
| **Entity States** | Basic string in database | Missing explicit typed state machine (`CANDIDATE`, `SUPPORTED`, `CONFIRMED`, `CONTRADICTED`, `REJECTED`, `UNKNOWN`). |
| **Observation Association** | Basic `EntityObservationModel` | Lacks association types (`DIRECT`, `GEOMETRIC`, `MULTIMODAL`, `TEMPORAL`, `HYPOTHESIZED`, `UNVALIDATED`, `REJECTED`, `UNKNOWN`, `INSUFFICIENT_EVIDENCE`), explicit method, provenance record, and rejection guard. |
| **Structured Evidence** | `CorrespondenceEvidenceModel` (pairwise) | No multimodal evidence abstraction at the entity level supporting `GEOMETRIC`, `TERRAIN`, `ILLUMINATION`, `SPECTRAL`, `SCALE`, `TEMPORAL`, `TEXTURE`, `REGISTRATION`, `PHYSICAL`, `MANUAL`, `SYNTHETIC` with states `SUPPORTED`, `CONTRADICTED`, `UNVALIDATED`, `INSUFFICIENT_EVIDENCE`, `NOT_APPLICABLE`. |
| **World Graph** | `GraphService` in backend | Lacks standalone ML-level graph representation supporting standardized nodes (`ENTITY`, `OBSERVATION`, `EVIDENCE`, `HYPOTHESIS`, `KNOWLEDGE_GAP`, `RECOMMENDATION`) and edges (`OBSERVES`, `ASSOCIATED_WITH`, `SUPPORTED_BY`, `CONTRADICTED_BY`, `DERIVED_FROM`, `TEMPORALLY_RELATED`, `SPATIALLY_RELATED`, `HYPOTHESIZES`, `HAS_UNCERTAINTY`, `HAS_GAP`, `RECOMMENDS`), deterministic serialization, and graph connectivity guardrails. |
| **Physical Uncertainty Propagation** | Pairwise `UncertaintyEngine` | Needs explicit propagation connecting Phase 3 GroundGrid, DEM sampling resolution, elevation range, parallax bounds, and corridor width into entity association and hypothesis uncertainty. |
| **Knowledge-Gap Detection** | Hardcoded heuristics in `KnowledgeGapService` | Needs comprehensive gap engine supporting `MISSING_MODALITY`, `MISSING_TEMPORAL_OBSERVATION`, `MISSING_GEOMETRIC_VALIDATION`, `MISSING_TERRAIN_VALIDATION`, `MISSING_SPECTRAL_VALIDATION`, `INSUFFICIENT_CORRESPONDENCE`, `FOOTPRINT_NON_OVERLAP`, `UNCERTAINTY_TOO_HIGH` with blocking reasons. |
| **Next-Best Observation** | Numerical heuristic in `RecommendationService` | Must guard against fabricated numerical scores when unjustified; use qualitative classification (`HIGH_POTENTIAL`, `MEDIUM_POTENTIAL`, `LOW_POTENTIAL`, `UNKNOWN`) and strict `POTENTIALLY_REDUCES_UNCERTAINTY` language. |
| **Real-Data Rejection Flow** | Evaluated in Stage 3.6 script | No end-to-end world model demonstration representing OHRC $\to$ real terrain $\to$ candidate physical relation $\to$ physical rejection $\to$ `FOOTPRINT_NON_OVERLAP` knowledge gap $\to$ next-best observation recommendation. |

---

## 4. Proposed Architectural Design for Phase 4

To preserve all existing database schemas, API routes, and 97 passing tests without risk of regression, Phase 4 will establish a clean, dedicated scientific domain package:
`outgraph/ml/world_model/`
- [`outgraph/ml/world_model/entity.py`](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/outgraph/ml/world_model/entity.py): Pure Python dataclasses / Pydantic models for persistent lunar entities and observation associations with explicit provenance and rejection enforcement.
- [`outgraph/ml/world_model/evidence.py`](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/outgraph/ml/world_model/evidence.py): Multimodal evidence model supporting 11 evidence types, 5 evidence statuses, measurements, units, uncertainty, and provenance.
- [`outgraph/ml/world_model/graph.py`](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/outgraph/ml/world_model/graph.py): NetworkX-based World Model Entity Graph with typed nodes and edges, edge provenance, serialization/deserialization, and non-transitivity guardrail.
- [`outgraph/ml/world_model/uncertainty.py`](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/outgraph/ml/world_model/uncertainty.py): Physical uncertainty propagation engine (scalar, interval/bounds, qualitative, `UNKNOWN`).
- [`outgraph/ml/world_model/knowledge_gap.py`](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/outgraph/ml/world_model/knowledge_gap.py): Evidence-driven knowledge-gap detection.
- [`outgraph/ml/world_model/next_best_observation.py`](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/outgraph/ml/world_model/next_best_observation.py): Evidence-driven next-best observation engine.
- [`outgraph/ml/world_model/world_model_engine.py`](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/outgraph/ml/world_model/world_model_engine.py): Unified facade orchestrating the entire lifecycle and real-data demonstrations.

The backend API services will be enriched or bridged to this scientific core while maintaining 100% backward compatibility for existing endpoints (`/api/entities`, `/api/knowledge-gaps`, `/api/recommendations/next-observation`, `/api/graph/full`).

---

## 5. Risks & Compatibility Considerations

1. **Risk of Breaking Existing 97 Tests:**
   - Any modifications to existing files (`outgraph/backend/app/models/*.py`, `outgraph/ml/geometry/*.py`) could break existing tests if signatures or table definitions change incompatibly.
   - *Mitigation:* Keep existing ORM models and services intact or perform only purely additive extensions. Build the Phase 4 scientific engine in `outgraph/ml/world_model/` and verify unit tests independently before integrating with API layer.
2. **Risk of Forcing OHRC $\leftrightarrow$ TMC-2 Correspondence:**
   - The demo mission in `test_api.py` uses synthetic observations where correspondence is verified. In contrast, real data has a $1.5 - 2.1\text{ km}$ footprint separation.
   - *Mitigation:* Explicitly support both synthetic demonstration mode (for existing API regression tests) and real-mission mode (which enforces `FOOTPRINT_NON_OVERLAP` rejection and generates corresponding knowledge gaps).
3. **Risk of Fabricated Information Gain / Uncertainty:**
   - Numerical scores must not be invented without physical basis.
   - *Mitigation:* Use qualitative ratings (`HIGH_POTENTIAL`, `MEDIUM_POTENTIAL`, etc.) and interval bounds wherever exact physical covariances are unavailable.

---

## 6. Audit Conclusion & Gate Approval

The repository is in a pristine, verified state (97 passed, 0 failed). Existing components are thoroughly documented. The implementation plan adheres strictly to the sequential scientific gates.

**Audit Status:** APPROVED FOR STAGE 4.1 EXECUTION.
