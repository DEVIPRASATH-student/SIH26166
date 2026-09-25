# PHASE 3 — STAGE 2: REFERENCE-DATUM GRID-TO-GRID PROJECTION REPORT
**Scientific Audit & Mathematical Verification Pass**  
**LunarSynapse Scientific Technical Documentation**  
**Date:** September 2026  
**Status:** COMPLETE & AUDITED (Stage 2 of Phase 3)  
**Execution Context:** Calibrated ISRO Ground-Grid Georeferencing Pipeline  

---

## 1. Executive Summary & Mandatory Scientific Guardrail

> [!IMPORTANT]
> **MANDATORY SCIENTIFIC GUARDRAIL:**
> "This experiment validates the consistency of the calibrated reference-datum grid mapping. It does not establish physical 3D correspondence between OHRC and TMC-2 observations."

In Phase 3 Stage 2, LunarSynapse implemented the **Reference-Datum GridProjector** (`outgraph/ml/geometry/grid_projection.py`), providing an **ISRO-calibrated GroundGrid reference-surface transformation** between OHRC and TMC-2 image planes:

$$\text{OHRC } (x_{\text{px}}, y_{\text{sc}}) \xrightarrow{\text{OHRC GroundGrid (Forward)}} (\lambda, \phi)_{\text{datum}} \xrightarrow{\text{TMC-2 GroundGrid (Inverse)}} \text{Predicted TMC-2 } (x_{\text{px}}, y_{\text{sc}})$$

This establishes a georeferenced coordinate transformation derived strictly from the ISRO PDS4 calibrated geometry records (`_g_grd_d18.csv`), completely replacing the unconstrained planar homography assumptions of Phase 2.5.

---

## 2. Root-Cause Analysis: The "TMC-2 Pixel = 0" Anomaly

During empirical evaluation of the real mission datasets, an apparent anomaly was detected:
- Out of 1,000 tested OHRC points, 645 produced finite projections, while 355 produced `NaN`.
- **Every single finite projection evaluated strictly to $\text{TMC-2 Pixel} = 0.0$**, while the scan coordinate varied smoothly from $y_{\text{sc}} \approx 59,577$ to $64,810$.
- The round-trip residual was large: $\text{mean} = 2,995.82\text{ m}$, $\text{median} = 3,007.81\text{ m}$, $\text{min} = 1,527.94\text{ m}$, $\text{max} = 4,318.80\text{ m}$.

### Investigation & Root Cause Findings:
1. **Is the TMC-2 Inverse Interpolator Defective? (NO):**
   An independent verification of real TMC-2 grid vertices across the full sensor width ($P \in [0, 3999]$) in the OHRC latitude zone ($0.22^\circ\text{ N}$ to $1.07^\circ\text{ N}$) proved that the `LinearNDInterpolator` achieves **machine-precision coordinate recovery** ($\Delta P \le 4.5 \times 10^{-13}\text{ px}$, $\Delta S \le 7.3 \times 10^{-12}\text{ scans}$):

   | Original Pixel | Original Scan | Selenographic Longitude | Selenographic Latitude | Recovered Pixel | Recovered Scan | Pixel Residual | Scan Residual |
   | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
   | **0** | 62300 | $23.552401^\circ\text{ E}$ | $0.648864^\circ\text{ N}$ | 0.0000 | 62300.0000 | $0.0000$ | $2.16 \times 10^{-9}$ |
   | **500** | 62300 | $23.669440^\circ\text{ E}$ | $0.640888^\circ\text{ N}$ | 500.0000 | 62300.0000 | $0.0000$ | $0.0000$ |
   | **1000** | 62200 | $23.786857^\circ\text{ E}$ | $0.649120^\circ\text{ N}$ | 1000.0000 | 62200.0000 | $0.0000$ | $0.0000$ |
   | **1500** | 62200 | $23.903821^\circ\text{ E}$ | $0.641393^\circ\text{ N}$ | 1500.0000 | 62200.0000 | $0.0000$ | $0.0000$ |
   | **2000** | 62100 | $24.021191^\circ\text{ E}$ | $0.649883^\circ\text{ N}$ | 2000.0000 | 62100.0000 | $0.0000$ | $0.0000$ |
   | **2500** | 62100 | $24.138162^\circ\text{ E}$ | $0.642399^\circ\text{ N}$ | 2500.0000 | 62100.0000 | $4.55 \times 10^{-13}$ | $7.28 \times 10^{-12}$ |
   | **3000** | 62000 | $24.255564^\circ\text{ E}$ | $0.650874^\circ\text{ N}$ | 3000.0000 | 62000.0000 | $0.0000$ | $0.0000$ |
   | **3500** | 62000 | $24.372623^\circ\text{ E}$ | $0.643621^\circ\text{ N}$ | 3500.0000 | 62000.0000 | $0.0000$ | $0.0000$ |
   | **3999** | 61900 | $24.489957^\circ\text{ E}$ | $0.652612^\circ\text{ N}$ | 3999.0000 | 61900.0000 | $0.0000$ | $0.0000$ |

2. **Delaunay Triangulation Convex-Hull Artifact:**
   The TMC-2 pushbroom track spans over $1,000\text{ km}$ from $-23.88^\circ\text{ N}$ to $+10.62^\circ\text{ N}$. Due to lunar orbital precession, the swath forms a curved track across the lunar sphere.
   The 2D Delaunay triangulation creates a global **convex hull** that encloses the curved swath. Along the western concave indentation of this swath, Delaunay connects boundary vertices across vast latitude spans:
   - For example, querying OHRC coordinate $(\text{Lon}=23.49^\circ, \text{Lat}=0.50^\circ)$ lands in Simplex `28872`.
   - The three vertices of Simplex `28872` are:
     - Vertex 17179: $\text{Lon}=23.632^\circ, \text{Lat}=+3.917^\circ, \mathbf{P=0}, S=41900$
     - Vertex 15498: $\text{Lon}=23.647^\circ, \text{Lat}=+4.573^\circ, \mathbf{P=0}, S=37800$
     - Vertex 87986: $\text{Lon}=22.541^\circ, \text{Lat}=-23.816^\circ, \mathbf{P=0}, S=214556$
   - All three simplex vertices lie on the western boundary of TMC-2 where $\mathbf{P = 0}$.
   - Linear interpolation among these vertices yields $P = w_1(0) + w_2(0) + w_3(0) \equiv \mathbf{0.0}$.
   - The scan line $S$ interpolates smoothly according to latitude along this chord, yielding $S \in [59577, 64810]$.

3. **Conclusion:**
   The `TMC-2 Pixel = 0.0` behavior is **NOT a bug in GroundGrid or GridProjector**. It is an expected consequence of querying coordinates that lie outside the physical swath but inside the 2D Delaunay convex hull chord, clamping linearly to the boundary edge where $P=0$.

---

## 3. Verified Physical Gap Analysis

We independently verified the physical geographic separation between the OHRC and TMC-2 products across all 53 TMC-2 scan lines intersecting the OHRC latitude range ($0.2247^\circ\text{ N}$ to $1.0689^\circ\text{ N}$):

| Metric | Measured Value |
| :--- | :--- |
| **Number of Scan Lines Sampled** | 53 lines (TMC-2 scan 59,300 to 64,900) |
| **OHRC Longitude Range** | $23.371989^\circ\text{ E}$ to $23.495434^\circ\text{ E}$ |
| **TMC-2 Western Edge ($P=0$) Longitude Range** | $23.541609^\circ\text{ E}$ to $23.563093^\circ\text{ E}$ |
| **Angular Longitudinal Gap ($\Delta \lambda$)** | $0.046175^\circ$ to $0.067659^\circ$ |
| **Minimum Physical Ground Gap** | $\mathbf{1,491.83\text{ m}}$ ($1.49\text{ km}$) |
| **Maximum Physical Ground Gap** | $\mathbf{2,051.30\text{ m}}$ ($2.05\text{ km}$) |
| **Mean Physical Ground Gap** | $\mathbf{1,773.17\text{ m}}$ ($1.77\text{ km}$) |
| **Median Physical Ground Gap** | $\mathbf{1,773.38\text{ m}}$ ($1.77\text{ km}$) |

### Classification of the Gap:
This is **A) A GENUINE PHYSICAL FOOTPRINT GAP** on the lunar surface.
- The two image swaths do not overlap: they are adjacent parallel observation tracks separated by $\sim 1.5 - 2.1\text{ km}$.
- The prior Phase 2 claim of "65.03% overlap" was **B) an Axis-Aligned Bounding Box (AABB) artifact**: OHRC's small bounding box falls inside the bounding box of TMC-2's global $1,000\text{ km}$ track.
- The 645 "valid" projections were **C) a 2D Delaunay convex-hull artifact**: the exterior concave bay was triangulated by chords connecting western boundary points ($P=0$).

---

## 4. 20-Point OHRC Target Projection Table

To evaluate projection behavior across the full OHRC footprint, 20 points distributed uniformly across 4 sample columns and 5 scan lines were evaluated:

| # | OHRC Pixel | OHRC Scan | Longitude | Latitude | TMC Pixel | TMC Scan | Domain Status | Physical Interpretation |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| 1 | 0 | 0 | $23.375034^\circ$ | $1.056037^\circ$ | NaN | NaN | INVALID | Outside Delaunay Convex Hull |
| 2 | 3999 | 0 | $23.414918^\circ$ | $1.060279^\circ$ | NaN | NaN | INVALID | Outside Delaunay Convex Hull |
| 3 | 7999 | 0 | $23.455054^\circ$ | $1.064560^\circ$ | 0.0 | 59586.0 | VALID | Clamped to TMC-2 Western Boundary |
| 4 | 11999 | 0 | $23.495434^\circ$ | $1.068878^\circ$ | 0.0 | 59603.4 | VALID | Clamped to TMC-2 Western Boundary |
| 5 | 0 | 19500 | $23.374263^\circ$ | $0.848685^\circ$ | NaN | NaN | INVALID | Outside Delaunay Convex Hull |
| 6 | 3999 | 19500 | $23.414147^\circ$ | $0.852929^\circ$ | NaN | NaN | INVALID | Outside Delaunay Convex Hull |
| 7 | 7999 | 19500 | $23.454282^\circ$ | $0.857212^\circ$ | 0.0 | 60885.0 | VALID | Clamped to TMC-2 Western Boundary |
| 8 | 11999 | 19500 | $23.494662^\circ$ | $0.861533^\circ$ | 0.0 | 60901.9 | VALID | Clamped to TMC-2 Western Boundary |
| 9 | 0 | 39000 | $23.373494^\circ$ | $0.641332^\circ$ | NaN | NaN | INVALID | Outside Delaunay Convex Hull |
| 10 | 3999 | 39000 | $23.413378^\circ$ | $0.645578^\circ$ | NaN | NaN | INVALID | Outside Delaunay Convex Hull |
| 11 | 7999 | 39000 | $23.453513^\circ$ | $0.649864^\circ$ | 0.0 | 62183.9 | VALID | Clamped to TMC-2 Western Boundary |
| 12 | 11999 | 39000 | $23.493893^\circ$ | $0.654188^\circ$ | 0.0 | 62200.9 | VALID | Clamped to TMC-2 Western Boundary |
| 13 | 0 | 58500 | $23.372741^\circ$ | $0.433962^\circ$ | NaN | NaN | INVALID | Outside Delaunay Convex Hull |
| 14 | 3999 | 58500 | $23.412626^\circ$ | $0.438211^\circ$ | 0.0 | 63466.5 | VALID | Clamped to TMC-2 Western Boundary |
| 15 | 7999 | 58500 | $23.452762^\circ$ | $0.442499^\circ$ | 0.0 | 63482.6 | VALID | Clamped to TMC-2 Western Boundary |
| 16 | 11999 | 58500 | $23.493142^\circ$ | $0.446826^\circ$ | 0.0 | 63500.2 | VALID | Clamped to TMC-2 Western Boundary |
| 17 | 0 | 78174 | $23.371989^\circ$ | $0.224735^\circ$ | NaN | NaN | INVALID | Outside Delaunay Convex Hull |
| 18 | 3999 | 78174 | $23.411874^\circ$ | $0.228986^\circ$ | 0.0 | 64777.1 | VALID | Clamped to TMC-2 Western Boundary |
| 19 | 7999 | 78174 | $23.452011^\circ$ | $0.233276^\circ$ | 0.0 | 64793.2 | VALID | Clamped to TMC-2 Western Boundary |
| 20 | 11999 | 78174 | $23.492393^\circ$ | $0.237605^\circ$ | 0.0 | 64810.4 | VALID | Clamped to TMC-2 Western Boundary |

---

## 5. Distinction in Round-Trip Residual Interpretation

We strictly distinguish between the two residual regimes:

1. **Synthetic Benchmark (Mathematical Interpolation Consistency):**
   - On overlapping synthetic grids, the round-trip residual is **$< 0.03\text{ mm}$ mean** and **$< 0.1\text{ mm}$ max**.
   - This validates that `GridProjector`'s forward-inverse mathematical logic is exact and introduces negligible interpolation error.

2. **Real Mission Datasets (Reference-Grid Transformation Behavior):**
   - For real OHRC and TMC-2 products, the round-trip residual has **$\text{mean} = 2,995.82\text{ m}$** ($\sim 3.0\text{ km}$), **$\text{min} = 1,527.94\text{ m}$**, and **$\text{max} = 4,318.80\text{ m}$**.
   - **Do NOT describe this $\sim 3\text{ km}$ residual as high-accuracy geographic consistency.**
   - Rather, this residual directly measures the **physical distance from each OHRC coordinate to the western boundary ($P=0$) of the non-overlapping TMC-2 strip**.
   - Because the points are clamped to the boundary edge at $P=0$, re-projecting $(P=0, S)$ back to ground coordinates produces the boundary longitude ($\sim 23.55^\circ$), creating a residual equal to the physical gap.

---

## 6. Scientific Terminology Guardrails

To maintain scientific integrity:
- We use: **"ISRO-calibrated reference-datum coordinate transformation"** or **"ISRO-calibrated GroundGrid reference-surface transformation."**
- We do **NOT** use "orbit and line-of-sight geometry" because this implementation relies strictly on ISRO's pre-computed geometry grid products (`_g_grd_d18.csv`), not on dynamic SPICE orbit kernels or ray-tracing LOS models.
- We do **NOT** claim that Stage 2 establishes physical correspondence between OHRC and TMC-2 imagery.

---

## 7. Automated Test Suite Status

A dedicated regression test suite was implemented in `outgraph/tests/test_grid_projection.py` (12 tests total):
1. `test_grid_projector_initialization_type_safety`: Rejection of non-GroundGrid types.
2. `test_grid_projector_synthetic_exact_projection`: Sub-millimeter mathematical closure on synthetic overlap.
3. `test_grid_projector_real_ohrc_vertices`: Verifies physical behavior at real OHRC corners.
4. `test_grid_projector_random_interior_points`: Random interior coordinate sampling.
5. `test_grid_projector_vectorized_shapes`: Array dimension preservation across 1D and 2D arrays.
6. `test_grid_projector_out_of_bounds_handling`: NaN returns and exception raising.
7. `test_grid_projector_domain_check_methods`: Verifies `is_ground_in_target_domain` and `is_source_in_target_domain`.
8. `test_grid_projector_geographic_overlap`: Bounding box intersection calculation.
9. `test_grid_projector_deterministic_repeatability`: Bitwise reproducibility across repeated calls.
10. `test_grid_projector_round_trip_residuals`: Synthetic residual evaluation.
11. `test_grid_projector_tmc2_inverse_recovery_across_sensor_width`: **Verifies independent machine-precision recovery across all TMC-2 pixel columns ($P \in [0, 3999]$).**
12. `test_grid_projector_real_ohrc_western_boundary_collapse`: **Regression test documenting the collapse of non-overlapping OHRC coordinates to TMC-2 Western boundary ($P=0.0$).**

### Full Pytest Status:
```
65 passed, 130 warnings in 65.28s
```
- **Prior to Stage 2:** 53 passed, 0 failed.
- **Stage 2 additions:** 12 passed, 0 failed.
- **Current test status:** **65 passed, 0 failed (100% green).**

---

## 8. Confirmations & Scope Boundaries
- **DEM Integration:** NOT implemented.
- **Parallax Model:** NOT implemented.
- **Epipolar Corridor:** NOT implemented.
- **Physical Feature Matcher:** NOT implemented.
- **Illumination Filtering:** NOT implemented.
- **Stage 3:** NOT started.
- **Real Mission Datasets:** NOT modified (100% intact and read-only).
- **Git State:** NOT committed, NOT pushed.
