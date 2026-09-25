# PHASE 4 STAGE 4.4 REPORT: UNCERTAINTY PROPAGATION ENGINE
**Project:** LunarSynapse (SIH 26166)  
**Date:** September 2026  
**Status:** COMPLETE & VERIFIED  
**Stage:** 4.4 — Physical Uncertainty Modeling & Deterministic Propagation

---

## 1. Objective

Stage 4.4 integrates the physical uncertainties quantified in Phase 3 into the persistent world model without inventing false Gaussian distributions or fabricating confidence values.

Uncertainty in lunar planetary science arises from diverse physical and instrumental sources:
- Detector pixel pitch and GSD (OHRC $0.25\text{ m}$, TMC-2 $5.0\text{ m}$, IIRS $20.0\text{ m}$).
- DEM spatial raster sampling (SLDEM2015 $\approx 59.2\text{ m/pixel}$).
- Pushbroom parallax and terrain elevation corridor bounds ($\Delta x_{\text{corridor}} \approx 20.3\text{ m}$).
- GroundGrid georeferencing interpolation residuals ($\sim 0.25\text{ m}$).
- Entity spatial offset from observation detection centroids.

---

## 2. Implementation Overview

Implemented in [`outgraph/ml/world_model/uncertainty.py`](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/outgraph/ml/world_model/uncertainty.py).

### 2.1 Supported Uncertainty Representations
1. `SCALAR`: Single precision measurement with physical units (e.g. $0.25\text{ m}$ GSD).
2. `INTERVAL`: Deterministic lower and upper bounds $[l, u]$ (e.g. $[0.25\text{ m}, 62.58\text{ m}]$).
3. `COVARIANCE`: Multi-dimensional covariance matrices (e.g. 2D ground-grid inversion error).
4. `QUALITATIVE`: Descriptive scientific risk ratings (`HIGH_EPISTEMIC_RISK`, `REJECTED_OUT_OF_BOUNDS`).
5. `UNKNOWN`: Explicit absence of uncertainty quantification. Guarded against silent numerical substitution.

### 2.2 Traceable Uncertainty Propagation
The [`UncertaintyPropagator`](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/outgraph/ml/world_model/uncertainty.py#L86-L162) constructs end-to-end traceable [`UncertaintyChain`](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/outgraph/ml/world_model/uncertainty.py#L76-L84) objects:
$$\text{Sensor Source Uncertainty} \longrightarrow \text{Geometric Parallax Uncertainty} \longrightarrow \text{Entity Association Uncertainty} \longrightarrow \text{Hypothesis Uncertainty}$$
Every link in the chain retains its exact source label, preventing loss of provenance.

---

## 3. Verification & Test Results

The test suite in [`outgraph/tests/test_world_model_uncertainty.py`](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/outgraph/tests/test_world_model_uncertainty.py) validated:
1. `test_uncertainty_preservation_types`: Asserts preservation of all 5 uncertainty representations.
2. `test_geometric_uncertainty_propagation`: Asserts proper combination of sensor GSD ($0.25\text{ m}$), DEM resolution ($59.2\text{ m}$), and parallax corridor ($20.3\text{ m}$) into interval bounds $[0.25, 62.58]\text{ m}$.
3. `test_association_uncertainty_propagation`: Verifies propagation across spatial offsets and out-of-bounds rejection flags.
4. `test_no_silent_confidence_on_unknown`: Verifies that unknown inputs propagate as `UNKNOWN` rather than inventing default numbers.
5. `test_traceable_uncertainty_chain`: Confirms traceability of multi-stage uncertainty chains.

**Test Result:** 5 passed, 0 failed.
Baseline 97 tests remain completely untouched and green. Total test count: $97 + 7 + 7 + 5 + 5 = 121$.
