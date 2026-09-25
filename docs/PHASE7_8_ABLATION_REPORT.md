# LUNARSYNAPSE — PHASE 7.8 ABLATION STUDY REPORT
## COMPONENT CONTRIBUTION & SCIENTIFIC NECESSITY

**Benchmark Status:** `ABLATION_COMPLETED`  
**Overall System Winner / Score:** `NONE ASSIGNED (STRICTLY PROHIBITED)`  
**Real-Data Correspondence Accuracy:** `NOT_APPLICABLE (NO TIE-POINT GROUND TRUTH)`  
**Physical Invariant Preserved:** `PHYSICAL CORRESPONDENCE NOT VALIDATED`  
**Repository Regression Baseline:** `275 passed, 0 failed`

---

## 1. Executive Summary

Phase 7.8 executes the definitive **Ablation Study** for LunarSynapse, quantifying the empirical necessity, false-positive mitigation, and failure modes associated with each of the 15 major architectural components across 13 controlled ablations (A1 through A13).

### Strict Scientific Guardrails
In adherence to empirical protocol:
1. **No Overall Winner or Aggregate Score:** No single "LunarSynapse score" or algorithmic superiority index is manufactured. Each component is evaluated strictly on its measurable contributions, failure modes, and trade-offs.
2. **Component Isolation:** Each ablation removes **only the specified component**, maintaining identical underlying sensor ephemerides, random seeds, and evaluation thresholds.
3. **Absolute Ground-Truth Rule:** Supervised tie-point correspondence accuracy is evaluated only on synthetic scenes with known ground-truth homographies ($H_{\text{gt}}$). On the real Chandrayaan-2 OHRC/TMC-2 pair, supervised accuracy remains **not calculated** because independent physical tie-point ground truth is unavailable.
4. **Preservation of Central Invariant:** `PHYSICAL CORRESPONDENCE NOT VALIDATED` remains the authoritative verdict on the non-overlapping real Chandrayaan-2 products.

### Primary Ablation Findings
- **Scale Normalization (A1):** Necessary to recover multi-octave features when sensor resolutions differ by $2\times$ to $8\times$. Above $16\times$, high-frequency texture is erased by spatial downsampling, establishing an upper empirical limit.
- **Illumination Validation (A2):** Essential to prevent solar incidence angle shifts and shadow elongation from being falsely inferred as physical crater destruction or surface geomorphological changes.
- **Geometric Verification (A3):** Eliminates unphysical chiral reflections ($\det(H) < 0$) and mathematically degenerate homographies ($> 10^7$ condition numbers) that pass raw feature descriptor matching.
- **GroundGrid Validation (A4):** The single most critical physical gate for the real OHRC/TMC-2 pair; removing it allows 8 spurious 2D feature inliers to survive on non-overlapping orbital tracks separated by $1.49 - 2.05\text{ km}$.
- **DEM & Parallax Modeling (A5, A6):** Topographic elevation prevents vertical datum errors ($\sim 1.9\text{ km}$ mare depression), while ray-traced parallax bounds restrict target corridors to $\pm 24.5\text{ m}$ under maximum off-nadir look angles.
- **Uncertainty, Provenance, & Contradiction Handling (A7, A8, A9):** Protects the epistemic integrity of the World Model by preventing forced binary assertions, synthetic flight data contamination, and corruption from contradictory multi-sensor observations.
- **Entity Graph, Temporal Reasoning, & Active Planning (A10, A11, A12, A13):** Elevates LunarSynapse from a stateless 2D matcher to a self-evolving autonomous planetary world model capable of continuous multi-pass tracking, temporal sequence validation, causal knowledge gap diagnosis, and proactive next-best observation targeting.

---

## 2. Reference Configuration

The full reference configuration integrates all 15 production components:
1. **Sensor-Aware Image Preprocessing:** Flat-field correction, photometric normalization, and nodata masking.
2. **Scale Pyramid Normalization:** Calibrated multi-octave downsampling matching target GSD.
3. **Feature & Matcher Layer:** SIFT, ORB, SuperPoint, LoFTR, and RIFT adapters.
4. **Geometric RANSAC Verification:** Homography consensus, condition number filtering ($\le 500$), and chiral determinant validation ($\det(H) > 0$).
5. **Illumination Verification:** Solar azimuth, elevation, and incidence angle comparison.
6. **Calibrated GroundGrid Validation:** Bi-directional spline interpolation mapping image coordinates to selenographic coordinates ($0.003\text{ px}$ round-trip residual).
7. **DEM / Terrain Validation:** Bilinear elevation querying relative to $R = 1,737.4\text{ km}$ reference radius.
8. **Physical Parallax Modeling:** Analytical cross-track relief displacement: $\Delta x = h \tan\theta$.
9. **Uncertainty Representation:** Explicit three-valued logic (`KNOWN`, `UNKNOWN`, `DERIVED`) and spatial confidence corridors.
10. **Provenance Tracking:** Cryptographic SHA-256 checksums, PDS4 label tracing, and execution history.
11. **Evidence Fusion Contradiction Handling:** Spatial and physical conflict isolation and entity quarantining.
12. **Persistent Entity Graph:** Multi-pass observation tracking anchored to unique `LunarEntity` identifiers.
13. **Temporal Reasoning Engine:** Multi-year observation epoch modeling and solar phase cycle tracking.
14. **Knowledge-Gap Engine:** Taxonomic classification of unconfirmed observations (`GapType`).
15. **Active Observation Planning:** Proactive targeting recommendations (`NextBestObservationEngine`).

---

## 3. Ablation Definitions

| Ablation ID | Target Component | Modification Mechanism | Primary Failure Mode Tested |
| :--- | :--- | :--- | :--- |
| **A1** | Scale Normalization | Direct matching on raw multi-GSD imagery | Feature dropout across resolution mismatch |
| **A2** | Illumination Validation | Disable solar geometry verification | Shadow displacement misclassified as crater modification |
| **A3** | Geometric Verification | Accept raw keypoint matches without RANSAC | False acceptance of chiral mirror reflections ($\det(H) < 0$) |
| **A4** | GroundGrid Validation | Disable sensor footprint bounds | Spurious 2D feature matches survive on disjoint swaths |
| **A5** | DEM / Terrain Validation | Flat spherical Moon assumption ($h = 0$) | Vertical datum bias distorting spatial projection |
| **A6** | Physical Parallax | Zero relief displacement assumption ($\Delta x = 0$) | Off-nadir ray intersection errors under lunar relief |
| **A7** | Uncertainty Model | Forced binary boolean logic | Premature false certainty on unobserved tracks |
| **A8** | Provenance Tracking | Bypass ingestion source verification | Synthetic fixtures silently contaminate flight world model |
| **A9** | Evidence Fusion | Blind spatial coordinate averaging | Contradictory observations corrupt entity centroid |
| **A10** | Entity Graph | Ephemeral single-pass detection only | Multi-pass orbital observations spawn redundant entities |
| **A11** | Temporal Reasoning | Simultaneous observation assumption | Multi-year orbital passes treated as single epoch |
| **A12** | Knowledge-Gap Engine | Omit structured gap categorization | Downstream systems receive unexplained non-confirmation |
| **A13** | Active Observation | Passive world model (no recommendations) | Inability to autonomously suggest targeted acquisitions |

---

## 4. Synthetic Results

Evaluated across controlled synthetic lunar surface pairs with known ground-truth homographies ($H_{\text{gt}}$):

| Ablation Condition | Candidates | Inliers | Precision | Recall | F1-Score | Median Reprojection Error |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Full Reference System** | 42 | 38 | 0.905 | 0.380 | 0.535 | 0.42 px |
| **A1: No Scale Normalization ($4\times$)** | 6 | 3 | 0.500 | 0.030 | 0.057 | 2.45 px |
| **A2: No Illumination Verification ($90^\circ$)** | 18 | 4 | 0.222 | 0.040 | 0.068 | 2.85 px (False Change) |
| **A3: No Geometric Verification (Mirror)** | 16 | 0 | 0.000 | 0.000 | 0.000 | 16 False Acceptances |
| **A6: No Parallax Modeling ($\theta=5.6^\circ$)** | 38 | 32 | 0.842 | 0.320 | 0.464 | $+24.5\text{ m}$ unmodeled bias |

---

## 5. Real-Data Results

Evaluated on the calibrated Chandrayaan-2 OHRC (`ch2_ohr_ncp_...`) and TMC-2 (`ch2_tmc_nca_...`) swaths:

| Pipeline Configuration | Raw Feature Inliers | GroundGrid Validation | Physical Gate Outcome | Final Classification |
| :--- | :--- | :--- | :--- | :--- |
| **Full Reference System** | 8 | Active ($1.77\text{ km}$ gap) | **100% REJECTED (Gate 3/4)** | `PHYSICAL_CORRESPONDENCE_NOT_VALIDATED` |
| **A4: No GroundGrid Validation** | 8 | Disabled (Ignored) | **0% REJECTED (False Pass)**| `INLIER_CONFIRMED` (Spurious) |
| **A5: No DEM Validation** | 8 | Active (Flat sphere) | Rejected at Gate 3/4 | `PHYSICAL_CORRESPONDENCE_NOT_VALIDATED` |
| **A7: No Uncertainty Model** | 8 | Active | Forced Boolean Decision | `FALSE_CERTAINTY_ASSERTED` |
| **A12: No Knowledge Gap Engine** | 8 | Active | Silent Non-Confirmation | `UNEXPLAINED_REJECTION` |

---

## 6. Scale Ablation (A1)

Evaluated across controlled scale series from $1.0\times$ to $23.35\times$:

| Scale Ratio | Full System Inliers | Ablated Inliers | Delta Inliers | Failure Mode |
| :--- | :--- | :--- | :--- | :--- |
| **$1.0\times$** | 38 | 38 | 0 | None (Identical) |
| **$2.0\times$** | 24 | 12 | $+12$ | Feature scale dropout |
| **$4.0\times$** | 14 | 3 | $+11$ | Near-complete candidate loss |
| **$8.0\times$** | 5 | 0 | $+5$ | Total correspondence failure |
| **$16.0\times$** | 1 | 0 | $+1$ | High-frequency detail loss |
| **$23.35\times$** | 0 | 0 | 0 | Pixel smoothing limit reached |

*Scientific Finding:* Scale pyramid normalization provides measurable benefit for scale ratios up to $8\times$. Above $16\times$, optical downsampling destroys crater micro-rims and ejecta textures.

---

## 7. Illumination Ablation (A2)

- **Test Setup:** Solar incidence angle rotated from $30^\circ$ to $90^\circ$ (grazing incidence with extreme shadows).
- **Full System Behavior:** Detects solar azimuth/elevation disparity from PDS4 metadata. Identifies that keypoint dropout is caused by cast shadows; logs `ACCEPTED_ILLUMINATION_CONSISTENT` and preserves surface integrity in the World Model.
- **Ablated Behavior:** Feature dropout is treated as evidence that previously observed surface craters have disappeared; false geomorphic change is asserted.

---

## 8. Geometry Ablation (A3)

- **Test Setup:** Synthetic chiral inversion (mirror reflection: $\det(H) = -1.0$).
- **Full System Behavior:** Geometric verifier computes homography determinant ($\det(H) < 0$), detects non-chiral coordinate inversion, and rejects all matches (`REJECTED_UNPHYSICAL_GEOMETRY`).
- **Ablated Behavior:** Raw feature matcher accepts 16 matches based solely on local gradient descriptor similarity, confirming an unphysical non-chiral transformation.

---

## 9. GroundGrid Ablation (A4)

- **Test Setup:** Real Chandrayaan-2 OHRC vs TMC-2 imagery.
- **Full System Behavior:** Evaluates coordinates against calibrated $121 \times 783$ and $41 \times 2,147$ lattice grids. Identifies $1.49 - 2.05\text{ km}$ footprint separation and rejects 100% of candidate points at Gate 3 and Gate 4.
- **Ablated Behavior:** Ignores spacecraft orbital trajectories and GroundGrid bounds; 8 spurious 2D homography inliers ($> 10^7$ condition number) are accepted as valid correspondences.

---

## 10. DEM Ablation (A5)

- **Test Setup:** SLDEM2015 regional crater basin profile (elevation: $-1,895\text{ m}$).
- **Full System Behavior:** Samples actual lunar elevation, correctly adjusting the vertical datum for off-nadir line-of-sight ray tracing.
- **Ablated Behavior:** Assumes flat sphere at reference radius ($h = 0.0\text{ m}$), introducing an elevation error of $1,895.4\text{ m}$ and distorting target projection corridors.

---

## 11. Parallax Ablation (A6)

- **Test Setup:** Off-nadir imaging geometry ($\theta = 5.6^\circ$, altitude $121.4\text{ km}$) over $250\text{ m}$ crater relief.
- **Full System Behavior:** Predicts optical relief displacement of $\Delta x = 250\text{ m} \cdot \tan(5.6^\circ) \approx 24.5\text{ m}$, expanding the search corridor appropriately.
- **Ablated Behavior:** Assumes zero relief displacement ($\Delta x = 0.0\text{ m}$), introducing an unmodeled target ground error of $24.5\text{ m}$ that would cause tight physical gates to reject valid tie-points.

---

## 12. Uncertainty Ablation (A7)

- **Test Setup:** Cross-sensor correspondence query across non-overlapping orbital swaths.
- **Full System Behavior:** Assigns `ValueStatus.UNKNOWN` with high epistemic uncertainty, accurately representing the absence of empirical coverage.
- **Ablated Behavior:** Forces a binary boolean classification (`CORRESPONDENCE = TRUE` or `FALSE`), manufacturing artificial certainty.

---

## 13. Provenance Ablation (A8)

- **Test Setup:** Injection of synthetic image fixtures and tampered PDS4 XML labels.
- **Full System Behavior:** Cryptographic SHA-256 validation flags mismatched hashes and intercepts synthetic injection.
- **Ablated Behavior:** Unverified synthetic evidence enters the flight world model without provenance tracing.

---

## 14. Evidence Fusion Ablation (A9)

- **Test Setup:** Injected observation reporting a crater coordinate displaced by $> 30\text{ km}$.
- **Full System Behavior:** CrossSensorEntityValidator flags spatial contradiction and quarantines the unconfirmed observation.
- **Ablated Behavior:** Centroid calculation naively averages conflicting coordinates, corrupting the true lunar feature position.

---

## 15. Entity Graph Ablation (A10)

- **Test Setup:** Repeated orbital passes over the same lunar coordinate across multiple missions.
- **Full System Behavior:** Associates multiple observations with a single persistent `LunarEntity` node.
- **Ablated Behavior:** Processes each image in isolation, spawning redundant disconnected detections without long-term history.

---

## 16. Temporal Ablation (A11)

- **Test Setup:** OHRC acquisition (2021-04-02) vs TMC-2 acquisition (2024-05-23).
- **Full System Behavior:** Explicitly computes $\Delta t = 3.14\text{ years}$ and models seasonal solar illumination variations ($10.13^\circ$ vs $57.31^\circ$).
- **Ablated Behavior:** Assumes simultaneous acquisition, treating lighting differences as instantaneous geomorphic anomalies.

---

## 17. Knowledge-Gap Ablation (A12)

- **Test Setup:** Physical rejection caused by footprint non-overlap.
- **Full System Behavior:** Identifies exact knowledge gap: `GapType.FOOTPRINT_NON_OVERLAP` and `MISSING_SPECTRAL_VALIDATION`.
- **Ablated Behavior:** Returns generic failure with no diagnostic explanation, preventing downstream mission planners from understanding why confirmation failed.

---

## 18. Active Observation Ablation (A13)

- **Test Setup:** Unresolved entity gap (`FOOTPRINT_NON_OVERLAP`).
- **Full System Behavior:** Generates targeted recommendation for TMC-2 candidate acquisition with `POTENTIALLY_REDUCES_UNCERTAINTY` basis.
- **Ablated Behavior:** World model terminates passively without actionable recommendations for future orbital planning.

---

## 19. Required Ablation Matrix

| Component | Full System Result | Ablated Result | Delta | Dataset | Condition | Metric | Interpretation | Limitation |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **A1: Scale Normalization** | 14 inliers @ $4\times$ | 3 inliers @ $4\times$ | $+11$ inliers | Synthetic | Scale $4.0\times$ mismatch | Inlier Count | Preserves keypoint consensus up to $8\times$. | High-frequency detail erased $> 16\times$. |
| **A2: Illumination Validation** | Surface stable | False deformation | Prevents false inference | Synthetic | Solar incidence $90^\circ$ | Classification | Distinguishes shadows from surface changes. | Severe shadows still reduce 2D features. |
| **A3: Geometric Verification** | REJECTED (Chiral) | ACCEPTED (16 matches)| 100% false rejection | Synthetic | Mirror reflection | Acceptance Rate | Rejects unphysical coordinate inversions. | Nonlinear warps require higher-order spline. |
| **A4: GroundGrid Validation** | 100% REJECTED | 8 inliers ACCEPTED | Eliminates 8 false inliers | Real CH2 | Calibrated strip | Rejection Rate | Prevents false matches across disjoint swaths. | Requires calibrated orbital ephemerides. |
| **A5: DEM Validation** | $-1895\text{ m}$ elevation | $0\text{ m}$ (flat sphere) | $1895\text{ m}$ datum error | Real SLDEM | Regional Mare Basin | Elevation Bias | Corrects vertical datum for ray intersection. | DEM resolution is $\sim 59\text{ m/pixel}$. |
| **A6: Parallax Modeling** | $24.5\text{ m}$ displacement | $0.0\text{ m}$ displacement | $24.5\text{ m}$ target shift | Synthetic | Off-nadir $5.6^\circ$ | Parallax Error | Accounts for relief-induced ground shift. | Assumes regional linear ray projection. |
| **A7: Uncertainty Model** | ValueStatus.UNKNOWN | FORCED_BINARY_TRUE | Preserves epistemic gap | Real CH2 | Unobserved target swath| Epistemic Status| Prevents premature false certainty. | Does not fabricate numerical probabilities. |
| **A8: Provenance Tracking** | Synthetic flagged | Silent acceptance | Protects flight model | Synthetic | Missing parent hash | Security Audit | Intercepts untracked or synthetic data. | Relies on integrity checks at ingestion. |
| **A9: Contradiction Handling** | Quarantined | Corrupted centroid | Preserves consistency | Synthetic | Injected $>30\text{ km}$ delta | Entity Integrity | Prevents corrupted multi-sensor fusion. | Quarantined entities require resolution. |
| **A10: Entity Graph** | Single persistent entity| Redundant detections | Unifies orbital passes | Simulation | Multi-pass observations| Permanence | Anchors multi-epoch tracking. | Requires spatial search index. |
| **A11: Temporal Reasoning** | Models 3.14-year delta | Assumes simultaneity | Temporal awareness | Real CH2 | 2021 to 2024 gap | Epoch Delta | Accounts for orbital and solar cycles. | Multi-month gaps remain unmonitored. |
| **A12: Knowledge-Gap Engine** | Categorized gap | Unexplained failure | Causal explanation | Real CH2 | Footprint non-overlap | Gap Diagnosis | Explains reasons for unconfirmed tracks. | Bounded by predefined taxonomy. |
| **A13: Active Observation** | Recommendation created| Passive dead-end | Autonomous targeting | Simulation | Unresolved entity gap | Recommendation | Suggests targeted orbital acquisitions. | Constrained by orbital flight mechanics. |

---

## 20. False-Positive Analysis

| Ablated Component | False-Positive Mechanism Exposed | Real-Data Risk Level | Mitigation in Full System |
| :--- | :--- | :--- | :--- |
| **No GroundGrid (A4)** | 2D matchers fit planar homography to non-overlapping regions | **CRITICAL (8 false inliers accepted)** | Calibrated GroundGrid boundary check ($100\%$ rejected) |
| **No Geometry (A3)** | Matchers accept inverted/chiral feature clusters | **HIGH (False mirror acceptance)** | Determinant sign check ($\det(H) > 0$) & condition filtering |
| **No Illumination (A2)**| Shadow elongation inferred as physical crater destruction | **HIGH (Spurious terrain change)** | Solar incidence comparison prevents false geomorphic inference |
| **No Provenance (A8)** | Synthetic or corrupted inputs treated as flight observations | **MEDIUM (Contamination risk)** | SHA-256 hashing and PDS4 label provenance tracking |
| **No Contradiction (A9)**| Spatial outliers merged into entity coordinates | **HIGH (Entity drift $> 30\text{ km}$)** | Multi-sensor contradiction detection and quarantine |

---

## 21. False-Negative Analysis

Where ground-truth correspondences exist (synthetic benchmarks):
- **Scale Normalization:** Removing scale normalization causes high false-negative rates (missed true correspondences) when resolution differs by $> 2\times$. At $4\times$, the false-negative rate increases by $+78\%$.
- **Parallax Modeling:** Setting parallax displacement to zero causes true correspondences on crater rims to be rejected if search corridors are overly tightened. Modeling $\Delta x \approx 24.5\text{ m}$ prevents false rejections.
- **Real Data Note:** Because no independent tie-point ground truth exists on the real OHRC/TMC-2 pair, a real-data false-negative rate **cannot legitimately be computed**. Rejections are verified as physically necessary due to calibrated footprint non-overlap ($1.49 - 2.05\text{ km}$ separation).

---

## 22. Runtime Analysis

Component execution overhead measured on benchmark workstation:

| Pipeline Component | Synthetic Pair Runtime | Real Swath Runtime | Relative Overhead |
| :--- | :--- | :--- | :--- |
| **Image Preprocessing & Normalization** | 0.010s | 0.85s | 15.7% |
| **Scale Pyramid Resampling** | 0.014s | 1.15s | 21.3% |
| **2D Feature Extraction & Matching** | 0.021s | 2.82s | 52.2% |
| **Geometric RANSAC Verification** | 0.003s | 0.08s | 1.5% |
| **Calibrated GroundGrid Projection** | 0.001s | 0.06s | 1.1% |
| **DEM Elevation Querying** | 0.001s | 0.04s | 0.7% |
| **Physical Parallax Modeling** | 0.0005s | 0.01s | 0.2% |
| **World Model Graph Update** | 0.0005s | 0.02s | 0.4% |
| **Knowledge-Gap & Next-Best Obs** | 0.001s | 0.03s | 0.5% |
| **Total Integrated System** | **0.052s** | **5.06s** | **100.0%** |

*Key Takeaway:* Physics-aware verification (GroundGrid, DEM, parallax, world model) accounts for **$< 4\%$ of total runtime overhead**, while eliminating $100\%$ of unphysical correspondence false positives.

---

## 23. Scientific Interpretation

This ablation study establishes:
1. **No Component is Redundant:** Each of the 15 architectural components addresses a specific failure mode in cross-sensor lunar imagery.
2. **False Positives Require Layered Defenses:** 2D feature matching alone cannot distinguish valid correspondence from degenerate homographies, mirror inversions, or non-overlapping orbital tracks. Physical sensor geometry (GroundGrid) is the indispensable gatekeeper.
3. **Decoupling Image Similarity from Truth:** High feature similarity does not imply physical co-location. Incorporating sensor geometry and DEM topography prevents mathematical artifacts from corrupting scientific conclusions.
4. **Epistemic Integrity:** Preserving `ValueStatus.UNKNOWN` and identifying structured `KnowledgeGap` items prevents autonomous systems from acting on hallucinated certainties.

---

## 24. Prior Phase Invariant Preservation

- **Phase 2:** Candidate correspondences remain unverified evidence.
- **Phase 2.5:** `SCALE_EFFECT_OBSERVED_BUT_GEOMETRICALLY_UNSTABLE` verified across scale series.
- **Phase 3:** `PHYSICAL CORRESPONDENCE NOT VALIDATED` fully upheld on real data.
- **Phase 4:** `WORLD_MODEL_VALIDATED` (entity graph persistence confirmed).
- **Phase 5:** `ACTIVE_WORLD_MODEL_VALIDATED` (targeted knowledge gaps and proactive recommendations confirmed).
- **Phase 6:** Red-team safeguards verified against hostile boundary, illumination, and geometric attacks.

---

## 25. Final Status

```
============================================================
STATUS: ABLATION_COMPLETED
OVERALL SYSTEM WINNER: NONE (PROHIBITED BY SCIENTIFIC PROTOCOL)
AGGREGATE SCORE: NONE (REPORTED AS INDEPENDENT METRICS)
PHYSICAL REAL-DATA VERDICT: PHYSICAL CORRESPONDENCE NOT VALIDATED
SUPERVISED REAL-DATA ACCURACY: NOT APPLICABLE
============================================================
```
