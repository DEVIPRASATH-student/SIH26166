# PHASE 3 — STAGE 3.2: DEM-AWARE TERRAIN GEOMETRY REPORT
**LunarSynapse Scientific Technical Documentation**  
**Date:** September 2026  
**Status:** COMPLETE (Stage 3.2 Gate Passed)  
**Execution Context:** Integrated Calibrated Ground-Grid & DEM Terrain Geometry Pipeline  

---

## 1. Executive Summary & Mandatory Scientific Guardrails

In Phase 3 Stage 3.2, LunarSynapse implemented the **TerrainGeometry** abstraction (`outgraph/ml/geometry/terrain_geometry.py`). It unifies the 2D ISRO GroundGrid georeferencing framework with physical lunar topography derived from SLDEM2015.

> [!IMPORTANT]
> **SCIENTIFIC DISTINCTION & PHYSICAL GUARDRAILS:**
> 1. **Reference Datum Surface:** Evaluated at $h = 0.0\text{ m}$ relative to the lunar reference sphere ($R_{\text{Moon}} = 1737.4\text{ km}$). This strictly preserves Stage 2 reference-datum coordinate transformations.
> 2. **Physical Terrain Surface:** Evaluated at $h = \text{DEM}(\lambda, \phi)$, yielding the physical 3D ground location $(\lambda, \phi, h)$.
> 3. **Underlying Invariance:** The calibrated ISRO GroundGrid files remain completely unmodified and immutable.
> 4. **Physical Claim Guardrail:** Introducing terrain elevation does **NOT** establish 3D physical correspondence between image observations.

---

## 2. Mathematical Formulation & Architecture

The architecture maps sensor space $(x_{\text{px}}, y_{\text{sc}})$ into selenographic space $(\lambda, \phi, h)$ through a sequential, non-destructive pipeline:

$$\text{Pixel } (x_{\text{px}}, y_{\text{sc}}) \xrightarrow[\text{Forward Interpolator}]{\text{GroundGrid}} (\lambda, \phi)_{\text{datum}} \xrightarrow[\text{Bilinear Interpolation}]{\text{SLDEM2015}} h_{\text{terrain}}$$

```
                 Image Coordinates: (pixel, scan)
                                │
                                ▼
                   [ISRO GroundGrid: Forward]
            (RegularGridInterpolator / Bilinear)
                                │
                                ▼
        Selenographic Coordinates: (longitude λ, latitude φ)
                                │
                 ┌──────────────┴──────────────┐
                 ▼                             ▼
       Reference Datum (h = 0)        Physical Terrain Surface
         (Stage 2 Baseline)             [SLDEM2015 Bilinear]
                 │                             │
                 ▼                             ▼
         (λ, φ, h = 0.0 m)             (λ, φ, h = -1890.3 m)
```

---

## 3. Verification & Numerical Validation

1. **Reference Datum Equivalence ($h = 0$):**
   When `use_dem=False` is requested, `pixel_to_terrain()` yields coordinates that are bitwise-identical to Stage 2 GroundGrid outputs:
   - Input: $x = 6000.0, y = 39000.0$
   - Output: $\lambda = 23.433417^\circ\text{ E}$, $\phi = 0.646791^\circ\text{ N}$, $h = 0.0\text{ m}$.
2. **Terrain Elevation Integration:**
   When `use_dem=True` is requested, real topography is retrieved at sub-millisecond speeds:
   - Output: $\lambda = 23.433417^\circ\text{ E}$, $\phi = 0.646791^\circ\text{ N}$, $h = -1897.5\text{ m}$.
3. **No-Data / Boundary Propagation:**
   Coordinates falling outside the calibrated footprint (e.g. $x = -10.0, y = 500.0$) produce `(np.nan, np.nan, np.nan)`, preventing erroneous terrain extrapolation.
4. **Vectorized Dimensionality:**
   Supports scalars, lists, 1D arrays, and 2D meshgrids with preserved tensor shapes.

---

## 4. Test Suite Status

Test module: [`outgraph/tests/test_terrain_geometry.py`](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/outgraph/tests/test_terrain_geometry.py)  
Status: **7 passed, 0 failed in 1.59s**  
- Type safety validation: PASSED
- Reference-datum equivalence ($h=0$): PASSED
- Real DEM elevation insertion: PASSED
- Deterministic repeatability: PASSED
- Vectorized array dimension preservation: PASSED
- Out-of-bounds propagation (NaN): PASSED
- Linear transect profiling: PASSED

**Stage 3.2 Acceptance Criteria:** FULLY SATISFIED.
