# Phase 7.11 World Model, Knowledge Gap & Active Observation Loop Benchmark Report
**System:** LunarSynapse — Physics-Aware, Self-Evolving Multi-Modal Lunar World Model  
**Project:** SIH26166 — Multi-modal, Sun-angle and Scale Invariant Image Correspondence using Chandrayaan-2 OHRC, TMC-2, and IIRS  
**Benchmark Phase:** Phase 7.11 (World Model / Knowledge Gap / Active Observation Benchmark)  
**Execution Timestamp:** 2026-09-24T14:20:00+05:30  
**Status:** `WORLD_MODEL_BENCHMARK_VALIDATED`

---

## 1. Objective

Evaluate whether LunarSynapse maintains consistent, robust, and scientifically valid representations of:
1. **Persistent Lunar Entities:** Stable identification across multiple sensors and temporal epochs.
2. **Entity Aliasing Resistance:** Prevention of false entity merges between spatially adjacent or visually similar surface features.
3. **Observation-Entity Non-Transitivity:** Enforcing that shared entity observation does not imply direct image correspondence ($A \to X \leftarrow B \not\implies A \leftrightarrow B$).
4. **Temporal Reasoning:** Disambiguating observational changes (sun angle, shadow shifts) from physical morphological changes.
5. **Knowledge Gap Detection:** Exhaustive classification across all 8 supported scientific gap categories.
6. **Next-Best Observation (NBO) Targeting:** Generating targeted, sensor-feasible recommendations strictly using `POTENTIALLY_REDUCES_UNCERTAINTY` language.
7. **Active Feedback Loop Stability:** Preventing oscillation, duplication, and recommendation explosions during self-evolving belief updates.
8. **Negative Controls:** Handling unresolvable gaps without inventing artificial observations or orbital trajectories.
9. **Provenance Preservation:** Ensuring synthetic data remains explicitly synthetic across the entire entity-evidence-graph lifecycle.

---

## 2. Entity Persistence

Evaluated under multi-sensor, multi-epoch observations:
- **Test Configuration:** A candidate crater at latitude $-70.5000^\circ$, longitude $22.8000^\circ$ was successively associated with:
  1. Chandrayaan-2 OHRC ($t_0$, sub-meter optical rim, uncertainty $0.25\text{ m}$)
  2. Chandrayaan-2 TMC-2 ($t_0 + 28\text{ days}$, stereo photogrammetry, uncertainty $5.0\text{ m}$)
  3. SLDEM2015 ($t_0 + 180\text{ days}$, altimetry elevation, uncertainty $15.0\text{ m}$)
- **Observed Behavior:**
  - The entity retained its persistent identity (`ENTITY-PERSIST-001`) across all associations.
  - Lifecycle state transitioned monotonically from `CANDIDATE` $\to$ `SUPPORTED` (1 sensor) $\to$ `CONFIRMED` (multi-sensor corroborated).
  - Spatial offsets within geodetic tolerance ($200\text{ m}$) were integrated into the position variance without fracturing the entity.

---

## 3. Entity Aliasing Resistance

Tested using two distinct, morphologically identical craters separated by $455\text{ m}$ (exceeding the $200\text{ m}$ spatial gate):
- **Observed Behavior:**
  - An observation targeted at Crater B attempted association with Crater A.
  - The spatial resolver explicitly rejected the association: `SPATIAL_DISTANCE_EXCEEDS_TOLERANCE: 454.9m > 200.0m`.
  - Both craters remained strictly independent entities (`CRATER-A != CRATER-B`).
  - Visual similarity did not trigger a false merge.

---

## 4. Observation/Entity Non-Transitivity

Verified the core epistemic guardrail:
$$\text{Obs}_A \xrightarrow{\text{OBSERVES}} \text{Entity}_X \xleftarrow{\text{OBSERVES}} \text{Obs}_B \quad\centernot\implies\quad \text{Obs}_A \xleftrightarrow{\text{CORRESPONDS}} \text{Obs}_B$$
- **Graph Audit:**
  - Nodes: `OBS-A` (OHRC), `OBS-B` (TMC-2), `ENTITY-X`.
  - Ingoing edges: `OBS-A -> ENTITY-X` (`OBSERVES`), `OBS-B -> ENTITY-X` (`OBSERVES`).
  - Verification: `graph.has_valid_correspondence("OBS-A", "OBS-B")` evaluated to `False`. Zero correspondence edges were instantiated.
  - **Scientific Principle:** Shared physical entity association does not prove or replace inter-image pixel correspondence.

---

## 5. Temporal Reasoning & Illumination Disambiguation

Tested multi-epoch observations under extreme solar azimuth inversion ($\Delta \text{azimuth} = 180.0^\circ$, shadow penumbras completely flipped):
- **Inputs:**
  - Epoch 1: Solar azimuth $45^\circ$, elevation $20^\circ$, apparent brightness $110\text{ DN}$, diameter $150.0\text{ m}$.
  - Epoch 2: Solar azimuth $225^\circ$, elevation $20^\circ$, apparent brightness $175\text{ DN}$, diameter $150.2\text{ m}$ (sub-pixel drift).
- **Engine Classification:**
  - Output State: `STABLE`
  - `physical_change_supported`: `False`
  - Observed differences logged: `Solar azimuth shifted by 180.0° between EP-1 and EP-2`, `Apparent pixel brightness shifted by 65.00`.
  - Synthesis Explanation: *"Observational differences detected (solar azimuth/incidence angle shift), but physical structure remains STABLE."*
  - **Result:** $0.0\%$ false-positive physical change rate under severe illumination variations.

---

## 6. Knowledge-Gap Systematic Benchmark

Evaluated across all 8 supported scientific gap categories in [`outgraph/ml/world_model/knowledge_gap.py`](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/outgraph/ml/world_model/knowledge_gap.py):

| Scenario | Target Knowledge Gap Category | Triggering Condition | Blocking Reason / Provenance | Status |
| :--- | :--- | :--- | :--- | :--- |
| **1** | `MISSING_SPECTRAL_VALIDATION` | Entity lacks IIRS hyperspectral cube | `NO_SPECTRAL_DATA_ATTACHED` | **PASSED** |
| **2** | `MISSING_TEMPORAL_OBSERVATION` | Only single-epoch acquisition available | `association_count = 1` | **PASSED** |
| **3** | `MISSING_GEOMETRIC_VALIDATION` | Unvalidated initial candidate keypoints | `checked_evidence: GEOMETRIC` | **PASSED** |
| **4** | `MISSING_TERRAIN_VALIDATION` | Entity lacks DEM elevation ($h = \text{None}$) | `checked_evidence: TERRAIN` | **PASSED** |
| **5** | `MISSING_MODALITY` | No auxiliary altimetry/spectral channels | `checked_evidence: MODALITY` | **PASSED** |
| **6** | `INSUFFICIENT_CORRESPONDENCE` | Mono-sensor observation lacks independent link | `sensor_count = 1` | **PASSED** |
| **7** | `FOOTPRINT_NON_OVERLAP` | Phase 3 swath rejection ($1.8\text{ km}$ separation) | `PHYSICAL_FOOTPRINT_SEPARATION` | **PASSED** |
| **8** | `UNCERTAINTY_TOO_HIGH` | Spatial uncertainty ($75\text{ m}$) $> 50\text{ m}$ tolerance | `uncertainty_m = 75.0` | **PASSED** |

**Pass Rate:** $8 / 8$ ($100.0\%$).

---

## 7. Active Observation & NBO Behavior

Evaluated recommendations generated by [`NextBestObservationEngine`](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/outgraph/ml/world_model/next_best_observation.py):
- **Language Policy Verification:**
  - Every recommendation uses: `POTENTIALLY_REDUCES_UNCERTAINTY`.
  - Forbidden terms (`WILL_RESOLVE`, `GUARANTEED_TO_RESOLVE`, `OPTIMAL_TRAJECTORY`) were **absent** from all generated payloads.
- **Feasibility Scenarios:**
  - `FOOTPRINT_NON_OVERLAP` $\to$ Targeted adjacent track TMC-2 acquisition (`FEASIBLE`).
  - `MISSING_SPECTRAL_VALIDATION` $\to$ IIRS nadir cube recommendation (`FEASIBLE`).

---

## 8. Active Loop Oscillation Resistance

Tested closed-loop evolution in [`ActiveWorldModelLoop`](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/outgraph/ml/world_model/active_loop.py):
$$\text{Observation} \to \text{Entity} \to \text{Gaps} \to \text{NBO} \to \text{Follow-up} \to \text{Belief Update}$$
- **Execution Log:**
  1. Pass 1: Initial OHRC observation created `SUPPORTED` entity with 3 open gaps (`MISSING_TERRAIN_VALIDATION`, `MISSING_SPECTRAL_VALIDATION`, `MISSING_TEMPORAL_OBSERVATION`).
  2. Follow-up: Recommended SLDEM2015 altimetry ingested ($h = -1892.4\text{ m}$).
  3. Resolution: `MISSING_TERRAIN_VALIDATION` transitioned from `OPEN` to `RESOLVED`.
  4. Entity state advanced to `CONFIRMED`.
- **Oscillation Check:** Zero duplicate recommendations; resolved gaps were not re-emitted; recommendation count remained bounded ($100\%$ unique IDs).

---

## 9. Negative Controls (No-Action)

Tested scenarios where required sensor payloads are unavailable:
- **Condition:** Entity with `MISSING_SPECTRAL_VALIDATION` evaluated under a restricted sensor catalog containing only `OHRC`.
- **Observed Behavior:**
  - NBO engine correctly identified candidate sensor `IIRS`, but marked feasibility as `PAYLOAD_UNAVAILABLE`.
  - The system did **not** invent an observation or attempt to substitute an unsuitable sensor.

---

## 10. Provenance Preservation

- **Synthetic Data Tracking:** Synthetic observations ingested during the active loop maintained `is_synthetic = True` across graph nodes (`OBS-SYNTH-DEM`), evidence items (`EV-FOLLOWUP-TERR`), and execution logs.
- **Provenance Retention:** Source processing stages, sensor names, and timestamps survived multi-epoch entity aggregation without loss.

---

## 11. Results Summary

- **Phase 7.11 Dedicated Tests:** 9 / 9 passed.
- **Subsystem Regression Tests:** 56 / 56 passed.
- **Full Suite Regression:** 293 passed, 0 failed.
- **Machine-Readable Table:** Saved to [`results/phase7_11_world_model_results.json`](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/results/phase7_11_world_model_results.json).

---

## 12. Limitations

1. **Simulated Orbital Geometry:** Active observation recommendations propose geometric viewing geometries (e.g. adjacent swath shifted by $\sim 2\text{ km}$), but do not calculate full orbital mechanics, spacecraft fuel budgets, or ground station downlink schedules.
2. **Synthetic Active Execution:** Active loop gap closure was validated using synthetic follow-up payloads; real spacecraft tasking is outside the scope of this repository.

---

## 13. Scientific Interpretation

The Phase 7.11 benchmark scientifically validates that:
1. **World Model Entities Decouple Feature Matching from Surface Knowledge:** An entity can accumulate physical evidence across missions without requiring direct pixel-to-pixel correspondence between every pair of images.
2. **Epistemic Blind Spots are First-Class Objects:** Knowledge gaps are structured, queryable, and auditable rather than silent unhandled exceptions.
3. **Active Recommendations are Derived Hypotheses:** By enforcing `POTENTIALLY_REDUCES_UNCERTAINTY`, the system preserves epistemic humility and prevents unjustified operational claims.

---

## 14. Status

```
WORLD_MODEL_BENCHMARK_VALIDATED
```
*(All 9 Phase 7.11 tests passing, knowledge gap benchmark 100% verified, 0 raw data modified).*
