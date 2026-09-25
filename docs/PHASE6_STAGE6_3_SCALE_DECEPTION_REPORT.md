# PHASE 6.3: SCALE DECEPTION & MULTI-GSD ADVERSARIAL ATTACK REPORT
**LunarSynapse — Physics-Aware, Self-Evolving Multi-Modal Lunar World Model**  
**Sub-Stage**: Phase 6.3  
**Status**: COMPLETED / DEFENSES VALIDATED  
**Date**: September 24, 2026  
**Provenance**: Controlled Synthetic Experiments (`is_synthetic = True`) & Real Data Regression (`data/real/` strictly read-only)

---

## 1. Objective
The primary objective of Phase 6.3 is to aggressively red-team the LunarSynapse correspondence and verification engines against incorrect, inconsistent, ambiguous, and deceptive image-scale assumptions. Specifically, this phase evaluates whether apparent numerical feature agreement under an incorrect scale transformation can induce:
- False feature correspondence across sensors,
- False geometric confidence from homography estimation,
- False entity association in the lunar world graph,
- Invalid physical evidence ingestion, or
- Unjustified confirmation.

The pipeline must rigorously differentiate **numerical image similarity** from **physically valid multi-sensor correspondence**.

---

## 2. Threat Model
The adversary or sensor defect assumes several deceptive strategies:
1. **Direct Scale Misalignment**: Pairing datasets with erroneous scale transformations (e.g., 2×, 4×, 10×, or small perturbations like 10%–25% scale error) where repetitive lunar features (craters, boulders) yield local descriptor similarity.
2. **False Scale Compensation via Warping**: Forcing an ill-conditioned homography or non-rigid projective warp that artificially fits keypoints across mismatched scales to achieve visually plausible overlay.
3. **Extreme Anisotropic Distortion (Aspect-Ratio Deception)**: Applying severe anisotropic stretching ($s_x \neq s_y$, e.g., 2:1, 10:1, or 1:2) that tricks local feature matchers into high raw match counts while deforming actual physical lunar topography.
4. **Resize-Then-Match Attack**: Pre-scaling high-resolution images down to low-resolution pixel grids to generate hundreds of artificial descriptor matches, attempting to overwhelm downstream physics gates by raw match count alone.
5. **Metadata Perturbation & Omission**: Injecting corrupted GSD metadata (e.g., claiming 0.30 m/px when actual is 0.26 m/px, or 5.0 m/px when actual is 6.07 m/px) or completely omitting GSD metadata (`None`), testing whether the pipeline silently accepts unverified scales or crashes due to missing attributes.
6. **Multi-GSD Ambiguity**: Introducing multiple competing scale hypotheses where visual evidence is ambiguous and verifying that the pipeline does not prematurely force a single deterministic transformation.

---

## 3. Scale Configurations
The red-team test matrix evaluated the following synthetic and real configurations:
- **Baseline Correct Scale**: $s = 1.0$ (identical GSD $1.0\text{ m/px} \leftrightarrow 1.0\text{ m/px}$) with spatial coverage $\ge 0.15$.
- **Spatially Clustered Scale**: $s = 1.0$, but keypoints restricted to a tight spatial cluster ($10 \times 10\text{ px}$), evaluating whether scale agreement alone can validate correspondence.
- **Moderate & Extreme Scale Errors**: Scaling factors $s \in \{0.05, 0.75, 1.25, 2.0, 4.0, 10.0\}$.
- **Adversarial Homography Warping**: $H = \text{diag}(2.5, 2.5, 1.0)$ with non-zero projective terms $H_{20} = 10^{-4}, H_{21} = 10^{-4}$ forced across $1.0\text{ m/px}$ products.
- **Anisotropic Scaling**: $s_x / s_y \in \{2.0 / 0.5, 10.0 / 0.2\}$.
- **Scale Perturbation**: Reported GSD $0.30\text{ m/px}$ on ground truth $0.26\text{ m/px}$ (15.4% error) and reported $5.0\text{ m/px}$ on ground truth $6.07\text{ m/px}$ (17.6% error).
- **Missing Scale**: `pixel_resolution_m = None` (GSD status `UNKNOWN`).

---

## 4. Sensor and GSD Assumptions
- **Real CH2 OHRC**: Nominal GSD $\approx 0.26\text{ m/pixel}$ (calibrated ground swath ~3 km).
- **Real CH2 TMC-2**: Nominal GSD $\approx 6.07\text{ m/pixel}$ (calibrated ground swath ~20 km).
- **Cross-Sensor Scale Ratio**: $\approx 6.07 / 0.26 \approx 23.35\times$.
- **Real Overlap Status**: Non-overlapping footprints in the calibrated Level-2 repository (verified in Phase 3 and Phase 2.5/2.5.1).

---

## 5. Synthetic Provenance
All adversarial scale test cases were generated synthetically and programmatically tagged:
- `is_synthetic = True` on all instantiated `LunarProduct` objects.
- `ProvenanceRecord.source_name = "SYNTH"`, `dataset_source = "SYNTHETIC"`.
- Zero synthetic data was written into `data/real/`.
- No artificial overlap was fabricated between the real OHRC and TMC-2 products.

---

## 6. Scenario Results

| Scenario | Attack Type | Configuration | Expected Outcome | Observed Outcome | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **A1** | Correct Scale & Distribution | $s=1.0$, coverage $> 0.15$ | `is_valid = True`, high scale score | Verified ($s \approx 1.0$, score $> 0.75$) | **DEFENDED** |
| **A2** | Scale Agreement Alone | $s=1.0$, clustered in 10px box | `is_valid = False` (poor coverage) | Rejected (`is_valid = False`, coverage $< 0.05$) | **DEFENDED** |
| **B1** | Severe Scale Discrepancy | $s = 4.0\times$ error | `is_valid = False`, score $\le 0.25$ | Rejected (score $\le 0.25$, valid = False) | **DEFENDED** |
| **B2** | Extreme Scale Discrepancy | $s = 10.0\times$ error | `is_valid = False`, score $\le 0.10$ | Rejected (score $\le 0.10$, valid = False) | **DEFENDED** |
| **B3** | Inverted Scale Mismatch | $s = 0.05\times$ error | `is_valid = False`, score $\le 0.10$ | Rejected (score $\le 0.10$, valid = False) | **DEFENDED** |
| **C** | False Scale Compensation | Homography warp forcing 2.5× on 1.0m | Rejected by Physics Engine (`!= VERIFIED`) | Rejected (`profile.status == REJECTED`) | **DEFENDED** |
| **D1** | Anisotropic Scaling (2:1) | $s_x=2.0, s_y=0.5$ | Flagged as degenerate ($s_x \neq s_y$) | Degenerate (`is_valid = False`) | **DEFENDED** |
| **D2** | Extreme Anisotropic (50:1) | $s_x=10.0, s_y=0.2$ | Flagged as degenerate | Degenerate (`is_valid = False`) | **DEFENDED** |
| **E** | Resize-Then-Match Attack | 100 inliers artificially fitted under $5\times$ | High match count cannot override scale gate | Rejected (`is_valid = False`, score $\le 0.25$) | **DEFENDED** |
| **F1** | Missing GSD Metadata | `src_res = None, tgt_res = None` | Preserves neutral `UNKNOWN` without crashing | Handled gracefully (score = 0.5, `UNKNOWN`) | **DEFENDED** |
| **F2** | Perturbed GSD Metadata | GSD perturbed by 15.4% and 17.6% | Fails tight physical scale consistency check | Divergence caught (`is_valid = False`) | **DEFENDED** |
| **G** | Multi-GSD Ambiguity | Competing scale hypotheses near margin | Preserves `AMBIGUOUS` / `REJECTED` | Not accepted (`AMBIGUOUS` preserved) | **DEFENDED** |
| **H1** | Phase 2.5 Decision String | Official Phase 2.5 artifact check | Preserves `SCALE_EFFECT_OBSERVED_BUT_GEOMETRICALLY_UNSTABLE` | Verified intact | **DEFENDED** |
| **H2** | Real OHRC/TMC-2 Non-Overlap | Real Level-2 GroundGrid Gate 3/4 evaluation | Rejection (`is_accepted = False`) | Rejected (`GATE3_TARGET_OUTSIDE_CALIBRATED_SWATH`) | **DEFENDED** |

---

## 7. Matcher Behavior
- **Local Feature Matchers (SIFT, ORB, LoFTR/SuperPoint fallback)**: Local feature matchers operate in normalized descriptor space and are scale-invariant by design. Consequently, when an image is scaled or resized, local matchers readily discover dozens to hundreds of candidate correspondences despite massive physical GSD discrepancies.
- **Defense Validation**: The red-team tests proved that high candidate match count ($N \ge 100$) and high raw descriptor confidence provide zero guarantee of physical correspondence. Raw match counts are treated strictly as unverified algorithmic hints.

---

## 8. Geometric Verification Behavior
- The `GeometricVerifier` and `SpatialHomographyAudit` compute:
  1. Homography condition number $\kappa(H) = \|H\| \cdot \|H^{-1}\|$,
  2. Determinant sign $\det(H) > 0$ (preserving spatial orientation),
  3. Vanishing line pole check (rejecting horizon singularities in field of view),
  4. Anisotropic aspect-ratio distortion: $\Delta_{\text{scale}} = |s_x - s_y| / \max(s_x, s_y)$.
- In Scenarios D1 and D2, anisotropic deformations ($2:1$ and $50:1$) caused the geometric verifier to immediately classify the candidate transformation as `GEOMETRICALLY_DEGENERATE`, rejecting the transformation regardless of inlier support.

---

## 9. Physical Verification Behavior
- The `ScaleSpatialVerifier` and `PhysicsVerificationEngine`:
  1. Calculate empirical transformation scale $s_{\text{emp}} = \sqrt{|h_{00} h_{11} - h_{01} h_{10}|}$,
  2. Compute expected physical scale ratio $s_{\text{phys}} = \text{tgt\_res\_m} / \text{src\_res\_m}$,
  3. Evaluate scale ratio discrepancy $\delta_s = |s_{\text{emp}} - s_{\text{phys}}| / s_{\text{phys}}$.
- When $\delta_s > 0.20$, the scale consistency score drops below the acceptance threshold ($< 0.70$).
- When spatial coverage or convex hull area is deficient ($< 0.15$), scale verification rejects the match even if $s_{\text{emp}} \approx s_{\text{phys}}$ (preventing false confirmation from localized feature clusters).

---

## 10. Evidence-Fusion Behavior
- The Bayesian and Dempster-Shafer evidence fusion engines incorporate scale verification scores as an independent gating modality.
- When `ScaleSpatialResult.is_valid == False`, the overall physics evidence profile is marked `REJECTED` or `UNCERTAIN`.
- No single observation modality is permitted to dominate the fusion vector: geometric inlier counts cannot override a scale divergence, nor can scale consistency override an ill-conditioned homography.

---

## 11. Entity Lifecycle Behavior
- In the Lunar World Model (`outgraph.ml.world_model.entity` and `graph`), candidate entities associated with correspondences failing scale verification are blocked from transitioning to `CONFIRMED`.
- Competing multi-scale observations maintain split entity hypotheses or remain in the `PROVISIONAL` / `AMBIGUOUS` state until independent multi-view geometry or calibrated DEM alignment confirms or refutes them.

---

## 12. False-Positive Analysis
- **Unprotected Pipeline Vulnerability**: An unprotected matching pipeline accepting homographies with $\ge 20$ inliers would have accepted the forced 2.5× warp (Scenario C) and the $5\times$ resized image (Scenario E), generating false surface associations.
- **Protected Pipeline Performance**: With `ScaleSpatialVerifier` and `PhysicsVerificationEngine` active, 100% of adversarial scale deformations were intercepted, producing zero false-positive verifications.

---

## 13. Vulnerabilities Discovered
During the Phase 6.3 red-team audit, two concrete weaknesses were uncovered in baseline code:
1. **Missing GSD Metadata `TypeError` Crash**:
   In `ScaleSpatialVerifier.verify()`, passing `src_res_m=None` or `tgt_res_m=None` resulted in an unhandled `TypeError: float() argument must be a string or a real number, not 'NoneType'` during scale ratio calculation.
2. **Physics Verification Engine Ingestion of `None` Resolution**:
   In `PhysicsVerificationEngine.verify_correspondence()`, extracting `spatial_resolution_m` from metadata without null guards passed `None` directly into arithmetic routines, risking silent failure or crash rather than recording an explicit `UNKNOWN` scale state.

---

## 14. Corrections Made
1. **Hardened `ScaleSpatialVerifier.verify()`** in `outgraph/ml/verification/scale_spatial.py`:
   - Updated signature to accept `Optional[float]` for `src_res_m` and `tgt_res_m`.
   - Added explicit guard: when either resolution is `None` or non-positive ($\le 0$), the scale score is assigned neutral `0.5` (`UNKNOWN` status), an informative warning is logged, and `is_valid` is set to `False` (blocking unverified scale confirmation without crashing).
2. **Hardened `PhysicsVerificationEngine.verify_correspondence()`** in `outgraph/ml/verification/physics_engine.py`:
   - Safely extract resolution from `source_product.metadata.pixel_resolution_m` with type checking, safely falling back to `None` if absent.
   - Handled `UNKNOWN` scale status in evidence profile synthesis.

---

## 15. Phase 2.5 Regression Result
- The Phase 2.5 scale-normalized benchmark suite was executed via `test_phase2_5_scale.py` and `test_phase2_5_1_audit.py`.
- **Outcome**: 11 passed, 0 failed.
- The official scientific decision code was verified intact:
  `SCALE_EFFECT_OBSERVED_BUT_GEOMETRICALLY_UNSTABLE`
- The conclusion that scale-normalization enables candidate feature detection while failing rigorous spatial and homographic stability remains firmly established.

---

## 16. Phase 3 Preservation
- Phase 3 physical geometry and GroundGrid boundary gates remain fully intact.
- Verified in `TestScenarioH_RealOHRCTMC2Regression::test_physical_correspondence_not_validated_invariant_holds`:
  Evaluating real OHRC vs TMC-2 products through `PhysicalCandidateEngine` yielded rejection via `GATE3_TARGET_OUTSIDE_CALIBRATED_SWATH`.
- Scientific invariant preserved: `PHYSICAL CORRESPONDENCE NOT VALIDATED`.

---

## 17. Phase 4 Preservation
- Phase 4 World Model components (`LunarEntity`, `WorldGraph`, `UncertaintyModel`, `EvidenceProfile`) remain fully operational.
- Verified across full regression: entity lifecycle state machines correctly handle `PROVISIONAL`, `CONFIRMED`, and `AMBIGUOUS` transitions.

---

## 18. Phase 5 Preservation
- Phase 5 active perception, observation matrix, and temporal reasoning modules remain fully operational.
- Full regression tests (`test_phase5_observation_matrix.py`, `test_phase5_cross_sensor_validation.py`, `test_phase5_gap_benchmark.py`, `test_phase5_active_loop.py`) passed with zero errors.

---

## 19. Raw-Data Integrity
- `data/real/` was verified completely untouched via `git status --porcelain data/real`.
- No raw binary, raster, or geometry files were modified or overwritten.
- All real sensor data remains strictly in its original read-only state.

---

## 20. Test Results
- **Dedicated Phase 6.3 Test Suite**: `outgraph/tests/test_phase6_3_scale_deception.py`
  - Tests run: **14**
  - Passed: **14**
  - Failed: **0**
  - Runtime: **40.20s**
- **Existing Scale Regression Suite**: `test_phase2_5_scale.py` + `test_phase2_5_1_audit.py`
  - Tests run: **11**
  - Passed: **11**
  - Failed: **0**
  - Runtime: **13.36s**
- **Full System Regression Suite**: `outgraph/tests/`
  - Tests run: **220**
  - Passed: **220**
  - Failed: **0**
  - Warnings: 446 (Pydantic / standard library deprecation warnings only)
  - Runtime: **77.79s (1m 17s)**

---

## 21. Scientific Limitations
1. **Linear Scale Approximation**: Scale verification currently models cross-sensor scale factor as locally isotropic or affine ($s = \sqrt{\det(H)}$). For extreme high-relief lunar terrain (e.g., deep crater walls, central peaks), perspective foreshortening introduces non-linear local scale gradients that require full 3D DEM ray-tracing to accurately resolve.
2. **Metadata Dependency**: If GSD metadata is completely absent and no physical DEM or calibrated GroundGrid is available, the system conservatively defaults to `UNKNOWN` and rejects correspondence. An autonomous multi-scale self-calibration mechanism (e.g., via crater size-frequency distributions) is an open research problem.
3. **Descriptor Invariance Paradox**: Modern deep learning matchers (e.g., LoFTR, SuperPoint) are trained to be scale-invariant, which creates a natural adversarial vulnerability: they intentionally match across different scales, requiring post-hoc physical geometry filters to reject physically impossible scale pairings.
