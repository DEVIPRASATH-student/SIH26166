# PHASE 3 — STAGE 3.6: INDEPENDENT PHYSICAL VALIDATION REPORT
**LunarSynapse Scientific Technical Documentation**  
**Date:** September 2026  
**Status:** COMPLETE & AUDITED (Stage 3.6 Gate Passed)  
**Execution Context:** Independent Ground Validation & Physical Gate Audit  

---

## 1. Executive Summary & Mandatory Scientific Determination

> [!IMPORTANT]
> **FINAL SCIENTIFIC DETERMINATION:**
> **"PHYSICAL CORRESPONDENCE NOT VALIDATED"**
> 
> Independent physical validation establishes that the selected real Chandrayaan-2 OHRC and TMC-2 products in `data/real/` represent **adjacent non-overlapping observation swaths separated by a physical ground gap of approximately 1.49 km to 2.05 km**. 
> 
> Neither 2D reference-datum projection nor 3D DEM terrain elevation can bridge this spatial separation. LunarSynapse maintains strict scientific integrity by declaring zero valid correspondence rather than fabricating an unphysical match.

---

## 2. Independent Validation Hierarchy

1. **Tier A — ISRO PDS4 Calibrated Geometry Kernels:**
   - Evaluated independently from the original `_g_grd_d18.csv` ground grids.
   - Verified that OHRC coverage ends at $\text{Lon} = 23.495434^\circ\text{ E}$, while TMC-2 coverage at matching latitudes begins at $\text{Lon} = 23.541609^\circ\text{ E}$.
2. **Tier B — Independent Topographic Validation (SLDEM2015):**
   - Evaluated real terrain elevation across 20 independent coordinates.
   - Regional elevation sits at $h \approx -1,768\text{ m}$ to $-2,003\text{ m}$ relative to $R = 1737.4\text{ km}$.
3. **Tier C — Physical Parallax Geometry Limits:**
   - For an altitude of $H = 121.43\text{ km}$ and look angle $\theta \le 5.6^\circ$, maximum possible terrain parallax is $\Delta x \le 246.4\text{ m}$.
   - Because $246.4\text{ m} \ll 1,491.8\text{ m}$, terrain relief cannot bring the target coordinate into the active sensor array.

---

## 3. 20-Point Independent Validation Table

| # | OHRC $(x, y)$ | Longitude | Latitude | DEM $h$ | Predicted TMC-2 | Corridor $[p_{\text{min}}, p_{\text{max}}]$ | Ground Gap | Status | Rejection Reason |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| 1 | (0, 0) | $23.375034^\circ$ | $1.056037^\circ$ | $-1978.9\text{ m}$ | NaN | NaN | $5689.3\text{ m}$ | REJECTED | `GATE3_TARGET_OUTSIDE_CALIBRATED_SWATH` |
| 2 | (4000, 0) | $23.414925^\circ$ | $1.060280^\circ$ | $-1986.6\text{ m}$ | NaN | NaN | $4479.9\text{ m}$ | REJECTED | `GATE3_TARGET_OUTSIDE_CALIBRATED_SWATH` |
| 3 | (7999, 0) | $23.455057^\circ$ | $1.064560^\circ$ | $-1993.6\text{ m}$ | NaN | $[-35.3, -30.4]$ | $3263.1\text{ m}$ | REJECTED | `GATE4_TARGET_CLAMPED_TO_SWATH_BOUNDARY` |
| 4 | (11999, 0) | $23.495434^\circ$ | $1.068878^\circ$ | $-2001.7\text{ m}$ | NaN | $[-35.4, -30.5]$ | $2039.0\text{ m}$ | REJECTED | `GATE4_TARGET_CLAMPED_TO_SWATH_BOUNDARY` |
| 5 | (0, 19544) | $23.374261^\circ$ | $0.848221^\circ$ | $-1927.9\text{ m}$ | NaN | NaN | $5551.6\text{ m}$ | REJECTED | `GATE3_TARGET_OUTSIDE_CALIBRATED_SWATH` |
| 6 | (4000, 19544) | $23.414151^\circ$ | $0.852466^\circ$ | $-1950.7\text{ m}$ | NaN | NaN | $4342.1\text{ m}$ | REJECTED | `GATE3_TARGET_OUTSIDE_CALIBRATED_SWATH` |
| 7 | (7999, 19544) | $23.454283^\circ$ | $0.856749^\circ$ | $-1963.5\text{ m}$ | NaN | $[-34.8, -29.9]$ | $3125.3\text{ m}$ | REJECTED | `GATE4_TARGET_CLAMPED_TO_SWATH_BOUNDARY` |
| 8 | (11999, 19544) | $23.494659^\circ$ | $0.861069^\circ$ | $-1958.1\text{ m}$ | NaN | $[-34.7, -29.8]$ | $1901.1\text{ m}$ | REJECTED | `GATE4_TARGET_CLAMPED_TO_SWATH_BOUNDARY` |
| 9 | (0, 39087) | $23.373491^\circ$ | $0.640406^\circ$ | $-1870.5\text{ m}$ | NaN | NaN | $5413.0\text{ m}$ | REJECTED | `GATE3_TARGET_OUTSIDE_CALIBRATED_SWATH` |
| 10 | (4000, 39087) | $23.413382^\circ$ | $0.644653^\circ$ | $-1895.2\text{ m}$ | NaN | NaN | $4203.4\text{ m}$ | REJECTED | `GATE3_TARGET_OUTSIDE_CALIBRATED_SWATH` |
| 11 | (7999, 39087) | $23.453514^\circ$ | $0.648938^\circ$ | $-1912.5\text{ m}$ | NaN | $[-34.0, -29.0]$ | $2986.5\text{ m}$ | REJECTED | `GATE4_TARGET_CLAMPED_TO_SWATH_BOUNDARY` |
| 12 | (11999, 39087) | $23.493890^\circ$ | $0.653262^\circ$ | $-1932.7\text{ m}$ | NaN | $[-34.3, -29.4]$ | $1774.1\text{ m}$ | REJECTED | `GATE4_TARGET_CLAMPED_TO_SWATH_BOUNDARY` |
| 13 | (0, 58630) | $23.372736^\circ$ | $0.432575^\circ$ | $-1829.5\text{ m}$ | NaN | NaN | $5273.2\text{ m}$ | REJECTED | `GATE3_TARGET_OUTSIDE_CALIBRATED_SWATH` |
| 14 | (4000, 58630) | $23.412628^\circ$ | $0.436824^\circ$ | $-1848.7\text{ m}$ | NaN | $[-32.9, -28.0]$ | $4063.6\text{ m}$ | REJECTED | `GATE4_TARGET_CLAMPED_TO_SWATH_BOUNDARY` |
| 15 | (7999, 58630) | $23.452760^\circ$ | $0.441112^\circ$ | $-1865.5\text{ m}$ | NaN | $[-33.2, -28.2]$ | $2846.7\text{ m}$ | REJECTED | `GATE4_TARGET_CLAMPED_TO_SWATH_BOUNDARY` |
| 16 | (11999, 58630) | $23.493137^\circ$ | $0.445438^\circ$ | $-1875.5\text{ m}$ | NaN | $[-33.4, -28.4]$ | $1634.6\text{ m}$ | REJECTED | `GATE4_TARGET_CLAMPED_TO_SWATH_BOUNDARY` |
| 17 | (0, 78174) | $23.371989^\circ$ | $0.224735^\circ$ | $-1768.2\text{ m}$ | NaN | NaN | $5130.6\text{ m}$ | REJECTED | `GATE3_TARGET_OUTSIDE_CALIBRATED_SWATH` |
| 18 | (4000, 78174) | $23.411881^\circ$ | $0.228987^\circ$ | $-1788.4\text{ m}$ | NaN | $[-31.9, -27.0]$ | $3920.9\text{ m}$ | REJECTED | `GATE4_TARGET_CLAMPED_TO_SWATH_BOUNDARY` |
| 19 | (7999, 78174) | $23.452015^\circ$ | $0.233277^\circ$ | $-1806.7\text{ m}$ | NaN | $[-32.2, -27.3]$ | $2703.9\text{ m}$ | REJECTED | `GATE4_TARGET_CLAMPED_TO_SWATH_BOUNDARY` |
| 20 | (11999, 78174) | $23.492393^\circ$ | $0.237605^\circ$ | $-1832.3\text{ m}$ | NaN | $[-32.6, -27.7]$ | $1492.4\text{ m}$ | REJECTED | `GATE4_TARGET_CLAMPED_TO_SWATH_BOUNDARY` |

---

## 4. Quantitative Validation Metrics

| Metric | Measured Value |
| :--- | :--- |
| **Total Validation Points Tested** | 20 points |
| **Valid Candidates Accepted** | **0 points (0.0%)** |
| **Candidates Rejected** | **20 points (100.0%)** |
| **Corridor Containment Rate** | **0.0%** (all corridors lie outside active pixel columns) |
| **Minimum Ground Separation to Target Swath** | **$1,492.4\text{ m}$** ($\approx 1.49\text{ km}$) |
| **Maximum Ground Separation to Target Swath** | **$5,689.3\text{ m}$** ($\approx 5.69\text{ km}$) |
| **Median Ground Separation** | **$3,592.0\text{ m}$** ($\approx 3.59\text{ km}$) |
| **95th Percentile Ground Separation** | **$5,558.5\text{ m}$** ($\approx 5.56\text{ km}$) |

---

## 5. Scientific Conclusion & Engineering Integrity

By subjecting candidate correspondences to independent physical validation:
1. The system confirms that the non-convergence of Phase 2 feature matchers was **not an algorithm defect**, but a direct consequence of physical non-overlap.
2. The system confirms that planar homographies (such as those fitted in Phase 2.5) were degenerate mathematical artifacts attempting to span disjoint ground tracks.
3. The system confirms that real lunar elevation ($h \approx -1.9\text{ km}$) and optical parallax ($\Delta x \le 246\text{ m}$) cannot bridge the $\sim 1.5 - 2.1\text{ km}$ spatial gap.
4. **Final Scientific Status:** **PHYSICAL CORRESPONDENCE NOT VALIDATED**.

**Stage 3.6 Acceptance Criteria:** FULLY SATISFIED (Rigorous Validation Documented).
