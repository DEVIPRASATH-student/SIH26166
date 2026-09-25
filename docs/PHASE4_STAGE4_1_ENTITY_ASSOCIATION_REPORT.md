# PHASE 4 STAGE 4.1 REPORT: OBSERVATION → ENTITY ASSOCIATION
**Project:** LunarSynapse (SIH 26166)  
**Date:** September 2026  
**Status:** COMPLETE & VERIFIED  
**Stage:** 4.1 — Observation to Entity Association Engine

---

## 1. Objective

The objective of Stage 4.1 is to establish a rigorous, persistent mechanism for associating multi-sensor lunar observations with persistent physical lunar entities (e.g., impact craters, boulder fields, ridges, rilles, terrain regions, albedo features, spectral anomalies).

Crucially, the association mechanism must:
1. Prevent false or ungrounded associations across non-overlapping or geometrically incompatible observations (such as the disjoint OHRC and TMC-2 products identified in Phase 3).
2. Explicitly distinguish confirmed physical entities from candidates, unvalidated associations, and rejected associations.
3. Preserve full provenance (source observation ID, sensor, processing stage, method, timestamp, notes).
4. Update entity lifecycle states dynamically upon the accumulation or contradiction of evidence.

---

## 2. Implementation Overview

The entity engine is implemented in [`outgraph/ml/world_model/entity.py`](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/outgraph/ml/world_model/entity.py).

### 2.1 Entity States
- `CANDIDATE`: Proposed lunar feature with preliminary or single-sensor detection.
- `SUPPORTED`: Feature corroborated by at least one validated observation.
- `CONFIRMED`: Feature independently corroborated by multiple consistent observations or modalities.
- `CONTRADICTED`: Feature possessing incompatible or contradictory observations.
- `REJECTED`: Feature evaluated and rejected due to spatial, physical, or geometric incompatibility.
- `UNKNOWN`: Insufficient information to classify entity status.

### 2.2 Association Types & Statuses
- **Association Types:** `DIRECT`, `GEOMETRIC`, `MULTIMODAL`, `TEMPORAL`, `HYPOTHESIZED`, `UNVALIDATED`, `REJECTED`, `UNKNOWN`.
- **Association Statuses:** `SUPPORTED`, `CONTRADICTED`, `UNVALIDATED`, `INSUFFICIENT_EVIDENCE`, `REJECTED`, `UNKNOWN`, `NOT_APPLICABLE`.

### 2.3 Spatial Gating & Rejection
The [`EntityResolver`](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/outgraph/ml/world_model/entity.py#L136-L235) computes lunar great-circle Haversine distances:
$$d = 2 R_{\text{Moon}} \arcsin\left(\sqrt{\sin^2\left(\frac{\Delta \phi}{2}\right) + \cos(\phi_1)\cos(\phi_2)\sin^2\left(\frac{\Delta \lambda}{2}\right)}\right)$$
with $R_{\text{Moon}} = 1,737,400.0\text{ m}$.
If the distance between the entity center and the observation exceeds the spatial tolerance (default $200.0\text{ m}$), or if physical geometry dictates non-overlap (e.g. `GATE3_TARGET_OUTSIDE_CALIBRATED_SWATH`), the association is marked `REJECTED` with an explicit rejection reason rather than fabricating correspondence.

---

## 3. Verification & Test Results

The test suite in [`outgraph/tests/test_entity_association.py`](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/outgraph/tests/test_entity_association.py) validated:
1. `test_valid_entity_creation`: Confirms correct entity instantiation with properties and initial `CANDIDATE` state.
2. `test_valid_observation_association`: Validates association within spatial tolerance, updating entity state to `SUPPORTED`.
3. `test_duplicate_association_handling`: Verifies deterministic updating of existing associations without duplicate record leakage.
4. `test_rejected_association_due_to_distance`: Asserts that an observation $\sim 1.7\text{ km}$ away is strictly `REJECTED` (`SPATIAL_DISTANCE_EXCEEDS_TOLERANCE`).
5. `test_forced_rejection_with_reason`: Asserts explicit rejection carrying Phase 3 gate error reasons (`GATE3_TARGET_OUTSIDE_CALIBRATED_SWATH`).
6. `test_provenance_preservation`: Confirms immutable association provenance tracking.
7. `test_multimodal_confirmation_state`: Verifies multi-observation promotion to `CONFIRMED`.

**Test Result:** 7 passed, 0 failed.
Baseline 97 tests remain completely untouched and green. Total test count: $97 + 7 = 104$.
