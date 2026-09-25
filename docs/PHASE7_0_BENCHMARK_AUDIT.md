# PHASE 7.0: BENCHMARK INFRASTRUCTURE AUDIT REPORT
**LunarSynapse — Physics-Aware, Self-Evolving Multi-Modal Lunar World Model**  
**Sub-Stage**: Phase 7.0 — Benchmark Infrastructure Audit  
**Status**: COMPLETED / AUDIT CERTIFIED  
**Date**: September 24, 2026  
**Baseline Test Suite**: 237 passed, 0 failed, 446 warnings in 82.74s  

---

## 1. Executive Summary
Phase 7.0 conducts a comprehensive scientific and architectural audit of LunarSynapse's existing benchmarking infrastructure, metrics, test fixtures, and evaluation engines prior to executing the Phase 7 empirical benchmark campaign (Phases 7.1 through 7.12). 

The audit reviewed:
1. Feature correspondence benchmarks (`ml/benchmark/metrics.py`, `phase2_runner.py`, `phase2_5_runner.py`, `pair_registry.py`),
2. Ground-truth and failure classification engines (`ml/benchmark/ground_truth.py`, `failure_classifier.py`),
3. Geometric and physical verification pipelines (`ml/verification/geometry.py`, `scale_spatial.py`, `physics_engine.py`, `matchers/physical_matcher.py`),
4. World Model knowledge-gap and active observation benchmarks (`ml/world_model/gap_benchmark.py`, `active_loop.py`, `uncertainty.py`, `temporal.py`),
5. Phase 6 adversarial red-team test suites (Phases 6.1 through 6.4).

The audit verified that the codebase strictly preserves the primary scientific invariant: **`PHYSICAL CORRESPONDENCE NOT VALIDATED`** for the disjoint real Chandrayaan-2 OHRC and TMC-2 observations. Key benchmark deficiencies, data leakage risks, and missing metrics were identified to guide the subsequent Phase 7 sub-stages.

---

## 2. Audit Scope & Component Inventory

| Component | File Path | Core Role | Audited Status |
| :--- | :--- | :--- | :--- |
| **Benchmark Metrics** | `outgraph/ml/benchmark/metrics.py` | Container for 28 feature, geometric, and scale metrics | **AUDITED** (Deficiencies identified) |
| **Failure Classifier** | `outgraph/ml/benchmark/failure_classifier.py` | Multi-category failure attribution and outcome classification | **AUDITED** (Hardcoded thresholds cataloged) |
| **Ground Truth Hierarchy** | `outgraph/ml/benchmark/ground_truth.py` | Evaluates ground-truth level (Level 1–4, UNKNOWN) | **AUDITED** (BBox leakage risk flagged) |
| **Pair Registry** | `outgraph/ml/benchmark/pair_registry.py` | Discovers real observation pairs and synthetic controls | **AUDITED** (Missing sensor modalities cataloged) |
| **Phase 2 Runner** | `outgraph/ml/benchmark/phase2_runner.py` | Executes baseline multi-matcher evaluation | **AUDITED** (Operational) |
| **Phase 2.5 Runner** | `outgraph/ml/benchmark/phase2_5_runner.py` | Multi-scale pyramid normalized benchmark | **AUDITED** (Operational, invariant preserved) |
| **Geometric Verifier** | `outgraph/ml/verification/geometry.py` | RANSAC homography, normalized condition, degeneracy | **AUDITED** (Phase 6.4 hardened) |
| **Scale & Spatial Verifier** | `outgraph/ml/verification/scale_spatial.py` | GSD consistency, convex hull ratio, spatial entropy | **AUDITED** (Phase 6.3 hardened) |
| **Physics Engine** | `outgraph/ml/verification/physics_engine.py` | Multi-gate evidence profile synthesis | **AUDITED** (Operational) |
| **Physical Matcher** | `outgraph/ml/matchers/physical_matcher.py` | Calibrated GroundGrid & DEM ray-tracing corridor engine | **AUDITED** (Phase 3 gates intact) |
| **Knowledge Gap Benchmark** | `outgraph/ml/world_model/gap_benchmark.py` | 8-scenario deterministic knowledge-gap test suite | **AUDITED** (Phase 5 validated) |
| **Red-Team Suites** | `outgraph/tests/test_phase6_*.py` | Hostile geometric, illumination, scale, warp suites | **AUDITED** (237/237 tests passing) |

---

## 3. Existing Metrics Audit

### 3.1 Feature Matching & Inlier Metrics
- `keypoints_source`, `keypoints_target` ($\mathbb{N}$): Raw keypoint counts extracted per image.
- `candidate_matches` ($\mathbb{N}$): Raw putative feature matches prior to geometric filtering.
- `ratio_test_matches` ($\mathbb{N}$): Matches surviving Lowe's ratio test (threshold $\tau = 0.75$).
- `geometric_inliers` ($\mathbb{N}$): Number of matches consistent with estimated homography.
- `inlier_ratio` ($[0, 1]$): Ratio of geometric inliers to candidate matches ($\frac{N_{\text{inliers}}}{N_{\text{candidates}}}$).

### 3.2 Geometric Residual & Matrix Conditioning Metrics
- `mean_reprojection_error_px` ($\mathbb{R}^+$): Arithmetic mean Euclidean residual $\frac{1}{N} \sum \|\mathbf{x}_i' - H\mathbf{x}_i\|$.
- `median_reprojection_error_px` ($\mathbb{R}^+$): 50th percentile residual (robust to outlier leakage).
- `p95_reprojection_error_px` ($\mathbb{R}^+$): 95th percentile residual (measures heavy-tail non-rigid distortion).
- `rmse_px` ($\mathbb{R}^+$): Root-mean-squared reprojection error.
- `homography_condition_number` ($\kappa(H_{\text{norm}})$): Scale-invariant condition number of normalized homography matrix.
- `homography_determinant` ($\det(H[:2, :2])$): Determinant of 2D affine component (flags area collapse/explosion).
- `corner_projection_valid` ($\mathbb{B}$): Boolean convexity and signed-area orientation check for projected frame boundary.
- `is_geometrically_stable` ($\mathbb{B}$): Composite boolean flag requiring zero degeneracy flags, inlier ratio $\ge \tau_{\text{ratio}}$, and error $\le \tau_{\text{error}}$.

### 3.3 Spatial Distribution & GSD Metrics
- `spatial_coverage_ratio` / `convex_hull_area_ratio` ($[0, 1]$): Fraction of image frame covered by inlier convex hull.
- `spatial_entropy` ($[0, 1]$): 2D spatial Shannon entropy across spatial grid cells.
- `native_gsd_source_m`, `native_gsd_target_m` ($\mathbb{R}^+$): Native spatial resolution in meters.
- `estimated_scale_ratio` ($\mathbb{R}^+$): Empirical transformation scale $\sqrt{|\det(H[:2, :2])|}$.

### 3.4 Physical Geometry Residuals (Phase 3 Engine)
- `dem_elevation_m` ($\mathbb{R}$): SLDEM2015 lunar surface elevation at source footprint.
- `parallax_vector_px` ($\mathbb{R}^2$): Expected target pixel displacement due to lunar terrain relief.
- `bidirectional_residual_m` ($\mathbb{R}^+$): Ground coordinate discrepancy after bidirectional projection.
- `rejection_reason` ($\mathbb{S}$): Specific physical gate triggering rejection (`GATE1` through `GATE6`).

---

## 4. Metric Deficiencies & Duplications

### 4.1 Duplicated Metrics
1. **`spatial_coverage_ratio` vs `convex_hull_area_ratio`**:
   - Both metrics measure $\frac{\text{Area}(\text{ConvexHull}(\text{inliers}))}{W \times H}$.
   - *Recommendation*: Deprecate `spatial_coverage_ratio` in favor of canonical `convex_hull_area_ratio`.
2. **`mean_reprojection_error_px` vs `rmse_px`**:
   - In `GeometricVerifier`, RMSE and mean reprojection error are computed over the same inlier subset. For Gaussian inlier noise, $\text{RMSE} \approx 1.25 \times \text{MeanError}$.
   - *Recommendation*: Retain both but document that RMSE is sensitive to borderline inliers, while median/p95 reprojection errors provide true robust characterization.

### 4.2 Invalid / Misleading Metrics
1. **Bounding-Box Overlap as "Ground Truth" (`ground_truth.py`)**:
   - `evaluate_ground_truth_level()` previously assigned `LEVEL_1_GEOREFERENCED` whenever bounding boxes overlapped ($[\text{lat}_{\min}, \text{lat}_{\max}] \cap [\text{lat}_{\min}', \text{lat}_{\max}'] \neq \emptyset$).
   - *Scientific Flaw*: As proven in Phase 3 and Phase 6.1, real OHRC and TMC-2 products have a ~1.77 km footprint separation despite nominal bounding-box intersection. Treating bounding-box intersection as ground truth creates false positive correspondence claims.
   - *Audit Directive*: For Phase 7, bounding-box intersection MUST NOT be classified as ground truth. Level 1 must be strictly reserved for synthetic known-transform benchmarks.
2. **Raw Inlier Ratio as "Accuracy"**:
   - Classical feature matching benchmarks often report inlier ratio as "precision."
   - *Scientific Flaw*: As proven in Phase 6.3 and 6.4, RANSAC can find 30–50 inliers on repetitive craters, resized images, or false planar fits where ground truth correspondence is false.
   - *Audit Directive*: Distinguish between algorithmic inlier consensus and verified ground-truth correspondence accuracy.

### 4.3 Missing Metrics (Required for Phase 7 Implementation)
The audit identified several metrics that must be implemented for Phase 7 benchmarks:
1. **Supervised Correspondence Accuracy**:
   - True Positives ($TP$), False Positives ($FP$), False Negatives ($FN$), True Negatives ($TN$).
   - Precision ($P = \frac{TP}{TP + FP}$), Recall ($R = \frac{TP}{TP + FN}$), F1 Score ($2 \frac{P \cdot R}{P + R}$).
   - Mean Corner Transfer Error (MCTE): $\frac{1}{4} \sum_{i=1}^4 \|\mathbf{c}_i^{\text{gt}} - H_{\text{est}} \mathbf{c}_i\|$.
2. **Transformation Parameter Recovery Errors**:
   - Translation error: $\Delta t = \|\mathbf{t}_{\text{est}} - \mathbf{t}_{\text{gt}}\|$ (px).
   - Rotation error: $\Delta \theta = |\theta_{\text{est}} - \theta_{\text{gt}}|$ (deg).
   - Scale recovery error: $\delta_s = \frac{|s_{\text{est}} - s_{\text{gt}}|}{s_{\text{gt}}}$.
3. **Uncertainty Calibration Metrics**:
   - Expected Calibration Error (ECE) across confidence bins.
   - Brier Score for binary correspondence acceptance.
   - Empirical coverage probabilities for spatial uncertainty ellipses.

---

## 5. Hardcoded Thresholds Catalog

| Component | Parameter | Hardcoded Value | Scientific Rationale | Flexibility Assessment |
| :--- | :--- | :--- | :--- | :--- |
| `GeometricVerifier` | `ransac_threshold_px` | `3.5 px` | Pushbroom jitter + epipolar tolerance | Reasonable default; sweep in 7.9 |
| `GeometricVerifier` | `min_inliers` | `6` | Minimum for overdetermined homography ($N \ge 4$) | Should be raised to $\ge 8$ for strict verification |
| `GeometricVerifier` | `min_inlier_ratio` | `0.25` | Rejection of random feature noise | Suitable for screening; sweeps required |
| `GeometricVerifier` | `max_reprojection_error` | `4.0 px` | Sub-pixel alignment threshold | Valid for nominal optics |
| `GeometricVerifier` | `max_condition_number` | `500.0` | Scale-invariant normalized condition limit | Hardened in Phase 6.4 |
| `GeometricVerifier` | `max_aspect_ratio` | `4.0` | SVD ratio limit on $H[:2, :2]$ | Hardened in Phase 6.4 |
| `ScaleSpatialVerifier` | `min_spatial_coverage` | `0.04` | Rejection of single-boulder clusters | Conservative; sweeps required |
| `ScaleSpatialVerifier` | `max_scale_discrepancy` | `3.5` | Allowed scale divergence factor | Prevents multi-GSD deception |
| `failure_classifier` | `az_diff` threshold | `90.0°` | Severe illumination divergence cutoff | Validated in Phase 6.2 |
| `KnowledgeGapDetector` | `uncertainty_threshold_m`| `50.0 m` | Lunar landmark navigation threshold | Domain-justified for landing corridor |

---

## 6. Data Leakage & Contamination Audit

### 6.1 Real vs Synthetic Separation
- **Finding**: Real data in `data/real/` contains strictly:
  - Chandrayaan-2 OHRC: `ch2_ohr_ncp_20210402T0546284043_d_img_d18`
  - Chandrayaan-2 TMC-2: `ch2_tmc_nca_20240523T1600309581_d_img_d18`
  - Authoritative DEM: SLDEM2015 south polar tile (`sldem2015_512_60s_75s_120_150.tif`)
- **Integrity**: `git status --porcelain data/real` confirmed zero modifications or derived file injections.
- **Risk Mitigation**: All synthetic benchmark generators must store artifacts in `data/synthetic/` or execute in-memory with `is_synthetic = True`. Under no circumstance may synthetic data be written to `data/real/`.

### 6.2 Sensor Modality Status
- **Finding**: In `pair_registry.py`, Priority 1 is designated as `OHRC <-> LRO NAC` and Priority 4 as `IIRS <-> Optical`.
- **Status**: Neither LROC NAC nor IIRS data is currently present in `data/real/`.
- **Audit Directive**: Phase 7 benchmarks MUST NOT claim real IIRS or LROC validation. Any multimodal tests must be explicitly labeled `is_synthetic = True` (Level 1/2) and reported as controlled synthetic evaluations.

### 6.3 Test-Set Contamination
- **Finding**: Parameter thresholds in `GeometricVerifier` and `failure_classifier.py` were set based on engineering domain constraints.
- **Audit Directive**: In Phase 7.9 (Robustness Curves / Parameter Sweep), evaluation datasets must be partitioned into DEVELOPMENT and TEST sets to prevent threshold overfitting on test metrics.

---

## 7. Audit of Phase 6 Red-Team Baseline
The existing test suite was executed in its entirety to establish the authoritative Phase 7.0 baseline:
- **Total Test Files**: 34
- **Total Tests Run**: **237**
- **Passed**: **237**
- **Failed**: **0**
- **Warnings**: **446** (Pydantic / standard library datetime deprecation warnings only)
- **Runtime**: **82.74 seconds**

All Phase 6 red-team defense capabilities were verified active:
1. **Phase 6.1**: Hostile geometric boundaries, out-of-grid coordinates, and datum shifts intercepted.
2. **Phase 6.2**: Solar illumination shifts (azimuth, elevation, incidence) differentiated from morphology changes.
3. **Phase 6.3**: Multi-GSD scale deceptions and missing GSD metadata handled without false confirmation.
4. **Phase 6.4**: Extreme homographies, vanishing line poles, anisotropic warps, and reflections intercepted.

---

## 8. Evaluation Hierarchy for Phase 7
To prevent overclaiming, Phase 7 benchmarks will strictly adhere to the following six-level hierarchy:

| Level | Benchmark Category | Data Provenance | Ground Truth Source | Allowed Claims |
| :---: | :--- | :--- | :--- | :--- |
| **0** | Unit-Test Correctness | Synthetic / Mock | Programmatic invariants | Code correctness |
| **1** | Known-Transform Benchmark | Synthetic Image Pairs | Ground-truth transformation matrix $H_{\text{gt}}$ | Controlled correspondence accuracy |
| **2** | Physically Controlled Benchmark | Synthetic Terrain / Sun-Angle | Synthetic DEM + ray-traced solar vectors | Controlled physical gate performance |
| **3** | Real Geometric Consistency | Real OHRC & TMC-2 | Calibrated GroundGrid CSVs | Calibrated spatial non-overlap |
| **4** | Real Terrain / DEM Consistency | Real OHRC, TMC-2, SLDEM2015 | Authoritative DEM elevation | Physical ray-tracing consistency |
| **5** | Independent Real Tie Points | Real Multi-Sensor Images | Independently verified human/instrument tie points | Supervised real-world accuracy (Currently Unavailable) |
| **6** | Independent Scientific Validation | Multi-Mission Overflights | Peer-reviewed external ground truth | Operational deployment readiness (Currently Unavailable) |

---

## 9. Recommendations for Phase 7 Execution
1. **Implement Canonical Benchmark Metric Calculator**: Develop a dedicated Phase 7 metric evaluation module (`outgraph/ml/benchmark/evaluator.py`) providing supervised $TP/FP/TN/FN$, Precision, Recall, F1, MCTE, and parameter errors for synthetic ground-truth pairs.
2. **Enforce Absolute Ground-Truth Rule**: In Phase 7.6 (Real Lunar Data Benchmark), explicitly report candidate match statistics and physical gate rejections while barring fabricated "ground-truth accuracy" numbers.
3. **Preserve Phase 3 Invariant**: Maintain `PHYSICAL CORRESPONDENCE NOT VALIDATED` for the real disjoint OHRC/TMC-2 observations across all reporting.
4. **Partition Synthetic Datasets**: Use explicit random seeds and separate parameter ranges for development tuning vs benchmark test sets in Phase 7.1 through 7.4.

---

## 10. Audit Certification
Phase 7.0 Benchmark Infrastructure Audit is **COMPLETED AND CERTIFIED**.  
The testing infrastructure, failure classifiers, and physical verification gates are sound, consistent, and ready for Phase 7.1 execution.
