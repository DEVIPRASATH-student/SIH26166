# Phase 8.5 — Explainability / Provenance / Evidence Visibility Final Scientific Report

**Project:** LunarSynapse — Physics-Aware, Self-Evolving Multi-Modal Lunar World Model  
**SIH Problem Statement:** SIH26166 — Multi-modal, Sun-angle and Scale Invariant Image Correspondence using Chandrayaan-2 OHRC, TMC-2, and IIRS  
**Stage:** Phase 8.5 (Explainability / Provenance / Evidence Visibility)  
**Status:** `EXPLAINABILITY_VALIDATED`  
**Execution Timestamp:** 2026-09-24T23:17:00Z  

---

## 1. Executive Summary

Phase 8.5 establishes the unified, transparent explainability and provenance layer of LunarSynapse. Rather than presenting black-box match scores, the system now provides judges and scientific reviewers with immediate, auditable answers to the core question:

> **"Why did LunarSynapse reject this apparent visual match?"**

Every correspondence candidate and demonstration scenario now traverses an explicit, transparent reasoning chain:

$$\text{Observation} \longrightarrow \text{Provenance} \longrightarrow \text{Visual Candidates} \longrightarrow \text{Geometric Evidence} \longrightarrow \text{Physical Gates (1–6)} \longrightarrow \text{Illumination Evidence} \longrightarrow \text{11D Fusion} \longrightarrow \text{Uncertainty} \longrightarrow \text{Epistemic Decision} \longrightarrow \text{Knowledge Gap} \longrightarrow \text{Next Observation Proposal}$$

All scientific guardrails established in earlier phases have been strictly maintained:
1. `REAL-DATA ACCURACY = N/A` (No independent real-lunar ground-truth tie points exist).
2. `PHYSICAL CORRESPONDENCE NOT VALIDATED` for the real Boguslawsky OHRC/TMC-2 pair.
3. `REAL-LUNAR EMPIRICAL UNCERTAINTY CALIBRATION NOT ESTABLISHED`.
4. $\text{Visual Similarity} \neq \text{Physical Correspondence}$.
5. $\text{Entity Association} \neq \text{Direct Image Correspondence}$.
6. $\text{UNKNOWN} \neq \text{NEGATIVE}$ (Missing evidence is never converted to negative evidence).
7. Recommendations strictly use `POTENTIALLY_REDUCES_UNCERTAINTY`; `WILL_RESOLVE` and `GUARANTEED` are strictly forbidden.
8. Raw data in `data/real/` remains completely untouched (0 bytes modified).

---

## 2. Explainability Architecture

The Phase 8.5 explainability architecture introduces a multi-tier explanation framework accessible via backend REST endpoints and an interactive frontend component (`ExplainabilityModal.tsx`):

1. **Judge-Friendly Decision Card**: Synthesizes the decision within seconds, explaining the high-level verdict, clarifying that non-overlap does not imply images are unrelated, and exposing decisive gate metrics.
2. **Deterministic Six Physical Gates Table**: Evaluates physical consistency across GroundGrid projection, DEM boundaries, swath limits, boundary clamping, elevation corridor, and bidirectional raytrace residuals.
3. **Standalone Illumination Verification Module**: Exposes solar azimuth/elevation vectors, divergence calculations, and consistency thresholds separately from the six physical gates.
4. **11-Dimensional Scientific Evidence Ledger**: Tracks evidence presence, absence, sources, and confidence across all 11 scientific dimensions without converting missing signals into negative conclusions.
5. **Epistemic Uncertainty Decomposition**: Explains *why* uncertainty is at its current level (evidence disagreement, geometric instability, feature ambiguity, spatial sparsity) and enforces the 4.0 px saturation limit.
6. **Knowledge Gap & Next-Best Observation (NBO)**: Bridges unresolved epistemic states to uncertainty-reducing observation proposals.
7. **Interactive Step-by-Step Decision Trace**: Provides a chronological, step-by-step audit trail from observation ingestion to epistemic conclusion.

---

## 3. Provenance Architecture

LunarSynapse enforces strict provenance tracking across all data types to ensure zero ambiguity between real lunar flight data and synthetic controlled benchmarks:

- **Raw Observation**: Originating from ISRO ISSDC archival Level-2 products (`ch2_ohr_ncp_20210402t0546284043_d_img_d18` and `ch2_tmc_nca_20240523t1600309581_d_img_d18`), tagged with PDS4 URNs, sensor geometries, and solar vectors.
- **Derived Result**: Orthorectified GroundGrids, SIFT keypoint sets, and homography matrices explicitly labeled as derived transformations.
- **Synthetic Control**: Simulated sensor products generated from procedural digital elevation models, with `is_synthetic = True` strictly enforced.
- **Model Inference**: Epistemic classifications and uncertainty estimates flagged as probabilistic system evaluations.
- **Recommendation**: Active observation proposals marked as decision-support heuristics, with the explicit disclaimer: *"No spacecraft tasking or orbital mechanics are simulated."*

---

## 4. Evidence Trace

For every correspondence hypothesis, an expandable step-by-step trace documents the lifecycle of the evaluation:

```
STEP 1: Observation Ingestion       → Source and target Level-2 products loaded with ISRO ISSDC provenance metadata.
STEP 2: Candidate Generation        → SIFT multi-scale detector identified candidate matches in 2D image coordinates.
STEP 3: Geometric Verification       → RANSAC homography estimation formed candidate 2D correspondence hypothesis.
STEP 4: GroundGrid Projection       → Source coordinates projected to Lunar ellipsoid through calibrated GroundGrid.
STEP 5: Physical Gate 1 & 2 Eval    → Monotonicity and SLDEM2015 regional coverage validated.
STEP 6: Physical Gate 3 Swath Eval  → Target coordinate falls outside calibrated target swath by ~1.49 km - 2.04 km.
STEP 7: Epistemic Decision Formation→ Physical correspondence not validated due to decisive Gate 3 rejection.
STEP 8: Knowledge Gap Creation      → Non-overlapping footprints create FOOTPRINT_NON_OVERLAP knowledge gap.
STEP 9: Observation Proposal        → Adjacent strip observation proposed that POTENTIALLY_REDUCES_UNCERTAINTY.
```

---

## 5. Physical-Gate Explanation

The six physical gates established in Phase 3 remain immutable in name, order, and scientific definition:

| Gate ID | Gate Name | Input | Metric | Threshold | Scientific Function |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **GATE 1** | `INVALID_SOURCE_GROUNDGRID` | Source GroundGrid GeoTIFF | Vertex Monotonicity | True | Rejects malformed or non-invertible sensor projection grids. |
| **GATE 2** | `DEM_OUT_OF_BOUNDS_OR_NODATA` | SLDEM2015 Elevation Grid | Coordinate Domain | True | Rejects coordinates falling outside DEM coverage or on NoData. |
| **GATE 3** | `TARGET_OUTSIDE_CALIBRATED_SWATH` | Target GroundGrid Polygon | Boundary Separation | $\le 0.0\text{ m}$ | Rejects coordinates falling outside the calibrated physical swath. |
| **GATE 4** | `TARGET_CLAMPED_TO_SWATH_BOUNDARY` | Boundary Detector | Clamping Delta | $0.0\text{ px}$ | Rejects artificial edge clamping that biases spatial alignment. |
| **GATE 5** | `TARGET_OUTSIDE_ELEVATION_CORRIDOR`| DEM Terrain Intersection | Elevation Residual | $\pm 50.0\text{ m}$ | Rejects ray-surface intersections outside sensor elevation bounds. |
| **GATE 6** | `BIDIRECTIONAL_RESIDUAL_TOO_LARGE` | Raytrace Closed Loop | Bidirectional Delta | $\le 4.0\text{ px}$ | Rejects unclosed ray loops exceeding the saturation bound. |

> **Critical Scientific Invariant:** Gate 5 is strictly `TARGET_OUTSIDE_ELEVATION_CORRIDOR`. Illumination verification is NOT Gate 5.

---

## 6. Illumination Explanation

Illumination verification operates as an independent radiometric consistency mechanism:

- **Metrics Evaluated**: Solar azimuth difference, solar elevation difference, incidence angle divergence, and temporal separation.
- **Rejection Threshold**: Solar azimuth divergence $> 60.0^\circ$.
- **Scenario C Evaluation**:
  - Solar azimuth divergence: $180.0^\circ$ (controlled opposing illumination).
  - Status: `REJECTED`.
  - Scientific Explanation: *"Illumination verification rejected the candidate due to the controlled illumination contradiction. Solar azimuth divergence of 180.0° exceeds the 60.0° physical consistency threshold, rendering the candidate physically unsupported under the tested conditions."*
  - Language Guardrail: Characterized as *"physically unsupported under tested conditions"*, strictly avoiding *"false match prevented"*.

---

## 7. Epistemic Uncertainty Explanation

Uncertainty is never presented as an unexplained scalar. LunarSynapse decomposes uncertainty into four distinct structural factors:

1. **Evidence Disagreement**: Conflict between modalities (e.g., 2D visual similarity vs. 3D spatial non-overlap).
2. **Geometric Instability**: High matrix condition number or sensitivity to initial coordinate perturbations.
3. **Feature Ambiguity**: Repetitive lunar regolith crater texture producing pseudo-homologous keypoints.
4. **Spatial Sparsity**: Lack of uniform candidate distribution across the target overlap domain.

### Empirical Calibration Status
- **Real Flight Data**: `REAL-LUNAR EMPIRICAL UNCERTAINTY CALIBRATION NOT ESTABLISHED`. The scalar value ($0.95$) reflects maximum epistemic uncertainty, not an empirically calibrated posterior distribution.
- **Saturation Bound**: Feature-dispersion uncertainty saturates above $4.0\text{ px}$. Residuals beyond this threshold cannot provide sub-pixel precision.

---

## 8. Knowledge-Gap Explanation

When a candidate is rejected or remains uncertain, LunarSynapse autonomously structures an Epistemic Knowledge Gap:

- **What is known?** Regional Boguslawsky crater morphology, calibrated sensor grids, and image-space keypoints.
- **What is unknown?** Cross-sensor physical sub-pixel alignment across the observation swaths.
- **Why is it unknown?** The pushbroom swaths are separated by $\sim 1.49\text{ km} - 2.04\text{ km}$, preventing physical ground overlap.
- **What evidence is missing?** An overlapping intermediate swath covering the baseline separation.

---

## 9. Next Observation (NBO) Explanation

Observation planning proposals translate knowledge gaps into targeted acquisition requirements:

- **Candidate Observation**: `TMC-2_ADJACENT_STRIP`
- **Expected Uncertainty Reduction**: $+78\%$ information gain estimate.
- **Terminology Rule**: Recommendations use strictly `POTENTIALLY_REDUCES_UNCERTAINTY`.
- **Prohibited Terms**: `WILL_RESOLVE` and `GUARANTEED` are strictly prohibited.
- **Mandatory Disclaimer**: *"Active observation recommendations are autonomous decision-support proposals, NOT spacecraft tasking, orbital scheduling, or mission commands. No spacecraft tasking or orbital mechanics are simulated."*

---

## 10. Scenario A Explanation (Real Negative Control)

- **Source / Target**: Chandrayaan-2 OHRC (`0.25 m/px`) vs. TMC-2 (`5.0 m/px`).
- **Provenance**: `REAL LUNAR DATA (ISRO Chandrayaan-2 ISSDC Archive)` (`is_synthetic = False`).
- **Candidate Count**:
  - Current Demonstration Instance: $26$ visual candidates.
  - Historical Phase 7 Benchmark: $31$ candidates / $8$ geometric inliers ($25.81\%$).
- **Physical Evaluation**: Gate 1 (PASS), Gate 2 (PASS), **Gate 3 (REJECTED)**.
- **Footprint Separation**: $\sim 1.49\text{ km} - 2.04\text{ km}$ non-overlap.
- **Decision**: `REJECTED`.
- **Primary Reason**: `TARGET_OUTSIDE_CALIBRATED_SWATH`.
- **Verdict**: `PHYSICAL CORRESPONDENCE NOT VALIDATED`.
- **Judge Distinction**: Both images observe the Boguslawsky region, but their specific pixel footprints do not physically overlap.

---

## 11. Scenario B Explanation (Synthetic Positive Control)

- **Pair**: Synthetic OHRC isomorphic pair under controlled illumination.
- **Provenance**: `SYNTHETIC CONTROLLED DATA` (`is_synthetic = True`).
- **Candidate Count**: $48$ candidates, $42$ geometric inliers ($87.5\%$).
- **Physical Evaluation**: All 6 physical gates pass within calibrated thresholds (residual $0.82\text{ px}$).
- **Decision**: `ACCEPTED`.
- **Primary Reason**: `PHYSICALLY_VALIDATED_UNDER_CONTROLLED_CONDITIONS`.
- **Limitation**: Synthetic validation demonstrates algorithm function under ideal conditions; it does NOT establish real-lunar accuracy.

---

## 12. Scenario C Explanation (Synthetic Illumination Contradiction)

- **Pair**: Synthetic OHRC pair with $180.0^\circ$ opposing solar azimuth.
- **Provenance**: `SYNTHETIC CONTROLLED DATA` (`is_synthetic = True`).
- **Visual Candidates**: $38$ candidates, $18$ inliers in 2D image coordinates (shadow terminators mimic ridge lines).
- **Physical Gates (1–6)**: ALL PASS.
- **Illumination Verification**: `REJECTED` (Divergence $180.0^\circ > 60.0^\circ$ threshold).
- **Decision**: `REJECTED`.
- **Primary Reason**: `ILLUMINATION_CONTRADICTION`.
- **Language**: *"Physically unsupported under the tested conditions."*

---

## 13. Scenario D Explanation (Synthetic Low-Evidence UNKNOWN)

- **Pair**: Synthetic low-light crater interior (Permanently Shadowed Region, SNR $< 3.0$).
- **Provenance**: `SYNTHETIC CONTROLLED DATA` (`is_synthetic = True`).
- **Candidate Count**: $N = 2$ candidates (insufficient for homography, minimum $4$ required).
- **Physical Evaluation**: `NOT_EVALUATED` (insufficient points to form hypothesis).
- **Decision**: `UNKNOWN`.
- **Primary Reason**: `INSUFFICIENT_EVIDENCE`.
- **Axiom**: $\text{UNKNOWN} \neq \text{NEGATIVE}$. Absence of evidence is not evidence of absence; the system refrains from forcing an ungrounded binary rejection.

---

## 14. Scenario E Explanation (Scale Disparity → NBO)

- **Pair**: Synthetic high-res OHRC ($0.25\text{ m/px}$) vs. coarse TMC-2 ($5.0\text{ m/px}$) ($20\times$ scale disparity).
- **Provenance**: `SYNTHETIC CONTROLLED DATA` (`is_synthetic = True`).
- **Candidate Count**: $8$ candidates, $3$ fragile inliers (residual $3.45\text{ px}$).
- **Physical Evaluation**: `AMBIGUOUS` (approaches $4.0\text{ px}$ saturation threshold).
- **Decision**: `AMBIGUOUS`.
- **Knowledge Gap**: `GAP-SCALE-DISPARITY-001 (MISSING_MODALITY)`.
- **Recommendation**: `TMC-2_STEREO_1M` intermediate scale bridge (`POTENTIALLY_REDUCES_UNCERTAINTY`).

---

## 15. Scientific Language Audit

A full automated scan across backend services, frontend components, and test files was executed to detect forbidden claims:

| Forbidden Phrase | Target Files Scanned | Instances Found Outside Disclaimers | Audit Status |
| :--- | :--- | :--- | :--- |
| `100% accurate` | All Python / TSX files | 0 | **PASS** |
| `guaranteed` | All Python / TSX files | 0 | **PASS** |
| `confirmed lunar match` | All Python / TSX files | 0 | **PASS** |
| `ai proved` | All Python / TSX files | 0 | **PASS** |
| `universally invariant` | All Python / TSX files | 0 | **PASS** |
| `WILL_RESOLVE` | All Python / TSX files | 0 | **PASS** |
| `real-time spacecraft tasking`| All Python / TSX files | 0 | **PASS** |
| `validated real-lunar accuracy`| All Python / TSX files | 0 | **PASS** |
| `calibrated real-lunar uncertainty`| All Python / TSX files | 0 | **PASS** |
| `wrong lunar feature` | All Python / TSX files | 0 | **PASS** |
| `never fails` | All Python / TSX files | 0 | **PASS** |
| `eliminates false positives` | All Python / TSX files | 0 | **PASS** |

---

## 16. Dedicated Phase 8.5 Test Results

A dedicated test suite `outgraph/tests/test_phase8_5_explainability.py` was authored, containing 19 comprehensive tests covering all 18 requirements:

- `test_1_real_negative_control_explanation_exists`: **PASSED**
- `test_2_synthetic_explanation_marked_synthetic`: **PASSED**
- `test_3_provenance_is_preserved`: **PASSED**
- `test_4_six_gates_correctly_named`: **PASSED**
- `test_5_gate_5_is_elevation_corridor`: **PASSED**
- `test_6_illumination_is_not_gate_5`: **PASSED**
- `test_7_illumination_evidence_separately_exposed`: **PASSED**
- `test_8_unknown_remains_unknown`: **PASSED**
- `test_9_missing_evidence_not_converted_to_negative`: **PASSED**
- `test_10_entity_association_does_not_imply_correspondence`: **PASSED**
- `test_11_uncertainty_explanation_preserves_unknown`: **PASSED**
- `test_12_saturation_limitation_remains_visible`: **PASSED**
- `test_13_nbo_uses_potentially_reduces_uncertainty`: **PASSED**
- `test_14_no_will_resolve_in_explanations`: **PASSED**
- `test_15_no_forbidden_claims_in_explanations`: **PASSED**
- `test_16_real_benchmark_values_remain_unchanged`: **PASSED**
- `test_17_current_demonstration_instance_distinguishable`: **PASSED**
- `test_18_raw_data_remains_unchanged`: **PASSED**
- `test_pydantic_schema_validation`: **PASSED**

**Dedicated Test Summary:** 19 passed, 0 failed, 0 errors in 2.72s.

---

## 17. Full Regression Suite Results

The entire project test suite was executed:
- **Total Tests Collected**: 358 tests
- **Tests Passed**: 358 passed
- **Tests Failed**: 0
- **Errors**: 0

---

## 18. Raw Data Integrity Verification

- Pre-modification git status on `data/real/`: 0 bytes modified.
- Post-modification git status on `data/real/`: 0 bytes modified.
- Tracked diff stat: `git diff --stat data/real/` returned empty string.

---

## 19. Phase Preservation Matrix

- **Phase 3 Preservation**: Calibrated GroundGrid geometry, SLDEM2015 bicubic interpolation, and six physical gates remain identical.
- **Phase 7 Preservation**: Historical benchmark metrics ($31$ candidates, $8$ geometric inliers, $25.81\%$ inlier ratio) strictly maintained without overwrite.
- **Phase 8.4 Preservation**: The five canonical scenarios (A–E) execute identically with identical mathematical verdicts.

---

## 20. Limitations & Blockers

### Limitations
1. `Real-data accuracy = N/A` (Physical correspondence not validated on real flight data).
2. `Real-lunar empirical uncertainty calibration not established` (Quantification remains bounded by epistemic models).
3. Active observation recommendations are advisory decision-support heuristics, not executable spacecraft commands.
4. Feature-dispersion uncertainty saturates above $4.0\text{ px}$.

### Blockers
- **None.** All Phase 8.5 deliverables are complete, verified, and audited.

---

## 21. Recommended Next Phase

Phase 8.5 is fully complete and validated. **Phase 8.6 (Performance / Reliability / Deployment Hardening)** is ready for authorization.
