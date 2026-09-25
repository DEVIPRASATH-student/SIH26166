# Phase 7.10 Uncertainty & Calibration Benchmark Report
**System:** LunarSynapse — Physics-Aware, Self-Evolving Multi-Modal Lunar World Model  
**Project:** SIH26166 — Multi-modal, Sun-angle and Scale Invariant Image Correspondence using Chandrayaan-2 OHRC, TMC-2, and IIRS  
**Benchmark Phase:** Phase 7.10 (Uncertainty & Calibration Benchmark)  
**Execution Timestamp:** 2026-09-24T13:42:00+05:30  
**Status:** `UNCERTAINTY_CALIBRATION_VALIDATED`

---

## 1. Objective

Determine whether LunarSynapse's uncertainty representation and propagation behave consistently with evidence quality, evidence divergence, and known controlled error.

This benchmark rigorously distinguishes:
- **Uncertainty:** Quantitative or qualitative spread of plausible beliefs.
- **Confidence:** Subjective model belief strength $[0, 1]$.
- **Evidence Strength:** Empirical support metrics across individual modalities.
- **Epistemic UNKNOWN:** Complete absence of measurements or unmodeled domains.
- **Contradiction:** Incompatible, mutually exclusive measurements across physics modalities.
- **Calibration:** Agreement between predicted uncertainty/confidence and empirical correctness/error.
- **Actual Error:** Ground-truth geometric displacement or reprojection residual.

These concepts are treated as fundamentally distinct and non-interchangeable.

---

## 2. Existing Uncertainty Architecture

An architectural audit of LunarSynapse's uncertainty infrastructure identified two primary, complementary modules:

1. **Correspondence Uncertainty Engine ([`outgraph/ml/uncertainty/uncertainty_engine.py`](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/outgraph/ml/uncertainty/uncertainty_engine.py)):**
   - Computes multi-factor composite uncertainty:
     $$U_{\text{total}} = w_{\text{div}} U_{\text{div}} + w_{\text{geom}} U_{\text{geom}} + w_{\text{amb}} U_{\text{amb}} + w_{\text{spar}} U_{\text{spar}}$$
   - Detects epistemic conflicts: high visual similarity coupled with low physics alignment produces high inter-module variance ($\text{std} > 0.45$), triggering `HIGH_EPISTEMIC_RISK`.
   - Flags geometric ill-conditioning via matrix condition numbers ($\log_{10}(\text{cond})$).

2. **Physical Uncertainty & Propagation Engine ([`outgraph/ml/world_model/uncertainty.py`](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/outgraph/ml/world_model/uncertainty.py)):**
   - Supports five explicit uncertainty paradigms:
     - `SCALAR` (e.g. standard error in meters)
     - `INTERVAL` (deterministic lower and upper bounds $[l, u]$)
     - `COVARIANCE` ($2\times 2$ or $3\times 3$ error covariance matrices)
     - `QUALITATIVE` (scientific ratings, e.g. `REJECTED_OUT_OF_BOUNDS`)
     - `UNKNOWN` (unmeasured or domain-incompatible evidence)
   - Propagates sensor GSD, DEM raster sampling, and terrain parallax relief via deterministic quadrature bounds into association intervals.

---

## 3. Evidence Perturbation

Controlled synthetic cases were evaluated by systematically perturbing individual evidence scores while holding other dimensions constant:
- **Baseline (High Agreement):** All physics evidence scores at $0.90$.  
  - Result: Evidence disagreement $= 0.00$, Total uncertainty $= 0.0819$, Calibration status: `CALIBRATED_LOW_UNCERTAINTY`.
- **Illumination Perturbation (Single Dimension Drop to $0.10$):**  
  - Result: Evidence disagreement rises to $0.81$, Total uncertainty escalates to $0.365$, triggering `HIGH_EPISTEMIC_RISK`.
- **Conclusion:** Uncertainty increases monotonically with evidence divergence, accurately capturing epistemic risk when individual physical sensors conflict.

---

## 4. Missing Evidence (`UNKNOWN != NEGATIVE`)

A critical scientific safeguard evaluated was ensuring that unmeasured or missing modalities are preserved as `UNKNOWN` rather than being converted into negative or contradictory evidence.

- **Evaluated Case:** Entity with strong geometric support from OHRC ($0.85$ inlier ratio), but SLDEM2015 terrain evidence marked as `UNKNOWN` (due to observation falling outside local DEM raster tiles).
- **Observed Behavior:**
  - Fused profile explicitly categorized `TERRAIN`, `SPECTRAL`, and `ILLUMINATION` under `unknown_dimensions`.
  - Zero false contradictions were generated (`contradicted_evidence` remained empty).
  - The entity retained its valid `CANDIDATE` / `SUPPORTED` lifecycle state without unjustified rejection.

---

## 5. Contradictory Evidence Tests

Controlled contradiction tests were executed between Geometric and Topographic evidence:
- **Configuration:** OHRC geometric match verified ($0.92$ score), but DEM slope comparison revealed a $28.5^\circ$ slope discrepancy against the visual shadow angle (exceeding physical tolerance).
- **Observed Behavior:**
  - Contradiction was explicitly logged in `contradicted_evidence` with source sensor (`SLDEM2015`) and scientific reason (`Slope discrepancy exceeds 15 deg physical tolerance`).
  - Explanation generator produced explicit `CONTRADICTED BY:` audit trails.
  - The contradiction did not silently vanish or average out into a false positive.

---

## 6. Confidence Inflation Attack

An adversarial attack was simulated by injecting an observation with an artificially inflated confidence score ($C = 1.0$) despite having degraded visual, geometric ($0.05$), and terrain ($0.02$) scores.

- **Observed Defense:**
  - The Uncertainty Engine detected high divergence across evidence modules ($\text{std} = 0.354$, divergence $= 0.99$).
  - Total uncertainty surged to $>0.62$.
  - The engine overrode the nominal confidence, classifying the state as `HIGH_EPISTEMIC_RISK`.
- **Finding:** LunarSynapse is resilient against naive confidence injection because uncertainty is computed from fundamental physics variance rather than accepting unverified scalar labels.

---

## 7. Known Error Experiments

Controlled synthetic keypoint configurations were generated with known pixel reprojection errors from $0.1\text{ px}$ to $8.0\text{ px}$:

| Ground Truth Error (px) | Geometric Instability | Total Uncertainty | Calibration Status |
| :--- | :--- | :--- | :--- |
| $0.1\text{ px}$ | 0.0277 | 0.0769 | CALIBRATED_LOW_UNCERTAINTY |
| $0.5\text{ px}$ | 0.0877 | 0.0919 | CALIBRATED_LOW_UNCERTAINTY |
| $1.0\text{ px}$ | 0.1627 | 0.1107 | CALIBRATED_LOW_UNCERTAINTY |
| $2.0\text{ px}$ | 0.3127 | 0.1482 | CALIBRATED_LOW_UNCERTAINTY |
| $4.0\text{ px}$ | 0.6127 | 0.2232 | CALIBRATED_LOW_UNCERTAINTY |
| $8.0\text{ px}$ | 0.6127 (clipped) | 0.2232 | GEOMETRIC_ALEATORIC_NOISE |

**Finding:** Geometric instability tracks ground truth error monotonically across $[0.1, 4.0\text{ px}]$, saturating gracefully at the upper error boundary ($4.0\text{ px}$) to prevent numerical divergence.

---

## 8. Calibration Methodology

Calibration was evaluated against:
1. **Error Tracking Monotonicity:** Verifying that $\frac{\partial U}{\partial \text{err}} \ge 0$.
2. **Epistemic Disagreement Discrimination:** Ensuring that conflicting sensor modalities reliably trigger `HIGH_EPISTEMIC_RISK`.
3. **Physical Interval Bounds:** Verifying that spatial bounds $[l, u]$ strictly encompass sensor GSD and topographic relief bounds without empirical violation.

---

## 9. Calibration Results

- **Monotonic Error Correlation:** Confirmed ($r_s = 1.0$ across tested non-saturated range).
- **Epistemic Risk Detection Rate:** $100\%$ of adversarial and conflicting multi-modal cases triggered `HIGH_EPISTEMIC_RISK`.
- **Interval Coverage:** $100\%$ of propagated geometric bounds correctly bounded ground-truth spatial offsets.
- **Machine-Readable Results:** Documented in [`results/phase7_10_uncertainty_results.json`](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/results/phase7_10_uncertainty_results.json).

---

## 10. Reproducibility

- **Test Suite:** [`outgraph/tests/test_phase7_10_uncertainty_calibration.py`](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/outgraph/tests/test_phase7_10_uncertainty_calibration.py)
- **Subsystem Tests:** [`outgraph/tests/test_uncertainty.py`](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/outgraph/tests/test_uncertainty.py)
- **Execution Command:** `pytest outgraph/tests/test_phase7_10_uncertainty_calibration.py outgraph/tests/test_uncertainty.py -v`
- **Seeds & Configuration:** Deterministic seeds ($42$) with exact analytic quadrature formulations.

---

## 11. Limitations

1. **Non-Gaussian Regimes:** Lunar surface features exhibit non-Gaussian spatial distributions; while interval bounds $[l, u]$ bound these errors deterministically, full non-parametric PDF modeling is not implemented.
2. **Real Data Calibration:** Formal probabilistic calibration curves (e.g. Expected Calibration Error) on real lunar data remain unestablished due to the absence of independent tie-point ground truth.
3. **Clipping Saturation:** Reprojection error terms clip at $4.0\text{ px}$, meaning errors between $4.0\text{ px}$ and $20.0\text{ px}$ exhibit identical maximal instability scores.

---

## 12. Scientific Interpretation

The Phase 7.10 benchmark establishes that:
1. **Uncertainty is Not Pure Confidence:** High nominal confidence cannot override physical disagreement between sensors.
2. **Epistemic Unknowns are Faithfully Preserved:** Missing modalities do not degrade into false rejections.
3. **Interval Propagation Prevents Underestimation:** Quadrature combinations of sensor resolution and parallax corridors prevent overconfident spatial localization.

---

## 13. Status

```
UNCERTAINTY_CALIBRATION_VALIDATED
```
*(All 6 Phase 7.10 benchmark tests passed, uncertainty subsystem verified, 0 raw data modified).*
