# PHASE 3 — STAGE 3.5: PHYSICAL CORRESPONDENCE CANDIDATE ENGINE REPORT
**LunarSynapse Scientific Technical Documentation**  
**Date:** September 2026  
**Status:** COMPLETE (Stage 3.5 Gate Passed)  
**Execution Context:** Physically Constrained Cross-Sensor Candidate Engine  

---

## 1. Executive Summary & Mandatory Scientific Guardrails

In Phase 3 Stage 3.5, LunarSynapse implemented the **PhysicalCandidateEngine** (`outgraph/ml/matchers/physical_matcher.py`). It enforces a rigorous six-gate physical validation process for potential cross-sensor correspondence candidates based on 3D selenographic geometry, SLDEM2015 topography, and pushbroom parallax corridors.

> [!IMPORTANT]
> **SCIENTIFIC DISTINCTION & GUARDRAILS:**
> - This engine is **NOT** a generic appearance or learned matcher (e.g. SIFT, LoFTR, RIFT).
> - Zero homography, RANSAC, or uncalibrated polynomial warps are used.
> - Candidate acceptance requires passing all six physical gates.
> - If any gate fails, the candidate is **explicitly REJECTED** with structured physical evidence.
> - When applied to non-overlapping observation swaths, **100% of candidates are rejected**, preventing the fabrication of false correspondences.

---

## 2. Six-Gate Physical Verification Architecture

Every candidate point is evaluated sequentially through six physical gates:

```
                      Candidate Feature: (pixel, scan)
                                     │
                 ┌───────────────────┴───────────────────┐
                 ▼                                       ▼
    [Gate 1: Source Domain]                  [Gate 2: DEM Elevation]
  Point inside OHRC GroundGrid              Valid SLDEM2015 elevation
  PASS: Continues                           PASS: Continues
  FAIL: GATE1_SOURCE_OUT_OF_GRID            FAIL: GATE2_INVALID_DEM_ELEVATION
                 │                                       │
                 └───────────────────┬───────────────────┘
                                     ▼
                        [Gate 3: Target Domain]
                     Point inside TMC-2 GroundGrid
                     PASS: Continues
                     FAIL: GATE3_TARGET_OUTSIDE_CALIBRATED_SWATH
                                     │
                                     ▼
                        [Gate 4: Swath Boundary]
                   Point not clamped to boundary (p > 0)
                   PASS: Continues
                   FAIL: GATE4_TARGET_CLAMPED_TO_SWATH_BOUNDARY
                                     │
                                     ▼
                        [Gate 5: Parallax Limits]
                     Displacement <= Physical Bound (350m)
                     PASS: Continues
                     FAIL: GATE5_PARALLAX_EXCEEDS_PHYSICAL_BOUNDS
                                     │
                                     ▼
                        [Gate 6: Corridor Bounds]
                     Corridor strictly inside target array
                     PASS: CANDIDATE ACCEPTED
                     FAIL: GATE6_CORRIDOR_OUTSIDE_TARGET_ARRAY
```

---

## 3. Empirical Results on Real Mission Datasets

When evaluated on candidate points across the real OHRC image:
- **Total Points Evaluated:** 25 distributed grid points.
- **Accepted Candidates:** **0 (0.0%)**.
- **Rejected Candidates:** **25 (100.0%)**.
- **Rejection Breakdown:**
  - `GATE3_TARGET_OUTSIDE_CALIBRATED_SWATH`: 10 points (40.0% — western section outside TMC-2 triangulation).
  - `GATE4_TARGET_CLAMPED_TO_SWATH_BOUNDARY`: 15 points (60.0% — eastern section clamped to $p=0.0$).
- **Scientific Significance:**
  Unlike Phase 2 (where unconstrained RANSAC forced degenerate homographies across the gap), the Physical Candidate Engine correctly recognizes that the two observation swaths are physically disjoint and **refuses to fabricate correspondence**.

---

## 4. Test Suite Status

Test module: [`outgraph/tests/test_physical_matcher.py`](file:///c:/Users/Devi Prasath S/OneDrive/Scans/Desktop/SIH%2026166/outgraph/tests/test_physical_matcher.py)  
Status: **5 passed, 0 failed in 8.67s**  
- Valid synthetic candidate passes all 6 gates: PASSED
- Gate 1 rejection (source out of bounds): PASSED
- Gate 3 rejection (target outside swath): PASSED
- Gate 4 rejection (target boundary clamped): PASSED
- Batch evaluation rejecting 100% of non-overlapping real candidates: PASSED

**Stage 3.5 Acceptance Criteria:** FULLY SATISFIED.
