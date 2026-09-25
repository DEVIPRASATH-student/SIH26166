# PHASE 4 STAGE 4.6 REPORT: NEXT-BEST OBSERVATION RECOMMENDATION ENGINE
**Project:** LunarSynapse (SIH 26166)  
**Date:** September 2026  
**Status:** COMPLETE & VERIFIED  
**Stage:** 4.6 — Evidence-Driven Next Observation Targeting

---

## 1. Objective

Stage 4.6 implements the Next-Best Observation (NBO) recommendation engine, enabling the Lunar World Model to proactively suggest future targeted acquisitions that will maximally reduce epistemic uncertainty.

### Scientific Guardrails Enforced
1. **Uncertainty Language:** All recommendations strictly adopt the scientifically modest phrase `POTENTIALLY_REDUCES_UNCERTAINTY`. The term `WILL_RESOLVE` is strictly forbidden.
2. **Qualitative Potential Ratings:** Rather than inventing arbitrary numerical information gain numbers without an empirical likelihood model, recommendations are rated using qualitative categories:
   - `HIGH_POTENTIAL`
   - `MEDIUM_POTENTIAL`
   - `LOW_POTENTIAL`
   - `UNKNOWN`
3. **Geometric & Payload Feasibility:** Recommendations verify whether candidate payloads are available and whether acquisition geometry is feasible (e.g. adjacent swath requirements to bridge non-overlapping footprints).

---

## 2. Implementation Overview

Implemented in [`outgraph/ml/world_model/next_best_observation.py`](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/outgraph/ml/world_model/next_best_observation.py) via class [`NextBestObservationEngine`](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/outgraph/ml/world_model/next_best_observation.py#L48-L163).

### 2.1 Gap-to-Targeting Mapping
- `FOOTPRINT_NON_OVERLAP`: Recommends an adjacent orbital track for `TMC-2` or `OHRC` shifted by $\sim 2\text{ km}$ to bridge the measured reference-datum gap ($1.49 - 2.05\text{ km}$).
- `MISSING_SPECTRAL_VALIDATION`: Recommends `IIRS` nadir targeting across $0.8 - 5.0\,\mu\text{m}$ to resolve pyroxene, olivine, and possible hydroxyl/hydration absorption features.
- `MISSING_TERRAIN_VALIDATION`: Recommends `TMC-2` stereo forward/aft photogrammetry or laser altimetry.
- `MISSING_TEMPORAL_OBSERVATION`: Recommends `OHRC` acquisition under opposite solar azimuth ($\Delta \text{azimuth} \approx 180^\circ$) to resolve interior crater shadow structures.
- `UNCERTAINTY_TOO_HIGH`: Recommends sub-meter `OHRC` optical targeting ($0.25\text{ m/px}$).

---

## 3. Verification & Test Results

The test suite in [`outgraph/tests/test_next_best_observation.py`](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/outgraph/tests/test_next_best_observation.py) validated:
1. `test_footprint_gap_recommendation`: Verifies recommendation to bridge footprint non-overlap gap using adjacent TMC-2 track; asserts absence of `WILL_RESOLVE` and presence of `POTENTIALLY_REDUCES_UNCERTAINTY`.
2. `test_missing_spectral_gap_recommendation`: Confirms IIRS targeting for unobserved spectral bands.
3. `test_unavailable_sensor_feasibility`: Verifies assignment of `PAYLOAD_UNAVAILABLE` when a recommended instrument is offline.
4. `test_deterministic_generation`: Confirms deterministic, repeatable recommendation generation.

**Test Result:** 4 passed, 0 failed.
Baseline 97 tests remain completely untouched and green. Total test count: $97 + 7 + 7 + 5 + 5 + 5 + 4 = 130$.
