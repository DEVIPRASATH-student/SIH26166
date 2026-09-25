# PHASE 3 — STAGE 3.3: ELEVATION-DEPENDENT PARALLAX MODEL REPORT
**LunarSynapse Scientific Technical Documentation**  
**Date:** September 2026  
**Status:** COMPLETE (Stage 3.3 Gate Passed)  
**Execution Context:** Optical Pushbroom Relief Displacement & Parallax Modeling  

---

## 1. Executive Summary & Core Physical Objective

In Phase 3 Stage 3.3, LunarSynapse formulated and implemented the **ParallaxModel** (`outgraph/ml/geometry/parallax_model.py`). It mathematically models how local lunar terrain elevation ($h$) relative to the reference spheroid ($R = 1737.4\text{ km}$) shifts apparent ground coordinates relative to the 2D reference datum ($h_0 = 0.0$).

> [!IMPORTANT]
> **SCIENTIFIC GUARDRAIL & ASSUMPTIONS:**
> 1. **Sensor Geometry:** Pushbroom linear CCD array with near-nadir pointing.
> 2. **Metadata Fidelity:** Uses verified spacecraft altitudes from ISRO PDS metadata (OHRC: $102.71\text{ km}$, TMC-2: $121.43\text{ km}$).
> 3. **No Fabricated Vectors:** Does not invent unvalidated spacecraft attitude rates or dynamic jitter.
> 4. **No Premature Correspondence:** Establishing relief displacement does **NOT** equal validated physical correspondence.

---

## 2. Mathematical Formulation

For an imaging sensor at spacecraft altitude $H$ above the lunar surface:

1. **Cross-Track Look Angle ($\theta_{\text{ct}}$):**
   For a pixel at sample column $x \in [0, N_{\text{samples}}-1]$ with center $x_{\text{center}}$:
   $$\tan(\theta_{\text{ct}}(x)) = \frac{(x - x_{\text{center}}) \cdot \text{GSD}}{H}$$

2. **Horizontal Ground Relief Displacement ($\Delta \vec{x}_{\text{ground}}$):**
   At terrain elevation $h$ (meters relative to datum $h_0 = 0$):
   $$\Delta x_{\text{cross-track}}(h, x) = -h \cdot \tan(\theta_{\text{ct}}(x))$$
   $$\|\Delta \vec{x}_{\text{ground}}(h, x)\| = |h| \cdot \tan(\theta_{\text{look}}(x))$$

3. **Sensor Pixel Displacement ($\Delta p$):**
   $$\Delta p(h, x) = \frac{\Delta x_{\text{cross-track}}(h, x)}{\text{GSD}} = -\frac{h}{H} \cdot (x - x_{\text{center}})$$

### Core Physical Properties Verified:
- **Reference-Datum Invariance ($h = 0$):** $\Delta \vec{x} \equiv 0$, $\Delta p \equiv 0$ (exact Stage 2 preservation).
- **Nadir Invariance ($x = x_{\text{center}}$):** $\theta_{\text{ct}} = 0 \implies \Delta \vec{x} \equiv 0$ (zero relief displacement at true nadir).
- **Physical Directionality:**
  - Depressions ($h < 0$, e.g. lunar mare plains at $h \approx -1900\text{ m}$) displace radially outward (away from nadir).
  - Elevated terrain ($h > 0$, e.g. crater rims) displace radially inward (toward nadir).

---

## 3. Sensor Displacement Limits & The Gap Bridge Analysis

Using validated ISRO orbit altitudes and sensor parameters:

| Parameter | Chandrayaan-2 OHRC | Chandrayaan-2 TMC-2 (Nadir) |
| :--- | :---: | :---: |
| **Spacecraft Altitude ($H$)** | $102.71\text{ km}$ ($102,710\text{ m}$) | $121.43\text{ km}$ ($121,430\text{ m}$) |
| **Ground Sampling Distance (GSD)** | $0.25\text{ m/pixel}$ | $6.0\text{ m/pixel}$ |
| **Total Swath Samples** | $12,000\text{ pixels}$ ($\approx 3.0\text{ km}$) | $4,000\text{ pixels}$ ($\approx 24.0\text{ km}$) |
| **Maximum Off-Nadir Look Angle ($\theta_{\text{max}}$)** | **$0.837^\circ$** | **$5.631^\circ$** |
| **Displacement at $h = -1,890\text{ m}$ (Regional Mean)** | **$27.6\text{ m}$** ($110.4\text{ px}$) | **$186.3\text{ m}$** ($31.1\text{ px}$) |
| **Max Possible Displacement ($|h| \le 2,500\text{ m}$)** | **$36.5\text{ m}$** ($146.1\text{ px}$) | **$246.4\text{ m}$** ($41.1\text{ px}$) |

### Crucial Scientific Discovery:
$$\text{Max Theoretical Parallax Displacement} = \mathbf{246.4\text{ meters}} \ll \mathbf{1,491.8\text{ meters}} = \text{Minimum Measured Footprint Gap}$$

Even under the most extreme realistic elevation relief ($\Delta h = 2,500\text{ m}$), the total parallax displacement ($\approx 246\text{ m}$) is **less than one-sixth of the minimum physical ground separation ($\approx 1.5\text{ km}$)** between the OHRC and TMC-2 products. 

**Conclusion:** Terrain elevation and optical parallax **CANNOT physically bridge the spatial gap** between these two products.

---

## 4. Test Suite Status

Test module: [`outgraph/tests/test_parallax_model.py`](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/outgraph/tests/test_parallax_model.py)  
Status: **7 passed, 0 failed in 0.94s**  
- $h = 0$ gives zero displacement: PASSED
- Nadir center ($x = x_{\text{center}}$) gives zero displacement: PASSED
- Elevation sign directionality (depressions vs elevations): PASSED
- Vectorized array dimension preservation: PASSED
- Deterministic repeatability: PASSED
- Non-finite / out-of-bounds input propagation (NaN): PASSED
- Maximum displacement bounds vs. footprint gap: PASSED

**Stage 3.3 Acceptance Criteria:** FULLY SATISFIED.
