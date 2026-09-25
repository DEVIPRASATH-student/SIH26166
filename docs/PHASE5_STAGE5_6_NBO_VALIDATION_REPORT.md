# PHASE 5 STAGE 5.6 REPORT: NEXT-BEST-OBSERVATION VALIDATION
**Project:** LunarSynapse (SIH 26166)  
**Date:** September 2026  
**Status:** COMPLETE & VERIFIED  
**Stage:** 5.6 — Evidence-Driven Next Observation Targeting Engine

---

## 1. Objective

Stage 5.6 validates that the Next-Best Observation (NBO) recommendation engine produces scientifically defensible recommendations without fabricating orbital trajectories or making false assertions of certainty.

### Key Scientific Mandates:
1. **Modest Uncertainty Language:** Every recommendation strictly states `POTENTIALLY_REDUCES_UNCERTAINTY`. The term `WILL_RESOLVE` is strictly forbidden.
2. **Trajectory Honesty:** The recommendation engine does **not** invent future orbital ephemerides or state vectors. The adjacent track required to bridge the OHRC/TMC-2 footprint gap is explicitly described as:
   `"potentially useful adjacent observation geometry (adjacent track shifted by ~2.0 km west; not a confirmed spacecraft trajectory plan)"`.
3. **Four Feasibility States:** Explicitly tracks `FEASIBLE`, `GEOMETRICALLY_INCOMPATIBLE`, `PAYLOAD_UNAVAILABLE`, and `UNKNOWN`.
4. **Qualitative Potential Ratings:** Employs qualitative categories (`HIGH_POTENTIAL`, `MEDIUM_POTENTIAL`, `LOW_POTENTIAL`, `UNKNOWN`) to avoid fabricating artificial numerical information-gain numbers.

---

## 2. Recommendation Flow & Verification

The recommendation flow processes each detected knowledge gap:
$$\text{Knowledge Gap} \longrightarrow \text{Candidate Sensor Identification} \longrightarrow \text{Modality \& Feasibility Check} \longrightarrow \text{Recommendation Output}$$

### Validated Test Scenarios:
- **Footprint Non-Overlap:** Targets an adjacent TMC-2 track with `HIGH_POTENTIAL` to bridge the $1.77\text{ km}$ gap.
- **Missing Spectral Modality:** Targets IIRS across $0.8 - 5.0\,\mu\text{m}$ bands to resolve clinopyroxene and olivine absorption bands.
- **Payload Unavailability:** When an instrument is not active in the sensor catalog, the recommendation status is correctly flagged as `PAYLOAD_UNAVAILABLE`.
- **Deterministic Generation:** Multiple invocations over identical knowledge gaps yield identical, repeatable recommendations.

---

## 3. Test Results

Existing and updated tests in [`outgraph/tests/test_next_best_observation.py`](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/outgraph/tests/test_next_best_observation.py) validated:
1. `test_footprint_gap_recommendation`: Verifies adjacent track targeting, presence of `POTENTIALLY_REDUCES_UNCERTAINTY`, and complete absence of `WILL_RESOLVE`.
2. `test_missing_spectral_gap_recommendation`: Verifies IIRS mineral targeting.
3. `test_unavailable_sensor_feasibility`: Verifies assignment of `PAYLOAD_UNAVAILABLE`.
4. `test_deterministic_generation`: Confirms deterministic output.

**Test Result:** 4 passed, 0 failed. Total passing test baseline preserved.
