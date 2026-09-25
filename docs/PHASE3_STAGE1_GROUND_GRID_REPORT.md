# Phase 3 Stage 1 — Ground-Grid Georeferencing Engine Report

**Project:** LunarSynapse — SIH26166  
**Module:** `outgraph.ml.geometry.ground_grid`  
**Status:** PHASE 3 STAGE 1 VERIFIED — GROUND-GRID ENGINE OPERATIONAL  
**Test Suite:** 53/53 tests passing (44 baseline + 9 Stage 1 tests)  

---

## 1. Actual CSV Structure Discovered

Inspection of the real mission geometry files confirmed:
* **OHRC Grid File:** `data/real/ohrc/ch2_ohr_ncp_20210402T0546284043_d_img_d18/geometry/calibrated/20210402/ch2_ohr_ncp_20210402T0546284043_g_grd_d18.csv`
* **TMC-2 Grid File:** `data/real/tmc2/ch2_tmc_nca_20240523T1600309581_d_img_d18/geometry/calibrated/20240523/ch2_tmc_nca_20240523T1600309581_g_grd_d18.csv`
* **CSV Columns:** `Longitude, Latitude, Pixel, Scan`
* **Lattice Completeness:** Both datasets form **100% complete rectangular Cartesian lattices** with zero missing cells, zero duplicates, and strictly monotonic coordinates along the scan lines.

```
+---------------------------------------------------------------------------------------------------+
| REAL DATA SAMPLING DISCOVERY                                                                      |
| - OHRC:  121 unique pixels (step 100, last 99) x 783 unique scans (step 100, last 74) = 94,743   |
| - TMC-2:  41 unique pixels (step 100, last 99) x 2147 unique scans (step 100, last 56) = 88,027 |
+---------------------------------------------------------------------------------------------------+
```

---

## 2. Interpolation Strategy Selected & Justification

### Forward Mapping: `(pixel, scan) → (longitude, latitude)`
* **Selected Method:** `scipy.interpolate.RegularGridInterpolator(..., method='linear')`
* **Justification:** Because `unique_pixels` and `unique_scans` are strictly ascending 1D coordinate vectors forming a complete Cartesian lattice, `RegularGridInterpolator` is mathematically optimal. It handles non-uniform steps at the final boundary (e.g., step of 99 or 74) natively without distortion, executes in $\mathcal{O}(1)$ time per query point, and achieves exact ($0.0\text{ error}$) reconstruction at all calibrated grid vertices.

### Inverse Mapping: `(longitude, latitude) → (pixel, scan)`
* **Selected Method:** `scipy.interpolate.LinearNDInterpolator(..., fill_value=np.nan)`
* **Justification:** On the spherical lunar surface with spacecraft roll and pitch, lines of constant scan or pixel project to slightly non-rectilinear curves in $(\lambda, \phi)$ space. `LinearNDInterpolator` constructs a 2D Delaunay triangulation directly on the calibrated $(\text{lon}, \text{lat})$ points. Points outside the calibrated convex hull footprint naturally evaluate to `np.nan`, preventing unphysical extrapolation.

---

## 3. Product Grid Statistics

| Metric | OHRC Ground Grid | TMC-2 Ground Grid |
| :--- | :--- | :--- |
| **Total Records** | **94,743** | **88,027** |
| **Lattice Regularity** | 100% Rectilinear (121 $\times$ 783) | 100% Rectilinear (41 $\times$ 2147) |
| **Pixel (Sample) Range** | $0$ to $11,999$ (12,000 px width) | $0$ to $3,999$ (4,000 px width) |
| **Scan (Line) Range** | $0$ to $78,174$ (78,175 lines) | $0$ to $214,556$ (214,557 lines) |
| **Longitude Bounds** | $[23.371989^\circ\text{ E}, 23.495434^\circ\text{ E}]$ | $[22.541304^\circ\text{ E}, 24.721199^\circ\text{ E}]$ |
| **Latitude Bounds** | $[0.224735^\circ\text{ N}, 1.068878^\circ\text{ N}]$ | $[-23.889283^\circ\text{ N}, 10.625027^\circ\text{ N}]$ |
| **Spatial Footprint** | $\approx 25.6\text{ km} \times 3.7\text{ km}$ | $\approx 1040\text{ km} \times 65\text{ km}$ |

---

## 4. Round-Trip Interpolation Accuracy

Evaluating $(p, s) \to (\lambda, \phi) \to (p', s')$ across 100 randomly sampled continuous interior coordinates:

```
[OHRC Round-Trip Error]
  - Pixel Error:  median = 2.21e-08 px | max = 2.25e-03 px  (0.0022 pixels)
  - Scan Error:   median = 5.30e-06 px | max = 2.51e-04 px  (0.00025 pixels)

[TMC-2 Round-Trip Error]
  - Pixel Error:  median = 1.25e-04 px | max = 1.61e-03 px  (0.0016 pixels)
  - Scan Error:   median = 7.99e-05 px | max = 1.06e-03 px  (0.0011 pixels)
```

On exact calibrated grid vertices, reconstruction error is **$0.000000\text{ pixels}$**.

---

## 5. Domain Boundary & Rejection Behavior

* **Inside Valid Domain:** Returns precise, continuous coordinate transformations.
* **Outside Domain (Default):** Returns `(np.nan, np.nan)`.
* **Outside Domain (`raise_out_of_bounds=True`):** Explicitly raises `GroundGridOutOfBoundsError`.
* **Domain Checks:** `contains_pixel(p, s)` and `contains_ground(lon, lat)` provide boolean validation before evaluation.

---

## 6. Performance & Memory Profile

* **File Size:** Operates strictly on the lightweight $\sim 3\text{ MB}$ CSV files, avoiding any loading of the $938\text{ MB}$ or $1.7\text{ GB}$ raw image rasters.
* **Initialization Time:**
  * OHRC: $0.25\text{ s}$ forward index, $1.4\text{ s}$ inverse Delaunay index.
  * TMC-2: $0.20\text{ s}$ forward index, $1.2\text{ s}$ inverse Delaunay index.
* **Query Speed:** $< 0.05\text{ ms}$ per query in vectorized NumPy format.
* **Caching:** Handled via internal `GroundGrid._CACHE`, ensuring zero re-parsing overhead across runs.

---

## 7. Mandatory Scientific Guardrail & Limitations

> [!CAUTION]
> **SCIENTIFIC INTEGRITY RULE:**  
> Ground-grid interpolation provides a calibrated pixel $\leftrightarrow$ selenographic ground coordinate mapping under the ISRO reference projection surface.  
> 
> **It does NOT by itself prove:**
> 1. Physical correspondence between features in OHRC and TMC-2
> 2. 3D terrain correctness or DEM relief alignment
> 3. True photogrammetric intersection
> 4. Feature-matcher correctness across sun-angle differences
> 
> Ground-grid georeferencing is a necessary structural constraint for Phase 3, not proof of solved registration.
