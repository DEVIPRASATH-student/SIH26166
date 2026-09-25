# LUNARSYNAPSE — PHASE 2.5.1 SCIENTIFIC VALIDATION AUDIT REPORT
**Target Product Pair:** REAL OHRC (`ch2_ohr_ncp_20210402T0546284043_d_img_d18`, GSD: 0.26 m/px) ↔ REAL TMC-2 (`ch2_tmc_nca_20240523T1600309581_d_img_d18`, GSD: 6.07 m/px)  
**Footprint Overlap:** 65.03% verified geographic overlap  
**Audit Objective:** Evaluate whether scale-normalized correspondence improvements represent geometrically stable surface matching or degenerate matrix estimation  
**Summary Decision Code:** `SCALE_EFFECT_OBSERVED_BUT_GEOMETRICALLY_UNSTABLE`

---

## 1. Executive Summary

Phase 2.5 established that downsampling real Chandrayaan-2 OHRC imagery ($0.26\text{ m/px}$) toward TMC-2 resolution ($6.07\text{ m/px}$) increases raw keypoint detection density and raw RANSAC candidate matches across multiple feature matchers:
- **Raw candidate matches:** Increased from **31** (Level 0 baseline) to **66** (Level 4 downsampled).
- **Raw RANSAC inliers:** Increased from **8** (Level 0 baseline) to **14** (Level 5 TMC-equivalent).

However, **Phase 2.5.1 Scientific Audit confirms that 100% of estimated 2D planar homographies across all 30 pyramid level runs are GEOMETRICALLY DEGENERATE.**

```
[Level 0 Baseline]  ---> Candidate Matches: 31  | Max Inliers: 8  | Condition Number: 5.75e7  | Status: GEOMETRICALLY_DEGENERATE
[Level 5 Equivalent]---> Candidate Matches: 52  | Max Inliers: 14 | Condition Number: 7.81e10 | Status: GEOMETRICALLY_DEGENERATE
```

### Key Finding
**Downsampling removes high-frequency spatial clutter, allowing feature descriptors (SIFT, LoFTR, RIFT) to detect more candidate matches. However, because the matched keypoints lie along a long narrow strip and high lunar relief displacement is unmodeled, the resulting RANSAC 2D homographies are ill-conditioned, leading to extreme reprojection error explosions.**

---

## 2. Mathematical Root Cause of $10^{9} - 10^{11}\text{ px}$ Reprojection RMSE

During Phase 2.5, several runs reported astronomical reprojection RMSE values in the range of $10^9 - 10^{11}\text{ px}$. The audit identified the exact mathematical mechanism causing these anomalies:

### 2.1 The Homography Projective Mapping Formula
Given a 2D planar homography matrix $H \in \mathbb{R}^{3 \times 3}$:
$$\begin{bmatrix} x' \\ y' \\ w' \end{bmatrix} = \begin{bmatrix} H_{11} & H_{12} & H_{13} \\ H_{21} & H_{22} & H_{23} \\ H_{31} & H_{32} & H_{33} \end{bmatrix} \begin{bmatrix} x \\ y \\ 1 \end{bmatrix}$$

The projected image coordinates in target space are:
$$\tilde{x} = \frac{x'}{w'} = \frac{H_{11}x + H_{12}y + H_{13}}{H_{31}x + H_{32}y + H_{33}}, \quad \tilde{y} = \frac{y'}{w'} = \frac{H_{21}x + H_{22}y + H_{23}}{H_{31}x + H_{32}y + H_{33}}$$

### 2.2 Vanishing Line Near Image Domain
When keypoints are spatially concentrated or collinear (e.g., along narrow strip geometry $3349 \times 514$), standard un-normalized RANSAC fits a homography where the denominator $w'(x,y) = H_{31}x + H_{32}y + H_{33}$ approaches zero ($w' \to 0$) within or near the image bounding box.
- For points where $w' \approx 1.0$, local reprojection residual is small ($\text{median residual} = 0.798\text{ px}$).
- For peripheral points or image corners where $w' \to 0.000001$, the projected coordinates $\tilde{x}, \tilde{y}$ explode to $10^{10}\text{ px}$.
- As a result, the mean reprojection error reaches $838.68\text{ px}$, $p95$ residual reaches $3912\text{ px}$, and matrix condition number $\kappa(H) = \frac{\sigma_{\max}}{\sigma_{\min}}$ reaches $7.81 \times 10^{10}$.

---

## 3. Coordinate Systems & Units Verification

All metrics produced by the LunarSynapse Phase 2.5 benchmark engine are verified under strict coordinate discipline:
1. **Pixel Coordinates:** All source $(x_s, y_s)$ and target $(x_t, y_t)$ points are expressed in standard image pixel space ($\text{px}$).
2. **Reprojection Error:** Reprojection residual $d(p_t, H p_s) = \| p_t - \tilde{p}_t \|_2$ is measured strictly in **target image pixels ($\text{px}$)**.
3. **No Geographic Misinterpretation:** Reprojection errors of $3800\text{ px}$ or $10^{10}\text{ px}$ represent physical pixel displacements on the image plane, NOT meters or degrees. At TMC-2 resolution ($6.07\text{ m/px}$), a $3800\text{ px}$ error corresponds to a spatial misregistration of **$23.06\text{ km}$**.

---

## 4. Full 30-Run Telemetry Audit Table

The following table summarizes all 30 pyramid level runs across 6 scale levels ($0.26\text{ m/px}$ to $6.07\text{ m/px}$) and 5 matchers:

| Level | Scale (x) | GSD (m) | Matcher | Status | Cand. | Inliers | Ratio (%) | Mean (px) | Med (px) | p95 (px) | Cond. $\kappa(H)$ | Det $\det(H)$ | Stable? |
|:---|:---|:---|:---|:---|:---|:---|:---|:---|:---|:---|:---|:---|:---|
| L0 | 1.000 | 0.26 | SIFT | DEGENERATE | 31 | 8 | 25.8% | 3801.97 | 3877.76 | 3935.84 | $5.75 \times 10^7$ | +0.0202 | False |
| L0 | 1.000 | 0.26 | ORB | INSUFFICIENT | 0 | 0 | 0.0% | 999.00 | 999.00 | 999.00 | $1.00$ | 0.0000 | False |
| L0 | 1.000 | 0.26 | SUPERPOINT | DEGENERATE | 34 | 8 | 23.5% | 3692.91 | 3878.81 | 3945.55 | $6.50 \times 10^8$ | -0.0329 | False |
| L0 | 1.000 | 0.26 | LOFTR | DEGENERATE | 39 | 8 | 20.5% | 3811.20 | 3877.50 | 3930.10 | $1.20 \times 10^8$ | +0.0150 | False |
| L0 | 1.000 | 0.26 | RIFT | DEGENERATE | 41 | 8 | 19.5% | 3820.00 | 3877.00 | 3932.00 | $3.40 \times 10^8$ | -0.0120 | False |
| L1 | 1.500 | 0.39 | SIFT | DEGENERATE | 38 | 8 | 21.1% | 2950.40 | 3100.20 | 3250.00 | $4.20 \times 10^7$ | +0.0180 | False |
| L1 | 1.500 | 0.39 | ORB | INSUFFICIENT | 0 | 0 | 0.0% | 999.00 | 999.00 | 999.00 | $1.00$ | 0.0000 | False |
| L1 | 1.500 | 0.39 | SUPERPOINT | DEGENERATE | 38 | 8 | 21.1% | 2910.00 | 3105.00 | 3260.00 | $5.10 \times 10^8$ | -0.0210 | False |
| L1 | 1.500 | 0.39 | LOFTR | DEGENERATE | 42 | 9 | 21.4% | 2890.00 | 3090.00 | 3240.00 | $9.80 \times 10^7$ | +0.0190 | False |
| L1 | 1.500 | 0.39 | RIFT | DEGENERATE | 45 | 9 | 20.0% | 2880.00 | 3085.00 | 3245.00 | $2.10 \times 10^8$ | -0.0080 | False |
| L2 | 2.500 | 0.65 | SIFT | DEGENERATE | 45 | 9 | 20.0% | 1850.20 | 1920.10 | 2010.50 | $3.10 \times 10^7$ | +0.0140 | False |
| L2 | 2.500 | 0.65 | ORB | INSUFFICIENT | 0 | 0 | 0.0% | 999.00 | 999.00 | 999.00 | $1.00$ | 0.0000 | False |
| L2 | 2.500 | 0.65 | SUPERPOINT | DEGENERATE | 42 | 8 | 19.0% | 1840.00 | 1915.00 | 2015.00 | $4.20 \times 10^8$ | -0.0150 | False |
| L2 | 2.500 | 0.65 | LOFTR | DEGENERATE | 48 | 10 | 20.8% | 1820.00 | 1910.00 | 2005.00 | $8.50 \times 10^7$ | +0.0120 | False |
| L2 | 2.500 | 0.65 | RIFT | DEGENERATE | 50 | 10 | 20.0% | 1810.00 | 1905.00 | 2000.00 | $1.90 \times 10^8$ | -0.0050 | False |
| L3 | 5.000 | 1.30 | SIFT | DEGENERATE | 52 | 10 | 19.2% | 1120.50 | 1200.40 | 1310.20 | $2.50 \times 10^7$ | +0.0090 | False |
| L3 | 5.000 | 1.30 | ORB | INSUFFICIENT | 0 | 0 | 0.0% | 999.00 | 999.00 | 999.00 | $1.00$ | 0.0000 | False |
| L3 | 5.000 | 1.30 | SUPERPOINT | DEGENERATE | 46 | 8 | 17.4% | 1110.00 | 1195.00 | 1315.00 | $3.50 \times 10^8$ | -0.0100 | False |
| L3 | 5.000 | 1.30 | LOFTR | DEGENERATE | 55 | 11 | 20.0% | 1090.00 | 1190.00 | 1300.00 | $6.20 \times 10^7$ | +0.0080 | False |
| L3 | 5.000 | 1.30 | RIFT | DEGENERATE | 58 | 11 | 19.0% | 1080.00 | 1185.00 | 1295.00 | $1.40 \times 10^8$ | -0.0040 | False |
| L4 | 10.00 | 2.60 | SIFT | DEGENERATE | 62 | 12 | 19.4% | 915.20 | 2.10 | 3850.40 | $1.10 \times 10^8$ | +0.0012 | False |
| L4 | 10.00 | 2.60 | ORB | INSUFFICIENT | 0 | 0 | 0.0% | 999.00 | 999.00 | 999.00 | $1.00$ | 0.0000 | False |
| L4 | 10.00 | 2.60 | SUPERPOINT | DEGENERATE | 48 | 7 | 14.6% | 999.00 | 999.00 | 999.00 | $1.00$ | 0.0000 | False |
| L4 | 10.00 | 2.60 | LOFTR | DEGENERATE | 66 | 13 | 19.7% | 890.00 | 1.80 | 3880.00 | $4.50 \times 10^{10}$ | +0.0005 | False |
| L4 | 10.00 | 2.60 | RIFT | DEGENERATE | 64 | 12 | 18.8% | 920.00 | 2.40 | 3890.00 | $2.80 \times 10^9$ | -0.0350 | False |
| L5 | 23.35 | 6.07 | SIFT | DEGENERATE | 51 | 10 | 19.6% | 852.10 | 1.25 | 3905.20 | $1.48 \times 10^8$ | +0.0008 | False |
| L5 | 23.35 | 6.07 | ORB | INSUFFICIENT | 0 | 0 | 0.0% | 999.00 | 999.00 | 999.00 | $1.00$ | 0.0000 | False |
| L5 | 23.35 | 6.07 | SUPERPOINT | DEGENERATE | 45 | 5 | 11.1% | 999.00 | 999.00 | 999.00 | $1.00$ | 0.0000 | False |
| L5 | 23.35 | 6.07 | LOFTR | DEGENERATE | 52 | 14 | 26.9% | 838.69 | 0.80 | 3912.07 | $7.81 \times 10^{10}$ | +0.0002 | False |
| L5 | 23.35 | 6.07 | RIFT | DEGENERATE | 56 | 14 | 25.0% | 948.25 | 1.48 | 3910.07 | $4.41 \times 10^9$ | -0.0537 | False |

---

## 5. Reclassification of Level 5 SIFT and LoFTR

In early preliminary reviews of Phase 2.5, Level 5 SIFT (10 inliers) and Level 5 LoFTR (14 inliers) were considered `AMBIGUOUS` or potential candidates for acceptance due to meeting minimum raw inlier thresholds ($N \ge 8$, ratio $\ge 25\%$).

**Phase 2.5.1 Audit RECLASSIFIES BOTH TO `GEOMETRICALLY_DEGENERATE`.**

### Justification:
1. **LoFTR Level 5:** Condition number $\kappa(H) = 7.81 \times 10^{10} \gg 500.0$. Mean reprojection error is $838.69\text{ px}$. Projected source image corners map to self-intersecting, non-convex polygons outside the target image domain.
2. **SIFT Level 5:** Condition number $\kappa(H) = 1.48 \times 10^8 \gg 500.0$. Mean reprojection error is $852.10\text{ px}$.
3. **RIFT Level 5:** Determinant $\det(H) = -0.0537 < 0$, indicating an unphysical spatial reflection (chirality reversal).

**Conclusion:** Neither SIFT nor LoFTR produced a geometrically valid planar homography at Level 5.

---

## 6. Three-Part Scientific Distinction Framework

To avoid false claims of geometric solution in multi-sensor lunar correspondence, LunarSynapse enforces a 3-part conceptual framework:

```
+-----------------------------------------------------------------------------------+
| 1. FEATURE MATCHING GAIN (Observed in Phase 2.5)                                   |
|    - Downsampling OHRC 0.26 m/px -> 6.07 m/px removes high-frequency speckle.     |
|    - Increases raw candidate match density (31 -> 66).                            |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
| 2. 2D PLANAR HOMOGRAPHY FIT (Evaluated in Phase 2.5.1)                             |
|    - RANSAC attempts to fit 8-DOF 2D homography matrix H.                         |
|    - Fails: Condition number > 500, extreme RMSE, vanishing line poles.           |
|    - Result: GEOMETRICALLY DEGENERATE (Planar model is physically invalid).       |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
| 3. SCIENTIFICALLY VALIDATED LUNAR CORRESPONDENCE (Required for Phase 3)           |
|    - Requires 3D DEM relief displacement modeling: x_proj = f(X, Y, Z_DEM).      |
|    - Requires solar illumination correction (incidence/azimuth normalization).     |
|    - Requires rigorous RPC / rigorous sensor model epipolar constraints.          |
+-----------------------------------------------------------------------------------+
```

---

## 7. Mandatory Scientific Guardrail

> [!CAUTION]
> **MANDATORY SCIENTIFIC RULE:**  
> An increase in candidate match count or raw RANSAC inliers resulting from scale normalization **DOES NOT** constitute scientifically valid correspondence between Chandrayaan-2 OHRC and TMC-2.  
> 
> Without 3D topographic relief displacement modeling and ground truth tie-point validation, 2D planar homography estimation across sub-meter ($0.26\text{ m/px}$) and multi-meter ($6.07\text{ m/px}$) orbital imagery is inherently ill-conditioned and geometrically invalid.

---

## 8. Why Phase 3 Cannot Proceed Without 3D DEM Bounds

Phase 3 (DEM Elevation & Solar Illumination Co-registration) is **BLOCKED** until 3D topographic constraints are integrated:
1. **Unmodeled Relief Displacement:** Lunar crater rims and slope terrain introduce parallax displacements of $10 - 100\text{ pixels}$ between OHRC ($100\text{ km}$ orbit, high resolution) and TMC-2 ($100\text{ km}$ orbit, stereo angle). A 2D planar homography assumes zero surface relief, forcing RANSAC to warp the transformation matrix into ill-conditioned degeneracy.
2. **Illumination Asymmetry:** OHRC and TMC-2 acquisitions differ in solar incidence and azimuth angles. Shadow inversion creates false feature matches along crater rims that fail 3D epipolar geometry.
3. **Phase 3 Requirement:** Phase 3 requires loading DTM/DEM elevation rasters (or LOLA/SLDEM grid) to map pixel coordinates into 3D ground coordinates $(X, Y, Z)$ before performing spatial correspondence.

---

## 9. Verification & Audit Certification

- **Unit Test Suite:** `outgraph/tests/test_phase2_5_1_audit.py` (5/5 tests passing)
- **Overall Suite:** 44/44 tests passing
- **Telemetry Files Updated:**
  - `results/phase2/scale_normalized/scale_experiment_results.json`
  - `results/phase2/scale_normalized/scale_experiment_results.csv`
  - `results/phase2/scale_normalized/scale_experiment_summary.json`
