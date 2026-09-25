# PHASE 5 STAGE 5.1 REPORT: REAL MULTI-OBSERVATION VALIDATION & COMPATIBILITY MATRIX
**Project:** LunarSynapse (SIH 26166)  
**Date:** September 2026  
**Status:** COMPLETE & VERIFIED  
**Stage:** 5.1 — Multi-Observation Inventory & Geometric Compatibility Engine

---

## 1. Objective

Stage 5.1 inventories available real lunar mission observations and establishes a formal observation compatibility engine. The engine evaluates spatial footprint overlap using calibrated geometry rather than bounding-box heuristics, preventing false claims of cross-sensor correspondence.

---

## 2. Multi-Observation Inventory

### Real Datasets Cataloged:
1. **Chandrayaan-2 OHRC:**
   - Product ID: `ch2_ohr_ncp_20210402T0546284043_d_img_d18`
   - Acquisition Time: `2021-04-02T05:46:28.4043`
   - GSD: $0.25\text{ m/pixel}$
   - Footprint: Lat $[0.2247^\circ, 1.0689^\circ\text{ N}]$, Lon $[23.3720^\circ, 23.4954^\circ\text{ E}]$
   - Geometry: Calibrated GroundGrid `_g_grd_d18.csv` present.
2. **Chandrayaan-2 TMC-2:**
   - Product ID: `ch2_tmc_nca_20240523T1600309581_d_img_d18`
   - Acquisition Time: `2024-05-23T16:00:30.9581`
   - GSD: $5.0\text{ m/pixel}$
   - Footprint: Lat $[0.3541^\circ, 1.2580^\circ\text{ N}]$, Lon $[23.4412^\circ, 24.1500^\circ\text{ E}]$
   - Geometry: Calibrated GroundGrid `_g_grd_d18.csv` present.
3. **SLDEM2015 DEM:**
   - Product ID: `SLDEM2015_512_00N_30N_000_045`
   - Spatial Resolution: $512\text{ px/deg}$ ($\approx 59.2\text{ m/px}$)
   - Footprint: Lat $[0.0^\circ, 1.5^\circ\text{ N}]$, Lon $[23.0^\circ, 24.0^\circ\text{ E}]$
   - Geometry: Fully overlapping both OHRC and TMC-2 regions.

---

## 3. Observation Compatibility Matrix

Using [`ObservationCompatibilityMatrix`](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/outgraph/ml/world_model/observation_matrix.py#L53-L177), pairwise spatial overlap was evaluated across all mission sensors:

| Sensor | OHRC | TMC-2 | IIRS | LROC NAC | SELENE TC |
|---|:---:|:---:|:---:|:---:|:---:|
| **OHRC** | — | `NO_OVERLAP` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` |
| **TMC-2** | `NO_OVERLAP` | — | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` |
| **IIRS** | `UNKNOWN` | `UNKNOWN` | — | `UNKNOWN` | `UNKNOWN` |
| **LROC NAC** | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | — | `UNKNOWN` |
| **SELENE TC**| `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | — |

### Key Scientific Findings:
- **OHRC $\leftrightarrow$ TMC-2:** Evaluated as **`NO_OVERLAP`**. The calibrated footprints in `data/real/` are physically separated by $1,491.8 - 2,051.3\text{ m}$ (mean $1,773.2\text{ m}$), which exceeds the maximum theoretical terrain-induced parallax displacement ($246.4\text{ m}$).
- **IIRS, LROC NAC, SELENE TC:** Evaluated as **`UNKNOWN`** because raw observation files are absent from `data/real/`. Missing data is never classified as `NO_OVERLAP` or false.

---

## 4. Verification & Test Results

The test suite in [`outgraph/tests/test_phase5_observation_matrix.py`](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/outgraph/tests/test_phase5_observation_matrix.py) validated:
1. `test_observation_registration`: Confirms metadata and geometric properties tracking.
2. `test_real_ohrc_tmc2_disjoint_footprint_rejection`: Asserts `NO_OVERLAP` due to the calibrated $1.77\text{ km}$ footprint gap.
3. `test_missing_calibrated_geometry_status`: Returns `INSUFFICIENT_GEOMETRY` when calibration grids are missing.
4. `test_controlled_synthetic_overlap`: Validates `VALIDATED_OVERLAP` for controlled intersecting bounding regions.
5. `test_sensor_compatibility_matrix_generation`: Confirms correct generation of the 5x5 matrix with `NO_OVERLAP` and `UNKNOWN` entries.

**Test Result:** 5 passed, 0 failed. Total test count: $131 + 5 = 136$.
