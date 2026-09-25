# Phase 7 Final Scientific Benchmark Report
**System:** LunarSynapse — Physics-Aware, Self-Evolving Multi-Modal Lunar World Model  
**Project:** SIH26166 — Multi-modal, Sun-angle and Scale Invariant Image Correspondence using Chandrayaan-2 OHRC, TMC-2, and IIRS  
**Benchmark Phase:** Phase 7.12 (Final Scientific Benchmark Certification)  
**Execution Timestamp:** 2026-09-24T14:45:00+05:30  
**Final Scientific Status:** `SCIENTIFIC_BENCHMARK_VALIDATED`

---

## 1. Executive Summary

Phase 7.12 concludes the exhaustive empirical benchmark campaign of LunarSynapse across twelve sequential stages (Phases 7.0 through 7.12). The objective of Phase 7 was **NOT** to declare algorithmic superiority, manufacture universal robustness claims, or force correspondence between uncalibrated observations. Rather, Phase 7 establishes an independently reproducible, auditable, and scientifically defensible characterization of:
1. Multi-modal feature correspondence behavior across extreme scale ($1\times$ to $23.35\times$) and illumination shifts;
2. Physical ray-tracing and GroundGrid geometric validation against authoritative SLDEM2015 topography;
3. Robustness response curves and empirical collapse boundaries across 8 controlled difficulty axes;
4. Physics-aware uncertainty quantification, epistemic divergence detection, and interval propagation;
5. Self-evolving Lunar World Model entity resolution, knowledge-gap taxonomy, and active observation loops.

Across the entire evaluation campaign:
- **Real Lunar Datasets Evaluated:** Chandrayaan-2 OHRC, Chandrayaan-2 TMC-2, LOLA/Kaguya SLDEM2015.
- **Real-Data Supervised Accuracy:** Categorized strictly as `NOT_APPLICABLE (NO TIE-POINT GROUND TRUTH)`.
- **Primary Scientific Invariant:** **`PHYSICAL CORRESPONDENCE NOT VALIDATED`** is strictly maintained for the real OHRC/TMC-2 pair due to a verified $1.49\text{ km} - 2.04\text{ km}$ physical footprint separation.
- **Physical Negative-Control Rejection Rate:** $100.0\%$ (all visual candidates rejected at physical validation Gates 3 and 4).
- **Full Repository Test Suite:** **299 passed**, 0 failed, 680 warnings across 81.97s.
- **Raw Data Immutability:** Exactly **0 bytes modified** in `data/real/`.

---

## 2. Scientific Scope

The scope of this benchmark encompasses three distinct and non-overlapping validation layers:
- **Layer 1: Software & Regression Verification:** 299 deterministic tests verifying system integrity, schema fidelity, error handling, and guardrails.
- **Layer 2: Controlled Synthetic Scientific Validation:** Quantitative characterization of precision, recall, F1, inlier ratios, and parallax displacement under known homographies and digital elevation models.
- **Layer 3: Real Lunar Scientific Validation:** Verification of sensor geometry, coordinate projection, DEM epipolar ray-tracing, and negative-control rejection on real Chandrayaan-2 products.

**Core Rule:** A success in Layer 1 or Layer 2 does **NOT** constitute proof of physical correspondence in Layer 3.

---

## 3. Dataset Inventory

| Product Identifier | Sensor / Source | Native Resolution | Dimensions | Selenographic Bounding Box | GroundGrid Verification | Local Availability |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `ch2_ohr_ncp_20210402T0546284043_d_img_d18` | Chandrayaan-2 OHRC | $0.26\text{ m/px}$ | $78,175 \times 12,000$ | Lat: $[0.2247^\circ, 1.0689^\circ]$, Lon: $[23.3720^\circ, 23.4954^\circ]$ | $121 \times 783$ grid verified | **AVAILABLE_LOCAL** |
| `ch2_tmc_nca_20240523T1600309581_d_img_d18` | Chandrayaan-2 TMC-2 | $6.07\text{ m/px}$ | $214,557 \times 4,000$ | Lat: $[-23.8893^\circ, 10.6250^\circ]$, Lon: $[22.5413^\circ, 24.7212^\circ]$ | $41 \times 2,147$ grid verified | **AVAILABLE_LOCAL** |
| `SLDEM2015_512_00N_30N_000_045.JP2` | LOLA / Kaguya Merged DEM | $512\text{ ppd}$ ($\sim 59\text{ m}$) | $15,360 \times 23,040$ | Lat: $[0.0^\circ, 30.0^\circ]$, Lon: $[0.0^\circ, 45.0^\circ]$ | Authoritative elevation | **AVAILABLE_LOCAL** |
| Chandrayaan-2 IIRS | Hyperspectral spectrometer | $20.0\text{ m/px}$ | N/A | N/A | Missing in local archive | **UNAVAILABLE** |
| LRO LROC NAC | Narrow Angle Camera | $0.50\text{ m/px}$ | N/A | N/A | Missing in local archive | **UNAVAILABLE** |
| Kaguya SELENE TC | Terrain Camera | $10.0\text{ m/px}$ | N/A | N/A | Missing in local archive | **UNAVAILABLE** |

---

## 4. Ground-Truth Hierarchy

All evaluations are classified against the four-level epistemic ground-truth hierarchy:
- **Level 1: Verified Georeferenced Overlap:** Established spatial overlap from calibrated spacecraft pointing and ephemerides.
- **Level 2: Independent DEM Topographic Reference:** Elevation and slope verified against LOLA/SLDEM2015.
- **Level 3: Manually Verified Tie-Point Ground Truth:** Human-expert or laser-altimetry co-registered surface fiducials.
- **Level 4: Controlled Synthetic Ground Truth:** Known synthetic homography, scale decimation, affine warp, or procedural noise.

**Current Real Data Status:** The available OHRC/TMC-2 pair lacks Level 3 tie points and fails Level 1 physical overlap. Consequently, real correspondence accuracy cannot be computed without scientific fabrication.

---

## 5. Benchmark Infrastructure

The benchmark infrastructure comprises five automated engines:
1. `RobustnessSweepEngine` ([`outgraph/ml/benchmark/robustness_sweep.py`](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/outgraph/ml/benchmark/robustness_sweep.py)): Executes multi-axis difficulty sweeps.
2. `AblationStudyEngine` ([`outgraph/ml/benchmark/ablation_study.py`](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/outgraph/ml/benchmark/ablation_study.py)): Evaluates 13 component removals.
3. `UncertaintyEngine` ([`outgraph/ml/uncertainty/uncertainty_engine.py`](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/outgraph/ml/uncertainty/uncertainty_engine.py)): Quantifies composite divergence and epistemic risk.
4. `KnowledgeGapBenchmark` ([`outgraph/ml/world_model/gap_benchmark.py`](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/outgraph/ml/world_model/gap_benchmark.py)): Evaluates 8 epistemic gap scenarios.
5. `ActiveWorldModelLoop` ([`outgraph/ml/world_model/active_loop.py`](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/outgraph/ml/world_model/active_loop.py)): Evaluates autonomous recommendation and gap closure.

---

## 6. Controlled Synthetic Benchmark

Evaluated across procedural lunar terrain tiles with known ground truth homographies:
- **SIFT:** High candidate density ($>50$ matches), stable under rotation ($F_1 > 0.96$).
- **ORB:** Fast execution ($4\text{ ms}$), stable under planar rotation ($F_1 > 0.93$), vulnerable to scale changes $>2.0\times$.
- **Geometric Verifier:** Consistently filters outliers, achieving precision $= 1.00$ when true inliers exist.

---

## 7. Multi-GSD / Scale Benchmark

Swept from $1.0\times$ to $23.35\times$ (the true OHRC-to-TMC-2 GSD ratio):
- For $s \in [1.0\times, 2.0\times]$: Descriptors maintain stability ($F_1 \in [0.63, 0.88]$).
- At $s = 4.0\times$: Decimation attenuates crater rim gradients ($F_1$ drops to $0.10$).
- At $s \ge 8.0\times$ and $23.35\times$: Raw 2D descriptor matching collapses completely (**0 candidates, 0 inliers**).
- **Finding:** Raw feature matching across multi-sensor lunar datasets without multi-scale pyramid normalization or regional geodetic bounding is mathematically invalid.

---

## 8. Illumination Benchmark

Swept solar incidence from $15.0^\circ$ to $90.0^\circ$ (grazing):
- Raw feature matchers detect keypoints on moving shadow boundaries across opposing azimuths ($\Delta \text{azimuth} = 180^\circ$), leading naive change detectors to infer false surface change.
- LunarSynapse's illumination validation engine models expected shadow shifts, achieving a **0.0% false-change rate** (`ACCEPTED_ILLUMINATION_CONSISTENT`).

---

## 9. Geometric Distortion Benchmark

- **Planar Rotation ($0^\circ$ to $180^\circ$):** Inlier ratios remained above $88\%$ for both SIFT and ORB.
- **Anisotropic Scaling:** Aspect ratio distortion $>2.5\times$ induced full homography degeneracy.
- **Reflection:** Affine transforms with $\det(H) < 0$ were explicitly rejected by the orientation chirality verifier.

---

## 10. Terrain / DEM Benchmark

- Evaluated against the physical sensor model of the Chandrayaan-2 TMC-2 off-nadir fore-camera ($\theta_{\text{look}} \approx 5.08^\circ$).
- Confirmed exact linear parallax growth: $\Delta x = h \tan(\theta_{\text{look}})$.
- At $h = 1,000\text{ m}$ relief, horizontal parallax displacement reaches **$88.96\text{ m}$** ($>14\text{ TMC-2 pixels}$, $>340\text{ OHRC pixels}$).
- **Finding:** Planar 2D homographies fail in rugged terrain; 3D ray-traced epipolar search corridors are mandatory.

---

## 11. Real Lunar Benchmark

Evaluated against the real Chandrayaan-2 OHRC and TMC-2 products:
- Image-only matchers found putative visual matches (SIFT: 31, SuperPoint: 34, LoFTR: 40, RIFT: 56).
- Calibrated GroundGrid analysis proved the footprints are separated by **$1,492.4\text{ m}$ to $2,039.0\text{ m}$**.
- Physical validation pipeline rejected **100.0% of candidate matches** (Gate 3: $47.1\%$, Gate 4: $52.9\%$).
- Result: **`PHYSICAL CORRESPONDENCE NOT VALIDATED`** successfully defended.

---

## 12. Baseline Comparison

- Evaluated SIFT, ORB, Scale-Normalized SIFT, and LunarSynapse across controlled conditions.
- Trade-offs documented: ORB offers lowest latency ($4\text{ ms}$); Scale-Normalized SIFT recovers matches up to $4\times$; LunarSynapse provides physical negative-control rejection.
- **No overall winner or ranking assigned.**

---

## 13. Ablation Study

Evaluated 13 architectural component ablations:
- Removing scale normalization ($A_1$) causes complete matching failure at $23.35\times$.
- Removing geometric verification ($A_2$) incurs $100\%$ false-positive acceptance on random noise.
- Removing DEM parallax modeling ($A_4$) causes physical rejection in regions with $>100\text{ m}$ relief.
- Removing non-transitivity guardrails ($A_8$) corrupts world graph topology.

---

## 14. Robustness Curves

Documented 10 empirical response curves across 103 data points:
- Scale vs. F1, Scale vs. Inlier Ratio, Illumination vs. False Change, Noise vs. F1, Blur vs. F1, Relief vs. Parallax Displacement, Overlap vs. Inliers ($0\%$ overlap strictly yields $0$ inliers), and Texture Density vs. Inliers.

---

## 15. Uncertainty & Calibration

- Epistemic conflict detection verified: conflicting sensor evidence triggers `HIGH_EPISTEMIC_RISK` ($U > 0.60$).
- Known error tracking verified: geometric instability tracks reprojection residual monotonically across $[0.1, 4.0\text{ px}]$.
- **Limitation:** Above $4.0\text{ px}$, instability saturates; real-lunar probabilistic calibration remains unestablished.

---

## 16. World Model

- Persistent entity resolution verified across multiple sensors and epochs.
- Entity aliasing resistance verified ($455\text{ m}$ crater separation strictly preserved).
- Epistemic guardrail enforced: $\text{Obs}_A \to \text{Entity}_X \leftarrow \text{Obs}_B \not\implies \text{Obs}_A \leftrightarrow \text{Obs}_B$.

---

## 17. Knowledge Gaps

All 8 supported scientific gap categories verified with $100\%$ detection rate:
1. `MISSING_MODALITY`
2. `MISSING_TEMPORAL_OBSERVATION`
3. `MISSING_GEOMETRIC_VALIDATION`
4. `MISSING_TERRAIN_VALIDATION`
5. `MISSING_SPECTRAL_VALIDATION`
6. `INSUFFICIENT_CORRESPONDENCE`
7. `FOOTPRINT_NON_OVERLAP`
8. `UNCERTAINTY_TOO_HIGH`

---

## 18. Active Observation Loop

- Autonomous feedback loop evaluated: Initial Observation $\to$ Gap $\to$ Recommendation $\to$ Follow-up $\to$ Confirmation.
- Recommendation language strictly bound to `POTENTIALLY_REDUCES_UNCERTAINTY`.
- Monotonic gap resolution confirmed with zero duplicate recommendations or oscillation.

---

## 19. Reproducibility

- Deterministic random seeds ($42$) used throughout all synthetic suites.
- Complete machine-readable results saved in `results/phase7_*.json`.
- Full repository test execution command: `pytest outgraph/tests/ -q`.

---

## 20. Test Results

- **Total Repository Tests:** **299 passed**, 0 failed, 0 skipped.
- **Execution Time:** 81.97s.
- **Warnings:** 680 (Pydantic V2 `dict` / `ConfigDict` deprecations and Python 3.13 `datetime.utcnow()` deprecations). Zero fatal runtime warnings.

---

## 21. Raw Data Integrity

- Verified checksums, file sizes, and binary headers for all files in `data/real/`.
- **RAW DATA MODIFIED = 0**.

---

## 22. Production Code Changes

| Production File | Modification | Scientific Rationale | Behavioral Impact |
| :--- | :--- | :--- | :--- |
| `outgraph/ml/world_model/knowledge_gap.py` | Added detection rules for `MISSING_GEOMETRIC_VALIDATION` and `MISSING_MODALITY` | Guarantees complete coverage for unvalidated candidates and missing auxiliary spectral channels | Enables explicit gap tracking for initial candidate features |

---

## 23. Scientific Claim Ledger

| Proposed Scientific Claim | Certified Classification | Evidence Basis |
| :--- | :--- | :--- |
| Under tested synthetic conditions, scale normalization extends feature recovery up to $4\times$. | **DEMONSTRATED** | Controlled scale sweep (Phase 7.9) |
| The evaluated real OHRC/TMC-2 pair is physically disjoint ($1.49 - 2.04\text{ km}$ separation). | **DEMONSTRATED** | GroundGrid geodetic projection (Phase 7.6) |
| Real OHRC/TMC-2 visual candidate correspondences are 100% rejected by physical gates. | **DEMONSTRATED** | 6-stage physical verification pipeline (Phase 7.6) |
| World model associations do not induce false inter-observation image correspondences. | **DEMONSTRATED** | Non-transitivity guardrail tests (Phase 7.11) |
| Observed optical parallax displacement scales linearly at $88.96\text{ m} / 1,000\text{ m}$ relief for TMC-2. | **DEMONSTRATED** | Ray-tracing parallax model (Phase 7.9) |
| LunarSynapse achieves universal scale and illumination invariance. | **NOT_VALIDATED** | Prohibited by scientific safety rules; falsified beyond $4\times$ scale |
| Real-lunar correspondence accuracy is 100%. | **NOT_VALIDATED** | Tie-point ground truth is unavailable; supervised accuracy is N/A |
| Active-loop observation recommendations guarantee uncertainty elimination. | **NOT_VALIDATED** | Recommendations only `POTENTIALLY_REDUCES_UNCERTAINTY` |

---

## 24. Negative Results

1. **Catastrophic Scale Collapse:** Standard feature descriptors (SIFT, ORB) suffer total collapse ($0$ inliers) at the true $23.35\times$ scale step without regional bounding.
2. **2D Homography Failure under Relief:** Planar homography fails to account for $>44\text{ m}$ parallax displacement on crater rims.
3. **Real Observation Non-Overlap:** The primary available real dataset pair does not intersect on the lunar surface.
4. **Saturation of Geometric Instability:** Reprojection error metrics saturate above $4.0\text{ px}$.

---

## 25. Final Limitations Register

1. No independently validated real OHRC/TMC-2 tie-point ground truth exists; real-data accuracy is strictly N/A.
2. Real physical correspondence remains not validated due to physical footprint separation.
3. Auxiliary sensor modalities (IIRS, LROC NAC, SELENE TC) remain unavailable locally.
4. Synthetic benchmarks demonstrate controlled robustness but cannot substitute for real-lunar verification.
5. Real-lunar empirical uncertainty calibration remains unestablished.
6. Geometric uncertainty saturation occurs above $4.0\text{ px}$.
7. Active-loop belief confirmation was demonstrated using synthetic follow-up observations.
8. Full spacecraft orbital mechanics, attitude control jitter, and mission scheduling windows were not simulated.

---

## 26. What Has Been Demonstrated

- Rigorous negative-control rejection of physically disjoint observations.
- Robust characterization of 8 empirical failure envelopes.
- Decoupling of world model surface knowledge from direct image matching.
- Elimination of false physical change claims caused by solar illumination shifts.
- Complete, non-destructive preservation of all raw lunar observations.

---

## 27. What Has NOT Been Demonstrated

- Sub-pixel real-lunar image correspondence between OHRC and TMC-2.
- Universal scale or illumination invariance under unconstrained conditions.
- Real-world spacecraft operational tasking.
- Formal probabilistic calibration on real lunar observations.

---

## 28. Final Scientific Status

```
SCIENTIFIC_BENCHMARK_VALIDATED
```
*(All 12 sub-stages completed, 299 repository regression tests passing, 0 raw data modified, all scientific claims verified and strictly bounded).*
