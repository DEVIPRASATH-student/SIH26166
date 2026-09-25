# Phase 2 — Real-Data Correspondence Baseline Report
**Project:** LunarSynapse — SIH26166 (Multi-modal, Sun angle and scale invariant image correspondence using Chandrayaan-2 optical images)  
**Date:** September 21, 2026  
**Status:** PHASE 2 REAL-DATA EXECUTION COMPLETE — REAL CHANDRAYAAN-2 DATA INGESTED & BENCHMARKED  

---

## 1. Objective

The objective of Phase 2 is to establish a scientifically defensible **real-data correspondence baseline** using LunarSynapse's product ingestion foundation and correspondence evaluation pipeline. The baseline evaluates real optical and spectral lunar datasets (Chandrayaan-2 OHRC and TMC-2), quantifies keypoint/geometric residuals under real scale gaps (0.26 m/px vs 6.07 m/px), and categorizes failure modes without relying on synthetic fallbacks or fabricated ground truth.

---

## 2. Real Dataset Inventory & Sensor Verification

| Sensor / Product ID | Mission | Instrument | Acquisition Timestamp | Native GSD (Verified from Label) | Image Dimensions & Datatype | Local Path | Verification Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **OHRC**<br>`ch2_ohr_ncp_20210402T0546284043_d_img_d18` | Chandrayaan-2 | Orbiter High Resolution Camera | 2021-04-02 05:46:28 UTC | **0.26 m/pixel** | 78,175 x 12,000 (1 band, uint8, 938.1 MB) | `data/real/ohrc/ch2_ohr_ncp_20210402T0546284043_d_img_d18/` | **VERIFIED** (PDS4 XML) |
| **TMC-2**<br>`ch2_tmc_nca_20240523T1600309581_d_img_d18` | Chandrayaan-2 | Terrain Mapping Camera (Nadir) | 2024-05-23 16:00:30 UTC | **6.07 m/pixel** | 214,557 x 4,000 (1 band, uint16 LSB, 1.716 GB) | `data/real/tmc2/ch2_tmc_nca_20240523T1600309581_d_img_d18/` | **VERIFIED** (PDS4 XML) |
| **TMC-2 (NCF)**<br>`ch2_tmc_ncf_20241214T1937388174_d_img_d18` | Chandrayaan-2 | Terrain Mapping Camera (Fore) | N/A | UNKNOWN | Corrupted archive | N/A | **EXCLUDED** (Integrity Failed) |

*Note: Per-product GSD, geometry, and illumination were strictly extracted from authoritative PDS4 XML labels. No nominal instrument specifications were used to replace missing fields.*

---

## 3. Product Provenance & Hashes

Append-only provenance tracking was executed for both real lunar observations:

### OHRC Product: `ch2_ohr_ncp_20210402T0546284043_d_img_d18`
- **Source:** ISRO / ISSDC Chandrayaan-2 Archive
- **XML Label:** `ch2_ohr_ncp_20210402T0546284043_d_img_d18.xml` (SHA256: `e527449f8a4517ec7d2cb41d3b41ecc307f1e18a0684ede15072a2ef7c631877`)
- **Image Binary:** `ch2_ohr_ncp_20210402T0546284043_d_img_d18.img` (MD5 from XML: `c4d89f11e9f6660c345349e453f6a0f4`, Size: 938,100,000 bytes)
- **Geometry CSV:** `ch2_ohr_ncp_20210402T0546284043_g_grd_d18.csv` (MD5 from XML: `3f84edf419eaeddbc7caba5bc8f958c5`, Records: 94,743)
- **Geometry XML:** `ch2_ohr_ncp_20210402T0546284043_g_grd_d18.xml` (Size: 6,206 bytes)

### TMC-2 Product: `ch2_tmc_nca_20240523T1600309581_d_img_d18`
- **Source:** ISRO / ISSDC Chandrayaan-2 Archive
- **XML Label:** `ch2_tmc_nca_20240523T1600309581_d_img_d18.xml` (SHA256: `bb163ef874942f764b349448be5ba7d60eb5ed5c9750b08d1e8aaacc0da1a123`)
- **Image Binary:** `ch2_tmc_nca_20240523T1600309581_d_img_d18.img` (MD5 from XML: `b9c5863b19b265acfa697c7d2c1425be`, Size: 1,716,456,000 bytes)
- **Geometry CSV:** `ch2_tmc_nca_20240523T1600309581_g_grd_d18.csv` (Records: 71,520, Size: 3,056,481 bytes)
- **Geometry XML:** `ch2_tmc_nca_20240523T1600309581_g_grd_d18.xml` (Size: 6,282 bytes)

---

## 4. Geographic Overlap Determination

Geographic bounds were parsed from refined corner coordinates in the respective PDS4 XML labels:

- **OHRC Geographic Footprint:**
  - Latitude Range: `[0.224735° N, 1.068878° N]`
  - Longitude Range: `[23.371989° E, 23.495434° E]`
- **TMC-2 Geographic Footprint:**
  - Latitude Range: `[-23.889283° N, 10.625027° N]`
  - Longitude Range: `[22.541304° E, 24.721199° E]`

### Polygon Intersection Evaluation:
- **Bounding Box Overlap:** `TRUE`
- **Exact Quad Polygon Intersection Area:** `65.03%` of the OHRC frame overlaps with the TMC-2 strip.
- **Overlap Status:** `OVERLAP_CONFIRMED`
- **Registered Real Pair:** `REAL_OHRC_TMC2_001_001` (Priority Tier 2, High Difficulty due to ~23.3x GSD scale difference).

---

## 5. Real-Data Baseline Benchmark Execution

The real correspondence benchmark was executed directly on the verified real pair `REAL_OHRC_TMC2_001_001` across 5 feature matching algorithms without synthetic fallback or fabricated ground truth.

### Real Benchmark Results Summary (`REAL_DATA = TRUE`)

| Pair ID | Matcher | Source | Target | Ground Truth Level | Status | Inliers | Candidate Matches | Inlier Ratio | Reprojection Error (Mean) | Coverage Ratio | Failure Category | Time (s) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `REAL_OHRC_TMC2_001_001` | **SIFT** | OHRC | TMC-2 | `LEVEL_UNKNOWN` | **AMBIGUOUS** | 8 | 31 | 25.81% | $1.46 \times 10^{10}\text{ px}$ | 12.82% | `GEOMETRIC_FAILURE` | 2.59s |
| `REAL_OHRC_TMC2_001_001` | **ORB** | OHRC | TMC-2 | `LEVEL_UNKNOWN` | **INSUFFICIENT_EVIDENCE** | 0 | 0 | 0.00% | 999.00 px | 0.00% | `FEATURE_SPARSITY_FAILURE` | 4.28s |
| `REAL_OHRC_TMC2_001_001` | **SUPERPOINT** | OHRC | TMC-2 | `LEVEL_UNKNOWN` | **AMBIGUOUS** | 8 | 34 | 23.53% | $2.47 \times 10^{10}\text{ px}$ | 9.78% | `GEOMETRIC_FAILURE` | 2.14s |
| `REAL_OHRC_TMC2_001_001` | **LOFTR** | OHRC | TMC-2 | `LEVEL_UNKNOWN` | **AMBIGUOUS** | 8 | 40 | 20.00% | 0.67 px | 7.43% | `GEOMETRIC_FAILURE` | 2.10s |
| `REAL_OHRC_TMC2_001_001` | **RIFT** | OHRC | TMC-2 | `LEVEL_UNKNOWN` | **AMBIGUOUS** | 9 | 56 | 16.07% | $2.64 \times 10^{9}\text{ px}$ | 24.26% | `GEOMETRIC_FAILURE` | 1.94s |

---

## 6. Failure Analysis & Findings

1. **Scale Gap Challenge (0.26 m/px vs 6.07 m/px):**
   - The ~23.3x ground sampling distance (GSD) ratio between OHRC and TMC-2 represents a severe scale gap. Standard 2D keypoint matchers (SIFT, ORB, SuperPoint) extract features at unscaled native image pixels, resulting in false matches across repetitive crater rims and lunar dust textures.
2. **ORB Sparsity Collapse:**
   - ORB extracted keypoints from the OHRC source view (2500 points) but 0 keypoints from the downsampled TMC-2 view (0 points), producing `INSUFFICIENT_EVIDENCE`.
3. **Geometric Residual Instability:**
   - While SIFT, SuperPoint, LoFTR, and RIFT extracted 31-56 candidate matches, RANSAC planar homography estimation yielded unstable condition numbers ($> 10^7$) and high mean reprojection residuals.
4. **Conclusion:**
   - Standard 2D classical and un-tuned deep matchers fail to achieve clean geometric registration on cross-resolution real Chandrayaan-2 OHRC vs TMC-2 imagery without explicit scale pyramid normalization or terrain elevation prior bounds.

---

## 7. Ground Truth Hierarchy Assessment

For the real OHRC vs TMC-2 pair:
- **Level 1 (Georeferenced Overlap):** `AVAILABLE` — Verified geographic footprint overlap (~65.03%).
- **Level 2 (Independent DEM / Reference):** `NOT AVAILABLE` — No high-resolution SLDEM/LRO DEM co-registered reference is present in the workspace.
- **Level 3 (Manually Verified Tie Points):** `NOT AVAILABLE` — No human-verified tie points exist for this specific pair.
- **Level 4 (Synthetic Transform):** `NOT APPLICABLE` — Real data benchmark explicitly isolated from synthetic controls.

**Assigned Real Pair GT Level:** `LEVEL_UNKNOWN` / `LEVEL_1_GEOREFERENCED` (Overlap verified, ground truth correspondence coordinates not yet established).

---

## 8. Scientific Claim Guardrails

- **Data Ingestion != Scientific Validation:** Ingestion and PDS4 label parsing were successful, but this does NOT constitute scientific validation of scale or illumination invariance.
- **RANSAC Fit != Correct Correspondence:** The 8-9 inliers found by SIFT/LoFTR exhibited unstable homography condition numbers, correctly flagged by the system as `AMBIGUOUS` / `GEOMETRIC_FAILURE`.
- **Claims Guardrail:** We explicitly DO NOT claim sun-angle invariance, scale invariance, or physics-aware superiority on real data at Phase 2.

---

## 9. Test Suite Verification

The full pytest test suite was executed:
```bash
python -m pytest outgraph/tests/ -v
```
**Results:** `33 PASSED`, 0 failed. All synthetic control demo functionality remains intact while real-data ingestion and benchmark pathways are fully verified.

---

## 10. Summary of Phase 2 Recovery

- **Phase 2 State:** Full implementation survived crash; real Chandrayaan-2 OHRC and TMC-2 products ingested, verified, and benchmarked.
- **Stop Condition:** Phase 2 complete. Execution halted before Phase 3 as directed.
errain.
