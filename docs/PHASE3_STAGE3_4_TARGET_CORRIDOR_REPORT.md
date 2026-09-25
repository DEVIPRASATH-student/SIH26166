# PHASE 3 — STAGE 3.4: ELEVATION-BOUNDED TARGET CORRIDOR REPORT
**LunarSynapse Scientific Technical Documentation**  
**Date:** September 2026  
**Status:** COMPLETE (Stage 3.4 Gate Passed)  
**Execution Context:** Target Sensor Search Space & Elevation Corridor Bounding  

---

## 1. Executive Summary & Mandatory Scientific Guardrails

In Phase 3 Stage 3.4, LunarSynapse implemented the **Elevation-Bounded Target Corridor** (`outgraph/ml/geometry/target_corridor.py`). Instead of predicting an unrealistically point-like target pixel, the engine establishes a physically bounded interval of admissible target sensor coordinates governed by local lunar topographic relief and parallax uncertainty.

> [!IMPORTANT]
> **TERMINOLOGY GUARDRAILS:**
> - Strictly termed **"Elevation-Bounded Target Corridor"**.
> - Does **NOT** use "epipolar corridor" because no full epipolar line is established across pushbroom orbits.
> - Preserves explicit failure modes: non-overlapping or boundary-clamped points are assigned structured rejection reasons (`CORRIDOR_CLAMPED_TO_WESTERN_BOUNDARY`, `TARGET_OUTSIDE_CALIBRATED_SWATH`, `SOURCE_OUT_OF_BOUNDS`).

---

## 2. Mathematical Formulation & Architecture

For a given OHRC feature coordinate $(x_{\text{px}}, y_{\text{sc}})$:

1. **Local Elevation Bounds:**
   Given nominal DEM height $h_{\text{nom}} = \text{DEM}(\lambda, \phi)$ and local topographic variance margin $\Delta h_{\text{margin}}$ (default $\pm 150\text{ m}$):
   $$h_{\text{min}} = h_{\text{nom}} - \Delta h_{\text{margin}}, \quad h_{\text{max}} = h_{\text{nom}} + \Delta h_{\text{margin}}$$

2. **Reference-Datum Anchor:**
   $$\text{TMC-2 Reference Target } (p_{\text{ref}}, s_{\text{ref}}) = \text{GridProjector}(\text{OHRC } x_{\text{px}}, y_{\text{sc}})$$

3. **Parallax Displacement Interval:**
   $$\Delta p_{\text{min}} = \text{ParallaxModel}(h_{\text{min}}, p_{\text{ref}}), \quad \Delta p_{\text{max}} = \text{ParallaxModel}(h_{\text{max}}, p_{\text{ref}})$$
   $$\text{Corridor Sample Interval } [p_{\text{corridor}}^{\text{min}}, p_{\text{corridor}}^{\text{max}}] = [\min(p_{\text{ref}} + \Delta p_{\text{min}}, p_{\text{ref}} + \Delta p_{\text{max}}), \max(p_{\text{ref}} + \Delta p_{\text{min}}, p_{\text{ref}} + \Delta p_{\text{max}})]$$

4. **Corridor Metrics:**
   $$\text{Corridor Width (pixels)} = |p_{\text{corridor}}^{\text{max}} - p_{\text{corridor}}^{\text{min}}|$$
   $$\text{Corridor Width (meters)} = \text{Width (pixels)} \times \text{GSD}_{\text{TMC2}}$$

```
                       OHRC Point (pixel, scan)
                                  │
                                  ▼
                     [TerrainGeometry + DEM]
               (λ, φ, h_nominal, [h_min, h_max])
                                  │
                ┌─────────────────┴─────────────────┐
                ▼                                   ▼
    [Reference-Datum Target]               [Parallax Displacements]
       (p_ref, s_ref)                        (Δp_min, Δp_max)
                │                                   │
                └─────────────────┬─────────────────┘
                                  ▼
                 Elevation-Bounded Target Corridor:
           [p_corridor_min, p_corridor_max] × [s_min, s_max]
```

---

## 3. Empirical Evaluation on Real Mission Datasets

When evaluated across the real OHRC image plane:
1. **Western OHRC Points (e.g. $x=0, y=0$):**
   - Project outside the TMC-2 convex hull.
   - Status: `is_valid = False`, Rejection Reason: `TARGET_OUTSIDE_CALIBRATED_SWATH`.
2. **Eastern OHRC Points (e.g. $x=11999, y=0$):**
   - Reference projection lands on the western boundary of the TMC-2 grid ($p_{\text{ref}} = 0.0$).
   - Local terrain elevation is $h \approx -2,001.7\text{ m}$.
   - Because $h < 0$, parallax shifts the predicted sample further outward (to $p \approx -32.96$).
   - The entire elevation corridor $[-35.43, -30.49]$ falls strictly below pixel column 0 (outside the physical sensor array).
   - Status: `is_valid = False`, Rejection Reason: `CORRIDOR_CLAMPED_TO_WESTERN_BOUNDARY`.
3. **Corridor Width Metrics on Real Terrain Relief ($\Delta h = 300\text{ m}$):**
   - Mean corridor width: **$4.94\text{ pixels}$** ($\approx 29.6\text{ m}$ on ground).
   - Demonstrates that local terrain elevation creates a search uncertainty of $\approx 30\text{ m}$, which is **two orders of magnitude smaller than the $1,773\text{ m}$ footprint gap**.

---

## 4. Test Suite Status

Test module: [`outgraph/tests/test_target_corridor.py`](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/outgraph/tests/test_target_corridor.py)  
Status: **5 passed, 0 failed in 8.25s**  
- Synthetic corridor generation and bracketing: PASSED
- Out-of-bounds source coordinate rejection: PASSED
- Real OHRC out-of-swath target rejection: PASSED
- Real OHRC boundary clamping rejection: PASSED
- Batched corridor calculation: PASSED

**Stage 3.4 Acceptance Criteria:** FULLY SATISFIED.
