# PHASE 6.4: GEOMETRIC WARP / HOMOGRAPHY DECEPTION ATTACK REPORT
**LunarSynapse — Physics-Aware, Self-Evolving Multi-Modal Lunar World Model**  
**Sub-Stage**: Phase 6.4  
**Status**: COMPLETED / DEFENSES VALIDATED  
**Date**: September 24, 2026  
**Provenance**: Controlled Synthetic Experiments (`is_synthetic = True`) & Real Data Regression (`data/real/` strictly read-only)

---

## 1. Executive Summary
Phase 6.4 red-teamed LunarSynapse against deceptive, adversarial, and degenerate geometric transformations (homographies, perspective warps, anisotropic distortions, non-rigid deformations, and orientation flips). The objective was to determine whether an attacker or sensor distortion could construct a mathematically convincing 2D transformation that achieves apparent numerical consensus while deforming physical lunar terrain.

Across 17 dedicated adversarial scenarios (Scenarios A through Q), LunarSynapse intercepted all malicious and degenerate transformations. Production code in `GeometricVerifier` was scientifically hardened to address two genuine architectural weaknesses: scale-dependent condition number evaluation and unconstrained anisotropic aspect-ratio stretching. Following this correction, the full system regression suite passed with **237 passed, 0 failed**. Raw data integrity in `data/real/` remained strictly pristine, and the core invariant `PHYSICAL CORRESPONDENCE NOT VALIDATED` was preserved.

---

## 2. Attack Objective
Determine whether an attacker can construct a mathematically convincing geometric transform that causes LunarSynapse to accept a false correspondence, produce false geometric confidence, or bypass physical geometry gates. The system must enforce that a mathematically valid transform cannot bypass physical validation.

---

## 3. Threat Model
The adversary exploits the flexibility of 8-degree-of-freedom planar projective transformations ($H \in \mathbb{R}^{3 \times 3}$) or non-rigid warps to manipulate keypoint positions:
1. **Vanishing-Line Injection**: Projective warps placing the horizon line / vanishing pole ($w' = H_{20}x + H_{21}y + H_{22} = 0$) directly across the image plane, creating severe singularities.
2. **Corner-Folding / Bowtie Inversion**: Projective transforms that invert vertex winding or create self-intersecting non-convex boundary polygons.
3. **Condition Number Exploitation**: Near-singular matrices with extreme condition numbers ($\kappa(H) > 500$) that are numerically unstable and blow up upon inverse mapping.
4. **Reflection & Chirality Reversal**: Transformations with negative determinants ($\det(H) < 0$ or $\det(H[:2, :2]) < 0$) that mirror the lunar surface, violating camera optical physics.
5. **Anisotropic Stretch Attacks**: Severe aspect-ratio distortions (e.g. 10:1) that stretch craters along one axis while preserving local descriptor matches.
6. **Non-Rigid / Local Non-Linear Deformations**: Sinusoidal surface ripples, piecewise discontinuous half-frame displacements, and thin-plate-spline radial distortions attempting to deceive RANSAC consensus.
7. **Adversarial Frame-Collapse**: Transformations fitting a tight cluster of points in the image center while collapsing or exploding the surrounding frame.

---

## 4. Existing Defense Before Attack
Prior to Phase 6.4, `GeometricVerifier` implemented basic checks:
- RANSAC inlier thresholding (`min_inliers=6`, `min_inlier_ratio=0.25`, `max_reprojection_error=4.0px`).
- Raw condition number check (`cond = np.linalg.cond(H) > 500.0`).
- Affine determinant bounds (`0.01 < det < 100.0` and `det(H) > 0`).
- Vanishing line check (`|w'| < 0.1`).
- Corner convexity check (`len(convexHull) == 4` and `cv2.isContourConvex`).
- Physical GroundGrid / DEM gates in `PhysicalCandidateEngine`.

---

## 5. Attack Scenarios

| Scenario | Attack Description | Geometric Formulation | Expected Status |
| :--- | :--- | :--- | :--- |
| **A** | Valid rigid transformation | $\theta=5^\circ, t_x=15, t_y=20$ | `GEOMETRICALLY_STABLE` |
| **B** | Mild affine distortion | Scale $1.04$, shear $0.03$, rotation $2^\circ$ | `GEOMETRICALLY_STABLE` |
| **C** | Moderate perspective warp | Physically plausible tilt ($H_{20}=10^{-5}, H_{21}=-2\times 10^{-5}$) | `GEOMETRICALLY_STABLE` |
| **D** | Projective homography | Well-conditioned projective homography | `GEOMETRICALLY_STABLE` |
| **E** | Extreme perspective homography | Vanishing line inside frame ($w' < 0.1$) | `VANISHING_LINE_IN_FRAME_POLE` |
| **F** | Corner-folding homography | Bowtie self-intersecting polygon | `NON_CONVEX_FLIPPED_CORNER_PROJECTION` or `TOO_FEW_INLIERS` |
| **G** | Nearly singular homography | Rank-deficient matrix with linearly dependent rows | `HIGH_CONDITION_NUMBER` / `EXTREME_DETERMINANT` |
| **H** | High condition number | $\kappa(H) > 500$ threshold breach | `HIGH_CONDITION_NUMBER` |
| **I** | Reflection | Mirror matrix $x \to -x$ ($\det < 0$) | `NEGATIVE_HOMOGRAPHY_DETERMINANT` / `EXTREME_DETERMINANT` |
| **J** | Rotation + reflection | Orthogonal matrix with $\det = -1$ | `NEGATIVE_HOMOGRAPHY_DETERMINANT` |
| **K** | Anisotropic warp | 10:1 aspect ratio stretch ($s_x=10.0, s_y=1.0$) | `EXTREME_ANISOTROPIC_DISTORTION` |
| **L** | Local nonlinear warp | Sinusoidal ripple $\Delta x = 18 \sin(y/30)$ | `REJECTED` (fails inlier ratio / error) |
| **M** | Piecewise deformation | Top half $+40\text{px}$, bottom half $-40\text{px}$ | `REJECTED` (inlier ratio $\le 0.50$) |
| **N** | Thin-plate-spline deformation | Smooth non-rigid radial displacement ($60\text{px}$) | `REJECTED` (inlier ratio $< 0.50$) |
| **O** | Adversarial frame collapse | Inliers match in center, scale $0.05\times$ | `EXTREME_DETERMINANT` / `REJECTED` |
| **P** | False RANSAC consensus | 6 collinear points in tight cluster | `REJECTED` (spatial score $< 0.20$) |
| **Q** | Physical Invariant Check | Real OHRC vs TMC-2 under forced homography | `GATE3_TARGET_OUTSIDE_CALIBRATED_SWATH` |

---

## 6. Test Design
Tests were implemented in `outgraph/tests/test_phase6_4_homography_deception.py` with synthetic keypoint grids ($8 \times 8 = 64$ points on a $512 \times 512$ image frame). Synthetic transforms were applied directly to coordinates, evaluating:
1. Homography estimation via OpenCV RANSAC,
2. Inlier filtering,
3. Determinant calculations,
4. Scale-invariant normalized condition number,
5. SVD singular value ratio of $H[:2, :2]$ (aspect ratio distortion),
6. Corner projection convexity and signed-area orientation preservation,
7. Mean, median, and 95th percentile reprojection errors,
8. Spatial coverage and convex hull area ratios,
9. Physical candidate engine evaluation on real Chandrayaan-2 Level-2 products.

---

## 7. Real vs Synthetic Data
- **Synthetic Data**: Scenarios A through P were executed purely in memory on synthetic grid coordinates with explicit parameter controls. All test fixtures operated with `is_synthetic = True`.
- **Real Data**: Scenario Q evaluated the calibrated Level-2 GroundGrid and DEM interface for real Chandrayaan-2 OHRC (`ch2_ohr_ncp_20210402T0546284043`) and TMC-2 (`ch2_tmc_nca_20240523T1600309581`).
- `data/real/` was maintained in strictly read-only mode.

---

## 8. Results
All 17 scenarios produced the scientifically required outcomes:
- **Plausible Transforms (A, B, C, D)**: Validated as geometrically stable with low reprojection residuals ($< 0.1\text{ px}$) and low condition numbers.
- **Singular & Ill-Conditioned Transforms (E, G, H)**: Detected and flagged with `VANISHING_LINE_IN_FRAME_POLE`, `HIGH_CONDITION_NUMBER`, and `EXTREME_DETERMINANT`.
- **Chirality Inversion (I, J)**: Intercepted via `NEGATIVE_HOMOGRAPHY_DETERMINANT` and oriented corner area checks.
- **Anisotropic Distortion (K)**: Successfully caught by the newly added `EXTREME_ANISOTROPIC_DISTORTION` check ($\rho = 10.0 > 4.0$).
- **Non-Rigid Warps (L, M, N)**: Correctly rejected due to inlier fragmentation ($< 50\%$ inliers) and elevated residuals.
- **False Spatial Consensus (O, P)**: Intercepted by extreme determinant and spatial entropy / convex hull ratio gates.
- **Physical Invariant (Q)**: Real OHRC/TMC-2 evaluation was rejected by `GATE3_TARGET_OUTSIDE_CALIBRATED_SWATH`.

---

## 9. Exact Test Counts
- **Phase 6.4 Test Suite** (`test_phase6_4_homography_deception.py`):
  - Tests run: **17**
  - Passed: **17**
  - Failed: **0**
  - Warnings: **0**
  - Runtime: **8.70s**
- **Affected Subsystem Tests** (`test_phase2_5_1_audit.py`, `test_phase6_1_geometric_boundary.py`, `test_phase6_3_scale_deception.py`, `test_phase6_4_homography_deception.py`):
  - Tests run: **83**
  - Passed: **83**
  - Failed: **0**
  - Runtime: **14.91s**
- **Full Repository Regression Suite** (`outgraph/tests/`):
  - Tests run: **237**
  - Passed: **237**
  - Failed: **0**
  - Warnings: **446**
  - Runtime: **99.18s (1m 39s)**

---

## 10. False Positive Analysis
- **Pre-Correction Vulnerability**: Before the Phase 6.4 fix, a harmless translation of 25 pixels in a $512 \times 512$ image produced an unnormalized condition number of $\kappa(H) = 627$, triggering a false positive rejection under the hardcoded $\kappa > 500$ threshold.
- **Post-Correction Performance**: With Hartley coordinate normalization, the normalized condition number for the same 25-pixel translation was $\kappa(H_{\text{norm}}) \approx 1.05$, correctly accepting valid physical transformations without false positive rejection.

---

## 11. False Negative / Missed Detection Analysis
- **Pre-Correction Vulnerability**: An unconstrained 10:1 anisotropic stretch (`H = diag(10.0, 1.0, 1.0)`) had $\det(H) = 10.0$ and $\kappa(H) = 10.0$, passing all prior checks as a false negative.
- **Post-Correction Performance**: Evaluating the singular values of $H[:2, :2]$ intercepted the 10:1 stretch as `EXTREME_ANISOTROPIC_DISTORTION`, eliminating the false negative.

---

## 12. Scientific Interpretation
- A planar projective homography is an 8-DOF mathematical abstraction. While it models planar surfaces under perspective projection, it is susceptible to unphysical distortions (vanishing poles, anisotropic stretches, reflections) if evaluated purely on inlier counts.
- Normalizing coordinates prior to condition number evaluation is mathematically necessary to decouple image frame resolution from geometric stability.
- Physical validation gates (GroundGrid, DEM, illumination) provide an indispensable second defense layer that prevents even mathematically perfect homographies from fabricating cross-sensor correspondence between disjoint images.

---

## 13. Discovered Weaknesses
Two architectural weaknesses were identified in baseline `GeometricVerifier`:
1. **Unnormalized Condition Number Calculation**: `np.linalg.cond(H)` was evaluated directly in raw pixel coordinates, causing condition numbers to scale quadratically with pixel translation ($\|t\|^2$). In addition, line 165 hardcoded `if cond > 500.0:` rather than using `self.max_condition_number`.
2. **Missing Anisotropic Aspect-Ratio Check**: Optical camera transformations must preserve approximate orthogonality and uniform scale. An anisotropic stretch of 10:1 was previously accepted because its determinant ($10.0$) and raw condition number ($10.0$) fell within standard scalar bounds.

---

## 14. Production Changes
Modified `outgraph/ml/verification/geometry.py`:
1. **Scale-Invariant Normalized Condition Number**:
   Normalized image coordinates by image dimension $S = \max(h, w, 1)$ via $T_{\text{norm}} = \text{diag}(1/S, 1/S, 1)$ and $H_{\text{norm}} = T_{\text{norm}} H T_{\text{norm}}^{-1}$. Evaluated condition number on $H_{\text{norm}}$ against `self.max_condition_number`.
2. **Anisotropic Aspect-Ratio Check**:
   Computed SVD on $H[:2, :2]$: $\rho = \sigma_{\max} / \sigma_{\min}$. If $\rho > 4.0$, flagged `EXTREME_ANISOTROPIC_DISTORTION`.
3. **Oriented Corner Check**:
   Added signed polygon area check `cv2.contourArea(..., oriented=True)` on projected corners to guarantee that orientation/chirality is preserved.
4. **Tail Residual Tracking**:
   Flagged `EXTREME_TAIL_RESIDUAL` when $p_{95} > 25.0\text{ px}$.

---

## 15. Regression Tests
- Added `outgraph/tests/test_phase6_4_homography_deception.py` containing 17 comprehensive unit tests.
- Re-executed `test_phase2_5_1_audit.py` to ensure all existing condition number, negative determinant, vanishing pole, and failure classifier tests remain 100% passing.

---

## 16. Raw Data Integrity
- Verified via `git status --porcelain data/real`: zero modifications to raw data files.
- Original OHRC and TMC-2 images, XML labels, and GroundGrid CSVs remain completely unmodified.

---

## 17. Phase 3 Preservation
- Phase 3 physical geometry and GroundGrid boundary gates remain fully active.
- Confirmed in Scenario Q: `PhysicalCandidateEngine.evaluate_candidate` strictly rejected real OHRC/TMC-2 pairing with `GATE3_TARGET_OUTSIDE_CALIBRATED_SWATH`.
- Scientific invariant preserved: `PHYSICAL CORRESPONDENCE NOT VALIDATED`.

---

## 18. Phase 4 Preservation
- World Model entity persistence and evidence graph structures remain fully intact.
- Unstable or rejected homographies are strictly blocked from associating with entities or confirming features in the world graph.

---

## 19. Phase 5 Preservation
- Active loop and temporal reasoning engines remain fully operational.
- All Phase 5 observation matrix, cross-sensor validation, and knowledge-gap tests passed without error.

---

## 20. Limitations
1. **Planar Homography Assumption**: Homography verification models terrain locally as planar. On extreme high-relief lunar terrain (e.g. crater rims with vertical relief $> 2\text{ km}$), parallax displacement requires full 3D ray-tracing against the calibrated DEM rather than 2D planar projective models.
2. **Local Feature Outlier Blindness in RANSAC**: Standard OpenCV RANSAC minimizes reprojection error solely over the inlier subset. If non-linear distortion leaves a small subset of points locally coplanar, secondary metrics (inlier ratio, all-point residuals, spatial coverage) must be enforced.

---

## 21. Remaining Unknowns
- Behavior of higher-order rational polynomial camera models (RPCs) under severe epipolar misalignment in the absence of GroundGrid tables.

---

## 22. Final Stage Status
**PHASE 6.4: RED-TEAM VALIDATED**  
All geometric warp and homography deception attacks were successfully defended. Production code was hardened with scale-invariant normalization and aspect-ratio checks. Full regression suite of 237 tests passed with zero failures.
