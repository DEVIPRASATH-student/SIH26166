# PHASE 6 — SUB-STAGE 6.2 REPORT
## Sun-Angle Change / Illumination Deception Attack

**Project:** LunarSynapse (SIH 26166) — Physics-Aware, Self-Evolving Multi-Modal Lunar World Model  
**Sub-Stage:** Phase 6.2 (Sun-Angle Change & Illumination Deception Red-Teaming)  
**Date:** September 2026  
**Auditor:** Automated Scientific Red-Team  
**Status:** `DEFENSE_SUCCESSFUL` (Observational Differences Decoupled from Physical Change)  

---

## 1. Objective

The objective of Sub-Stage 6.2 is to red-team LunarSynapse's temporal reasoning, feature correspondence, and entity lifecycle pipelines against changes in image appearance caused purely by solar illumination variations.

The central scientific question evaluated is:  
*Can substantial variations in image appearance caused by solar azimuth, solar elevation, shadow elongation, brightness, and contrast cause LunarSynapse to incorrectly infer physical surface change, false correspondence, contradictory entity evidence, or unjustified confidence?*

The system must rigorously differentiate **OBSERVATIONAL DIFFERENCE** (solar illumination and viewing geometry) from **GENUINE PHYSICAL CHANGE** (impact cratering, boulder displacement, tectonic deformation).

---

## 2. Threat Model

The attack vectors were systematically categorized across seven scenarios:
1. **Scenario A (Azimuth Divergence):** Identical topography observed under a $90^\circ$ solar azimuth rotation ($\phi = 45^\circ \to 135^\circ$), rotating shadow orientations and altering reflectance gradients.
2. **Scenario B (Solar Elevation & Shadow Length):** High solar elevation ($50^\circ$, short shadows) versus low grazing sun ($10^\circ$, elongated shadows where shadow length $L = h / \tan(10^\circ) \approx 5.67 \times h$).
3. **Scenario C (Severe Brightness/Albedo Shifts):** Over $>40\%$ mean image brightness disparity without physical topography change.
4. **Scenario D (Shadow-Dominated Terrain):** Deep crater interiors where over $50\%$ of floor detail is obscured by opposing shadows ($\Delta\phi = 180^\circ$).
5. **Scenario E (Multi-Epoch Solar Cycles):** 4-epoch observation sequence spanning $>1000$ days with cycling seasonal solar angles over a static crater.
6. **Scenario F (Complete Contrast Inversion):** $180^\circ$ opposite sun directions (East sun vs. West sun) where illuminated and shaded crater walls completely reverse.
7. **Scenario G (Sensitivity vs. Specificity Control):** Disambiguating illumination-only variance from genuine structural change (controlled $35\text{ m}$ crater expansion).

---

## 3. Synthetic Provenance

In strict compliance with Rules 1, 2, and 7:
- All illumination experiments utilized physically grounded synthetic simulations (`outgraph/ml/synthetic_data/terrain_generator.py` and `sensor_simulator.py`).
- Every synthetic observation was tagged with `is_synthetic=True` and `"disclaimer": "SYNTHETIC / DEMO DATA - Physics-grounded simulation"`.
- Zero synthetic illumination artifacts were mixed with real mission observations or written into `data/real/`.
- `data/real/` remained 100% read-only.

---

## 4. Scenario Definitions & Setup

| Scenario | Topography | Solar Azimuth ($\phi$) | Solar Elevation ($\theta$) | Apparent Brightness | Expected Physical State |
|---|---|---|---|---|---|
| **Scenario A** | Fixed crater ($r=50\text{m}, h=20\text{m}$) | $45^\circ \to 135^\circ$ ($\Delta\phi=90^\circ$) | $25^\circ \to 25^\circ$ | Shift $> 0.15$ | `STABLE` |
| **Scenario B** | Fixed crater ($r=50\text{m}, h=20\text{m}$) | $60^\circ \to 60^\circ$ | $50^\circ \to 10^\circ$ ($\Delta\theta=40^\circ$) | Elongated shadows | `STABLE` |
| **Scenario C** | Fixed entity (`SYNTH-ENTITY-BRT`) | $45^\circ \to 45^\circ$ | $30^\circ \to 30^\circ$ | $0.30 \to 0.72$ ($\Delta=0.42$) | `STABLE` (no contradiction) |
| **Scenario D** | Deep crater ($>50\%$ shadow) | $30^\circ \to 210^\circ$ ($\Delta\phi=180^\circ$) | $15^\circ \to 15^\circ$ | Reversal | `REJECTED` / `AMBIGUOUS` |
| **Scenario E** | 4-epoch multi-year cycle | $45^\circ \to 120^\circ \to 220^\circ \to 45^\circ$ | $25^\circ \to 30^\circ \to 15^\circ \to 25^\circ$ | Variable | `STABLE` (Span $>1000$d) |
| **Scenario F** | Contrast inversion | $90^\circ \to 270^\circ$ ($\Delta\phi=180^\circ$) | $20^\circ \to 20^\circ$ | Wall albedo inverted | `STABLE` |
| **Scenario G1** | Negative Control | $45^\circ \to 135^\circ$ | $25^\circ \to 25^\circ$ | Variable, Diam $80\text{m} \to 80\text{m}$ | `STABLE` |
| **Scenario G2** | Positive Control | $45^\circ \to 45^\circ$ | $25^\circ \to 25^\circ$ | Constant, Diam $80\text{m} \to 115\text{m}$ | `CHANGE_SUPPORTED` |

---

## 5. Solar Geometry & Photometric Physics

Simulations were rendered using the hybrid Lunar-Lambert / Lommel-Seeliger photometric function:
$$r(\alpha, i, e) = (1 - c) \frac{\cos(i)}{\cos(i) + \cos(e)} + c \cos(i)$$
where:
- $i$ is local incidence angle relative to surface normal $\mathbf{n}$,
- $e$ is emission angle (near-nadir, $e \approx 0^\circ$),
- $\alpha = |i - e|$ is phase angle,
- $c = 0.6$ is the lunar empirical limb-darkening weight.
Shadow ray-casting explicitly identifies grazing slopes where $\cos(i) \le 0$.

---

## 6. Image & Appearance Changes

- **Mean Radiometric Disparity:** In Scenario A, mean absolute image difference between $45^\circ$ and $135^\circ$ azimuth was $> 15.0$ DN (8-bit grayscale), representing substantial apparent visual difference.
- **Shadow Area Fraction:** In Scenario B, reducing solar elevation from $50^\circ$ to $10^\circ$ increased the crater shadow fraction from $11.4\%$ to $58.2\%$, dramatically shifting the apparent centroid of interior dark patches.
- **Highlight/Shadow Reversal:** In Scenarios D and F, the western crater wall shifted from maximum illumination to total shadow.

---

## 7. Temporal Reasoning Results

The `TemporalReasoningEngine` was tested against all multi-epoch timelines:
1. In Scenario A, solar azimuth shift ($\Delta\phi = 90^\circ$) was chronicled in `observed_differences`, and the state was classified as `STABLE` (`physical_change_supported = False`).
2. In Scenario B, solar elevation shift ($\Delta\theta = 40^\circ$) was chronicled in `observed_differences`, and the state was classified as `STABLE`.
3. In Scenario C, apparent brightness shift ($\Delta I = 0.42$) was chronicled, maintaining `STABLE`.
4. In Scenario E, across 4 epochs spanning 1095 days, seasonal solar cycling was recognized as observational variance, maintaining `STABLE`.
5. In Scenario F, contrast inversion was classified as `STABLE`.
6. **Zero false-positive `CHANGE_SUPPORTED` classifications occurred in any illumination-only test.**

---

## 8. Correspondence Results

- **Illumination Verifier Defense (Scenario D):** Opposing solar illumination ($\Delta\phi = 180^\circ$) was evaluated in `IlluminationVerifier`.
  - Gradient alignment score dropped to negative correlation ($\cos \text{sim} \approx -0.85$).
  - `illumination_score = 0.22` (below the $0.35$ minimum validity threshold).
  - `is_valid = False` with reason: `"Illumination Failure: Illumination conflict: high solar divergence (ΔAz=180.0°, shadow orientation mismatch)"`.
  - **Result:** The system strictly refused to treat shifting shadow boundaries as stable surface correspondence.

---

## 9. Entity Lifecycle Results

- Evaluated in `EntityResolver` and `CrossSensorEntityValidator`:
  - Entities subjected to severe brightness shifts and shadow changes did **not** transition to `CONTRADICTED` or `REJECTED`.
  - Entities remained in their validated physical state (`CANDIDATE` or `SUPPORTED`).
  - Observational shifts were recorded in entity evidence profiles without degrading spatial integrity.

---

## 10. Evidence-Fusion Behavior

- The 11-dimensional `EvidenceFusionEngine` properly categorized solar angle variations under `EvidenceType.ILLUMINATION`.
- Illumination evidence remained completely decoupled from `EvidenceType.GEOMETRIC` and `EvidenceType.TERRAIN`.
- Confirmed that photometric brightness differences cannot override 3D geometric invariant checks.

---

## 11. Expected vs. Actual Behavior

| Scenario | Expected Output | Actual Output | Red-Team Decision |
|---|---|---|---|
| Azimuth shift ($90^\circ$), same terrain | `STABLE`, no change | `STABLE`, `change_supported=False` | **DEFENSE PASSED** |
| Elevation shift ($50^\circ \to 10^\circ$) | `STABLE`, no change | `STABLE`, `change_supported=False` | **DEFENSE PASSED** |
| Brightness shift ($\Delta=0.42$) | `STABLE`, no contradiction | `STABLE`, entity state preserved | **DEFENSE PASSED** |
| Deep crater opposing shadows ($180^\circ$) | `is_valid=False`, low score | `is_valid=False`, score $0.22 < 0.35$ | **DEFENSE PASSED** |
| 4-epoch multi-year solar cycle | `STABLE`, 4 epochs | `STABLE`, span 1095d, 4 epochs | **DEFENSE PASSED** |
| Contrast inversion ($180^\circ$) | `STABLE`, no destruction | `STABLE`, `change_supported=False` | **DEFENSE PASSED** |
| Positive control ($35\text{m}$ expansion) | `CHANGE_SUPPORTED` | `CHANGE_SUPPORTED`, `change_supported=True` | **DEFENSE PASSED** |

---

## 12. False-Positive Analysis

- **False-Positive Physical Change Detections:** **0 (Zero)**.
- Across all synthetic illumination attacks, in zero instances was an illumination, shadow, or brightness artifact classified as physical surface change.
- In Scenario G, the system correctly distinguished the negative control (`STABLE`) from the positive control (`CHANGE_SUPPORTED`), proving that the temporal engine possesses both **high specificity** (resisting false alarms) and **high sensitivity** (detecting true changes).

---

## 13. Uncertainty Behavior

- Multi-epoch observations under divergent illumination correctly flag increased observational uncertainty without fabricating epistemic contradictions.
- Temporal analysis output explicitly populates `observed_differences` for full provenance and traceability.

---

## 14. Knowledge-Gap Behavior

- In the presence of ambiguous change claims where geometric shift is accompanied by extreme solar divergence, the engine outputs `POSSIBLE_CHANGE` with the explanation:  
  *"Apparent geometric differences observed alongside significant solar angle shifts; requires normalized illumination validation."*
- This correctly creates an epistemic knowledge gap rather than asserting ungrounded certainty.

---

## 15. Vulnerabilities Discovered

### Vulnerability Red-Team Discovery: Solar Elevation Blindspot in Temporal Ingestion
- **Discovery:** In the baseline `TemporalReasoningEngine` (`outgraph/ml/world_model/temporal.py`), the illumination shift detector only tested `solar_azimuth_deg` ($\Delta\phi > 10.0^\circ$) and `apparent_brightness` ($\Delta I > 0.15$). It did **not** test `solar_elevation_deg` or `incidence_angle_deg`.
- **Attack Vector:** An attacker presenting two observations with identical azimuth ($\phi = 60^\circ$) but radically different elevations ($50^\circ$ vs. $10^\circ$) would alter shadow lengths by a factor of 5. If automated edge detection suffered apparent rim expansion from the grazing shadow, `has_geometric_shift` would be set while `has_illumination_shift` remained false, triggering a false-positive `CHANGE_SUPPORTED`.
- **Severity:** Medium (robustness gap under low-sun grazing geometry).

---

## 16. Corrections Made

In strict accordance with the Sub-Stage Protocol:
- **Correction Applied:** Updated `outgraph/ml/world_model/temporal.py` (lines 107-123) to explicitly monitor `solar_elevation_deg` ($\Delta\theta > 5.0^\circ$) and `incidence_angle_deg` ($\Delta i > 5.0^\circ$), and set `has_illumination_shift = True` on significant brightness shifts.
- **Verification:** Scenario B test and full regression suite confirmed that solar elevation shifts are now deterministically caught and logged as observational illumination differences.

---

## 17. Test Results

- **New Phase 6.2 Tests:** **7 passed, 0 failed** in 2.69s (`outgraph/tests/test_phase6_2_illumination.py`).
- **Relevant Phase 5 Temporal Suite:** **24 passed, 0 failed** in 1.25s (`test_phase5_temporal.py`, `test_entity_association.py`, `test_evidence_model.py`, `test_world_graph.py`).
- **Full Regression Suite:** **206 passed, 0 failed, 442 warnings** in 105.12s.
- **Regressions:** **0 (Zero)**.

---

## 18. Scientific Limitations

1. **Hapke Photometric Parameter Homogeneity:** The synthetic sensor simulator uses a global lunar limb-darkening parameter ($c = 0.6$) and uniform Lommel-Seeliger scattering. Natural lunar regolith exhibits localized opposition surges and coherent backscatter effects at phase angles $< 2^\circ$, which are not modeled in these simulations.
2. **Sub-Pixel Rim Shadow Creep:** Under extreme grazing angles ($\theta < 5^\circ$), crater rim shadows extend kilometers across adjacent terrain, potentially obscuring independent ground control points. Normalized illumination orthorectification is required for sub-meter feature extraction under extreme grazing angles.
3. **Absence of Real Multi-Epoch Temporal Pairs in Local Storage:** `data/real/` currently contains a single OHRC Level-2 product and a single TMC-2 Level-2 product. Real temporal change benchmarking requires multi-epoch repeat-pass products from the Chandrayaan-2 mission archive.

---

## 19. Raw-Data Integrity Confirmation

- All files in `data/real/` (`data/real/ohrc/`, `data/real/tmc2/`, `data/real/dem/`, `data/real/iirs/`, `data/real/lro_nac/`, `data/real/selene/`):
  - **100% UNMODIFIED**.
  - All Phase 6.2 tests used purely synthetic observations explicitly isolated from real product directories.

---

## 20. Phase 3 / 4 / 5 Preservation Status

- **Phase 3 Physical Gates:** `PRESERVED` (All 6 physical gates, GroundGrid projections, and parallax models intact).
- **Phase 4 World Model:** `PRESERVED` (Entity states, evidence profiles, world graph, and uncertainty models intact).
- **Phase 5 Temporal & Active Model:** `PRESERVED` (Multi-observation matrix, cross-sensor validation, and temporal reasoning intact).

---

## 21. Sub-Stage Gate Decision

Sub-Stage 6.2 execution is **COMPLETE** and **SUCCESSFUL**. The LunarSynapse temporal and correspondence reasoning engines are verified resilient against solar angle and illumination deception.

**Recommended Next Step:** Await explicit user authorization to proceed to **Phase 6.3: Extreme Scale Disparity Stress (20:1 GSD Ratio)**.
