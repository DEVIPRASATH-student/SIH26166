# PHASE 4 STAGE 4.5 REPORT: KNOWLEDGE-GAP DETECTION ENGINE
**Project:** LunarSynapse (SIH 26166)  
**Date:** September 2026  
**Status:** COMPLETE & VERIFIED  
**Stage:** 4.5 — Evidence-Driven Epistemic Blind Spot Identification

---

## 1. Objective

Stage 4.5 implements the capability for the Lunar World Model to explicitly recognize what it does *not* know. A Knowledge Gap is a scientifically meaningful absence of evidence that prevents promoting a candidate entity or hypothesis to confirmed status.

Crucially:
- A knowledge gap is **never** interpreted as evidence that a feature does not exist.
- A physical correspondence rejection (such as the Phase 3 finding that OHRC and TMC-2 swaths do not overlap) is preserved as a `FOOTPRINT_NON_OVERLAP` knowledge gap with an explicit blocking reason, rather than an operational software error.

---

## 2. Implementation Overview

Implemented in [`outgraph/ml/world_model/knowledge_gap.py`](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/outgraph/ml/world_model/knowledge_gap.py).

### 2.1 Supported Knowledge Gap Categories
1. `MISSING_MODALITY`: Missing whole-modality sensor observation (e.g. lack of IIRS hyperspectral bands).
2. `MISSING_TEMPORAL_OBSERVATION`: Feature imaged only at a single epoch; phase angle and illumination dynamics unconstrained.
3. `MISSING_GEOMETRIC_VALIDATION`: Sub-meter boundary or crater diameter lacks independent geometric confirmation.
4. `MISSING_TERRAIN_VALIDATION`: Feature depth and slope profile lack 3D stereo or laser altimeter verification.
5. `MISSING_SPECTRAL_VALIDATION`: Surface composition (pyroxene, olivine, plagioclase) unconfirmed by spectral absorption spectra.
6. `INSUFFICIENT_CORRESPONDENCE`: Feature observed by only a single sensor without corroborating cross-sensor coverage.
7. `FOOTPRINT_NON_OVERLAP`: Physical sensor footprints are disjoint on the lunar surface (direct Phase 3 finding).
8. `UNCERTAINTY_TOO_HIGH`: Spatial or physical uncertainty bounds exceed scientific tolerance ($> 50.0\text{ m}$).

### 2.2 Gap Properties
Each [`KnowledgeGap`](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/outgraph/ml/world_model/knowledge_gap.py#L46-L60) encapsulates:
- `gap_id`, `entity_id`, `gap_type`, `description`
- `required_evidence`: Specific sensor or algorithmic evidence required to close the gap.
- `current_evidence`: Existing observations or rejection logs.
- `severity`: Impact rating (`HIGH`, `MEDIUM`, `LOW`, `UNKNOWN`).
- `blocking_reason`: Scientific or physical impediment (e.g. `PHYSICAL_FOOTPRINT_SEPARATION`).
- `provenance` and `status` (`OPEN`, `RESOLVED`, `BLOCKED`, `ACKNOWLEDGED`).

---

## 3. Verification & Test Results

The test suite in [`outgraph/tests/test_knowledge_gap.py`](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/outgraph/tests/test_knowledge_gap.py) validated:
1. `test_missing_spectral_gap_detection`: Verifies detection of missing IIRS coverage.
2. `test_missing_terrain_gap_detection`: Verifies detection of unconstrained elevation.
3. `test_missing_temporal_observation_gap`: Verifies detection of single-epoch acquisitions.
4. `test_footprint_non_overlap_gap_from_phase3_rejection`: Asserts that Phase 3 physical rejections (`GATE3_TARGET_OUTSIDE_CALIBRATED_SWATH`) create a `FOOTPRINT_NON_OVERLAP` knowledge gap with `PHYSICAL_FOOTPRINT_SEPARATION` blocking reason.
5. `test_uncertainty_too_high_gap`: Verifies gap generation when spatial uncertainty exceeds threshold.

**Test Result:** 5 passed, 0 failed.
Baseline 97 tests remain completely untouched and green. Total test count: $97 + 7 + 7 + 5 + 5 + 5 = 126$.
