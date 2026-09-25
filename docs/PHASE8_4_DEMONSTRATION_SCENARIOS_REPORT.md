# LunarSynapse — Phase 8.4 Demonstration Scenarios Report

**Project:** LunarSynapse (SIH 26166)  
**Problem Statement:** Multi-modal, Sun-angle and Scale Invariant Image Correspondence using Chandrayaan-2 OHRC, TMC-2 and IIRS  
**Stage:** Phase 8.4 — Real + Synthetic Demonstration Scenarios  
**Status:** `DEMONSTRATION_VALIDATED`  
**Date:** September 2026  

---

## 1. Executive Summary

Phase 8.4 implements and validates a scientifically grounded, SIH-ready suite of 5 demonstration scenarios. The demonstration suite operationalizes the central LunarSynapse paradigm:

$$\text{Observation} \longrightarrow \text{Visual Candidates} \longrightarrow \text{Correspondence Hypothesis} \longrightarrow \text{Geometric Verification} \longrightarrow \text{Physical Verification} \longrightarrow \text{Evidence} \longrightarrow \text{Uncertainty} \longrightarrow \text{World Model} \longrightarrow \text{Knowledge Gap} \longrightarrow \text{NBO}$$

The governing scientific axiom across all views and APIs remains immutable:
$$\mathbf{Visual\ Similarity\ \neq\ Physical\ Correspondence}$$
$$\mathbf{Entity\ Association\ \neq\ Direct\ Image\ Correspondence}$$
$$\mathbf{UNKNOWN\ \neq\ NEGATIVE}$$

All five canonical scenarios have been formalized in the backend (`/api/demo/scenarios`), implemented in the demonstration UI (`ScenariosLab.tsx`), and verified across 11 focused automated regression tests.

---

## 2. Scenario Inventory

| Scenario ID | Name | Provenance | Candidate Count | Physical Verification Result | Epistemic Decision |
|---|---|---|---|---|---|
| **SCENARIO-A** | Real Lunar Negative Control (OHRC vs TMC-2) | `REAL LUNAR DATA` (`is_synthetic = false`) | 26 candidates (CURRENT INSTANCE) | `REJECTED` (Gate 3/4 `FOOTPRINT_NON_OVERLAP`, ~1.49–2.04 km separation) | Physical correspondence not validated; real validation unestablished |
| **SCENARIO-B** | Controlled Synthetic OHRC Homologous Pair | `SYNTHETIC CONTROLLED DATA` (`is_synthetic = true`) | 184 candidates / 168 inliers (91.3%) | `PHYSICALLY_VERIFIED` (All 6 gates passed under known conditions) | Controlled validation; does not establish real accuracy |
| **SCENARIO-C** | Controlled Synthetic Illumination Contradiction | `SYNTHETIC CONTROLLED DATA` (`is_synthetic = true`) | 45 visual candidates | `REJECTED` (Illumination verification divergence 180° > 60° threshold) | Physically unsupported under tested conditions; candidate rejected under illumination contradiction |
| **SCENARIO-D** | PSR Low-Evidence Control | `SYNTHETIC CONTROLLED DATA` (`is_synthetic = true`) | 2 candidates ($N < 4$ required) | `EVALUATION_INCOMPLETE` (Decision unforced) | `UNKNOWN` ($U=1.00$); `UNKNOWN != NEGATIVE` preserved |
| **SCENARIO-E** | Cross-Scale Disparity Knowledge Gap → NBO | `SYNTHETIC CONTROLLED DATA` (`is_synthetic = true`) | 8 candidates (20x scale step) | `UNCERTAIN` (Scale disparity limits direct gate validation) | `MISSING_MODALITY` gap $\to$ `POTENTIALLY_REDUCES_UNCERTAINTY` recommendation |

---

## 3. Real Negative-Control Result (Scenario A)

### Observational Input
- **OHRC Observation:** `urn:isro:isda:ch2_cho.ohr:data_calibrated:ch2_ohr_ncp_20210402t0546284043_d_img_d18`
- **TMC-2 Observation:** `urn:isro:isda:ch2_cho.tmc:data_calibrated:ch2_tmc_nca_20240523t1600309581_d_img_d18`
- **Provenance:** `REAL LUNAR DATA` (`is_synthetic = false`)

### Execution Trace & Audit Disclosures
1. **Visual Matching:** SIFT/ORB detection extracts **26 visual candidate keypoints** in image space.
   - *Audit Clarification A:* Explicitly labeled **CURRENT DEMONSTRATION INSTANCE: 26 candidates**, separate from historical Phase 7 benchmark (31 candidates / 8 geometric inliers).
2. **GroundGrid / DEM Ray Projection:** Rigorous pushbroom camera geometry and SLDEM2015 topography project pixels to lunar coordinates.
3. **Physical Verification (Gates 3 & 4):**
   - Calibrated ground tracks do not overlap; footprints are separated by **approximately 1.49 km – 2.04 km**.
   - Target coordinate falls completely outside calibrated swath.
   - Physical rejection triggered at Gate 3 / Gate 4 (`FOOTPRINT_NON_OVERLAP`).
4. **Gate 6 Metric Distinction:**
   - Image-space residual threshold $\le 4.0\text{ px}$ (Gate 6 saturation bound).
   - Physical ground-space residual threshold $> 15\text{ m}$.
5. **Scientific Verdict:**
   - **"The evaluated physical geometry does not support correspondence for this pair."**
   - **`PHYSICAL CORRESPONDENCE NOT VALIDATED`**
   - **`REAL-DATA ACCURACY = N/A`**

---

## 4. Synthetic Positive-Control Result (Scenario B)

### Observational Input
- **Source Observation:** `OBS-OHRC-SYNTH-01`
- **Target Observation:** `OBS-OHRC-SYNTH-02`
- **Provenance:** `SYNTHETIC CONTROLLED DATA` (`is_synthetic = true`)

### Execution Trace
1. **Candidate Generation:** 184 feature matches detected.
2. **Geometric Verification:** 168 inliers verified via affine/homography RANSAC (inlier ratio: 0.913).
3. **Physical Verification:** All 6 physical gates pass under known controlled terrain conditions:
   - Residual error: $1.2\text{ px} \le 4.0\text{ px}$ image-space; $2.1\text{ m} \le 15\text{ m}$ ground-space.
4. **Epistemic Result:** Controlled world-model update confirmed.
5. **Mandatory Disclaimer:**
   - *"This controlled synthetic result demonstrates pipeline behavior under known conditions. It does not establish real-lunar accuracy."*
   - Synthetic metrics are strictly quarantined and never pollute real benchmarks.

---

## 5. Synthetic Adversarial Control (Scenario C)

### Observational Input
- **Source Observation:** `OBS-CONTRA-001` (Solar azimuth $45^\circ$)
- **Target Observation:** `OBS-CONTRA-002` (Solar azimuth $225^\circ$)
- **Provenance:** `SYNTHETIC CONTROLLED DATA` (`is_synthetic = true`)

### Execution Trace & Architectural Distinction
1. **Visual Candidates:** 45 visual matches detected along crater rims due to symmetrical crater curvature.
2. **Illumination Verification (Separate Physics Validation):**
   - Controlled solar azimuth divergence is $180.0^\circ$, far exceeding the physics-based threshold of $60.0^\circ$. Shadow inversion causes false topological slope correlation.
   - **Architectural Clarification:** Illumination verification is separate from the six physical gates. Gate 5 remains strictly `TARGET_OUTSIDE_ELEVATION_CORRIDOR`. Illumination verification operates as a dedicated physics/evidence validation stage.
3. **Scientific Verdict:**
   - **`REJECTED`**
   - Formulated as: *"Illumination verification rejected the candidate due to the controlled 180° solar/illumination divergence (>60° threshold); physical correspondence is unsupported under the tested illumination condition."*
   - Correctly phrased as **"physically unsupported under the tested conditions"** (NOT "wrong lunar feature").
   - Demonstrates that naive AI feature matching generates deceptive candidate matches that LunarSynapse illumination physics successfully rejects under controlled scenarios.

---

## 6. Unknown / Insufficient Evidence Control (Scenario D)

### Observational Input
- **Source Observation:** `OBS-UNKNOWN-001` (PSR interior, low SNR)
- **Target Observation:** `OBS-UNKNOWN-002`
- **Provenance:** `SYNTHETIC CONTROLLED DATA` (`is_synthetic = true`)

### Execution Trace
1. **Candidate Extraction:** Deep shadow floor yields only **2 keypoints** ($N < 4$ minimum required for homography).
2. **Pipeline Behavior:** Halts at candidate hypothesis stage; refuses to force an ungrounded binary decision.
3. **Preservation of Scientific Axiom:**
   - **`UNKNOWN != NEGATIVE`**
   - High epistemic uncertainty ($U = 1.00$).
   - Absence of evidence does not constitute negative entity evidence.

---

## 7. Knowledge Gap → Next-Best Observation (Scenario E)

### Observational Input
- **Source Observation:** `OBS-OHRC-001` ($0.25\text{ m/px}$)
- **Target Observation:** `OBS-TMC2-001` ($5.0\text{ m/px}$)
- **Provenance:** `SYNTHETIC CONTROLLED DATA` (`is_synthetic = true`)

### Execution Trace & Recommendation Chain
1. **Cross-Scale Disparity:** 20x resolution gap yields 8 fragile candidate matches; physical gates indeterminate.
2. **Knowledge Gap Instantiation:**
   - `gap_type`: `MISSING_MODALITY` / Scale bottleneck.
   - `priority`: 0.76.
3. **Autonomous Recommendation Formulation:**
   - Recommendation type: `POTENTIALLY_REDUCES_UNCERTAINTY`
   - Target sensor: `TMC-2_STEREO_1M` (intermediate 1.0–2.0 m/px bridge)
   - Expected information gain: $+65\%$
4. **Operational Safeguard:**
   - Formulated as autonomous decision-support proposal.
   - Disclaimed: *NOT spacecraft tasking, orbital scheduling, or mission commands.*
   - Strict ban on words `WILL_RESOLVE` or `GUARANTEED`.

---

## 8. Real vs. Synthetic Separation Architecture

LunarSynapse maintains strict structural isolation:
1. **Backend / API Truth:** Every observation and correspondence carries explicit boolean `is_synthetic`.
2. **Database Integrity:** Real flight rows are partitioned and never overwritten by synthetic generation routines.
3. **Benchmark Segregation:** `results/phase2/real_benchmark_results.json` contains solely real flight evaluations. Synthetic metrics do not compute real-lunar accuracy.
4. **UI Badging:** Visual badges (`REAL LUNAR DATA` in amber vs. `SYNTHETIC CONTROLLED DATA` in purple) appear across all scenario panels.

---

## 9. Scientific Safety & Claim Audit

A complete grep audit of the frontend code, schemas, and scenario representations verified 0 instances of prohibited claims:

| Prohibited Phrase | Occurrences Found | Compliant Replacement Used |
|---|---|---|
| `100% accurate` / `perfect` / `guaranteed` | 0 | *demonstrated under tested conditions* |
| `confirmed lunar match` | 0 | *candidate correspondence hypothesis* |
| `ai proved` | 0 | *evaluated scenario* |
| `universally invariant` | 0 | *scale/illumination conditioned* |
| `WILL_RESOLVE` | 0 | `POTENTIALLY_REDUCES_UNCERTAINTY` |
| `real-time spacecraft tasking` | 0 | *autonomous decision-support proposal* |
| `validated real-lunar accuracy` | 0 | `REAL-DATA ACCURACY = N/A` |
| `calibrated real-lunar uncertainty` | 0 | `REAL-LUNAR EMPIRICAL UNCERTAINTY CALIBRATION NOT ESTABLISHED` |
| `wrong lunar feature` | 0 | *physically unsupported under the tested conditions* |

---

## 10. Automated Testing Results

- **Dedicated Phase 8.4 Suite:** `outgraph/tests/test_phase8_4_demonstration_scenarios.py`
  - Total tests: 11
  - Passed: 11
  - Failed: 0
  - Errors: 0
- **Full Backend Regression Suite:**
  - Total tests: 338
  - Passed: 338
  - Failed: 0
  - Errors: 0
- **Frontend Build Validation:**
  - `npm run build` executed cleanly in 11.06s.
  - TypeScript errors: 0.

---

## 11. Raw-Data Integrity Audit

Git telemetry and filesystem inspection of raw flight data:
```bash
git status --short data/real/
git diff --stat data/real/
```
**Result:** Exactly **0 bytes modified** under `data/real/`.

---

## 12. Preservation of Previous Scientific Phases

- **Phase 3 Preservation:** Six kinematic gates (`GATE 1` to `GATE 6`) remain strictly implemented with dual thresholds ($4.0\text{ px}$ image-space residual limit, $15\text{ m}$ physical ground-space rejection).
- **Six Physical Gates Invariant:** The established six physical gates remain strictly defined: Gate 1 (`INVALID_SOURCE_GROUNDGRID`), Gate 2 (`DEM_OUT_OF_BOUNDS_OR_NODATA`), Gate 3 (`TARGET_OUTSIDE_CALIBRATED_SWATH`), Gate 4 (`TARGET_CLAMPED_TO_SWATH_BOUNDARY`), Gate 5 (`TARGET_OUTSIDE_ELEVATION_CORRIDOR`), Gate 6 (`BIDIRECTIONAL_RESIDUAL_TOO_LARGE`). Illumination verification is separate from the six physical gates. Gate 5 remains `TARGET_OUTSIDE_ELEVATION_CORRIDOR`.
- **Phase 7 Preservation:** Historical Phase 7 SIFT benchmark (31 candidates / 8 geometric inliers) remains untouched in benchmark ledgers.
- **Phase 8.3 Preservation:** Complete React demonstration UI with all 15 panels, interactive graphs, telemetry cards, and disclaimer banners remains operational.

---

## 13. Mandatory Scientific Limitations

1. **`REAL-DATA ACCURACY = N/A`**: Without ground-truth survey markers on the Moon, real-data accuracy cannot be reported as a percentage.
2. **`PHYSICAL CORRESPONDENCE NOT VALIDATED`**: In the evaluated real OHRC/TMC-2 pair, physical correspondence is rejected due to calibrated footprint non-overlap (~1.49–2.04 km separation).
3. **`REAL-LUNAR EMPIRICAL UNCERTAINTY CALIBRATION NOT ESTABLISHED`**: Uncertainty intervals reflect analytical error propagation; empirical calibration against real-lunar ground truth is not established.
4. **`SYNTHETIC POSITIVE CONTROL DOES NOT ESTABLISH REAL-LUNAR ACCURACY`**: High synthetic inlier metrics reflect pipeline consistency under known synthetic models only.
5. **No Spacecraft Tasking**: Observation proposals represent informational decision-support and do not perform orbital tasking or spacecraft maneuvering.

---

## 14. Remaining Clarification Items (for Hardening Stages)

- **Audit Item A:** The candidate-count distinction between the current demonstration instance (26 candidates) and historical Phase 7 benchmark (31 candidates / 8 inliers) is documented and exposed in `candidate_count_notes`.
- **Audit Item B:** Gate 6 dual-metric notation ($4.0\text{ px}$ image-space saturation limit vs. $15\text{ m}$ ground-space physical residual) is exposed in `gate_metrics_notes`. Formal mathematical unification will occur during Phase 8.6/8.7 hardening.

---

## 15. Next Phase Authorization Recommendation

Phase 8.4 is **COMPLETE and VALIDATED** (`DEMONSTRATION_VALIDATED`).  
Awaiting scientific jury audit and formal authorization before proceeding to **Phase 8.5 (Explainability / Provenance / Evidence Visibility)**.
