# PHASE 5 REPORT: REAL-DATA CASE STUDIES
**Project:** LunarSynapse (SIH 26166)  
**Date:** September 2026  
**Status:** COMPLETE & VERIFIED  
**Stage:** 5.8 — Multi-Scenario Empirical Case Studies

---

## 1. Executive Summary

Stage 5.8 evaluates the Lunar World Model across three scientifically distinct scenarios grounded in the empirical mission data present in `data/real/`. In strict accordance with global scientific rules, absent datasets are explicitly reported as `INSUFFICIENT_REAL_DATA` rather than fabricated.

---

## 2. Case Study A: Physical Swath Non-Overlap & Rejection

### Scenario Context
- **Sensor 1:** Chandrayaan-2 OHRC (`ch2_ohr_ncp_20210402T0546284043_d_img_d18`)
- **Sensor 2:** Chandrayaan-2 TMC-2 (`ch2_tmc_nca_20240523T1600309581_d_img_d18`)
- **Geographic Footprint:** Mare Vaporum / Sinus Medii, near lunar equator.

### Empirical Evaluation
- Calibrated GroundGrid boundary analysis establishes that the eastern boundary of the OHRC swath and the western boundary of the TMC-2 swath are separated by **$1,491.8\text{ m} - 2,051.3\text{ m}$** (mean $1,773.2\text{ m}$).
- The 3D optical relief displacement model demonstrated that maximum realistic terrain elevation variations ($|h| \le 2500\text{ m}$) produce at most **$246.4\text{ m}$** of parallax displacement.
- Inversion of OHRC feature coordinates into TMC-2 detector coordinates yields Scan $-140.2$, which lies outside the calibrated detector array $[0, 80000]$.

### World Model Representation
- **Correspondence Status:** **`PHYSICAL CORRESPONDENCE NOT VALIDATED`**
- **Association Status:** **`REJECTED`** (`GATE3_TARGET_OUTSIDE_CALIBRATED_SWATH`)
- **Knowledge Gap:** `GAP_FOOTPRINT_NON_OVERLAP` (Severity: `HIGH`, Blocking Reason: `PHYSICAL_FOOTPRINT_SEPARATION`).
- **Next-Best Observation:** Recommends an adjacent western TMC-2 orbital track shifted by $\sim 2.0\text{ km}$ (`POTENTIALLY_REDUCES_UNCERTAINTY`).
- **Conclusion:** Rejection is preserved as a verified scientific fact. Zero artificial correspondence was forced.

---

## 3. Case Study B: Compatible Multi-Sensor Observation (OHRC + SLDEM2015)

### Scenario Context
- **Sensor 1:** Chandrayaan-2 OHRC optical imagery ($0.25\text{ m/px}$)
- **Sensor 2:** SLDEM2015 merged LOLA+TC Digital Elevation Model ($59.2\text{ m/px}$)
- **Target Entity:** `LUNAR-CRATER-MV1` (Lat $0.5542^\circ\text{ N}$, Lon $23.4110^\circ\text{ E}$).

### Empirical Evaluation
- The SLDEM2015 buffered tile (Lat $[0.0^\circ, 1.5^\circ\text{ N}]$, Lon $[23.0^\circ, 24.0^\circ\text{ E}]$) completely encloses the OHRC imaging swath with $0\%$ no-data values.
- Bilinear sampling provides a verified regional elevation of **$-1,892.4\text{ m}$** with regional topographic relief span of $234.84\text{ m}$.
- OHRC sub-meter imagery verifies circular rim sharpness and continuous ejecta across a diameter of $140.0\text{ m}$.

### World Model Representation
- **Overlap Status:** **`VALIDATED_OVERLAP`**
- **Lifecycle Progression:** `CANDIDATE` $\to$ `SUPPORTED` (OHRC) $\to$ **`CONFIRMED`** (corroborated by independent SLDEM2015 altimetry).
- **Evidence Profile:**
  - `GEOMETRIC`: `SUPPORTED` (OHRC GroundGrid, diameter $140.0\text{ m}$, uncertainty $0.25\text{ m}$).
  - `TERRAIN`: `SUPPORTED` (SLDEM2015, elevation $-1,892.4\text{ m}$, uncertainty $15.0\text{ m}$).
- **Archive Limitation Note:** For optical-to-optical stereo overlap between OHRC and independent sensors (such as LROC NAC), status is reported as **`INSUFFICIENT_REAL_OVERLAP_DATA`** within the current local archive.

---

## 4. Case Study C: Multi-Epoch Temporal & Multi-Modal Archive Audit

### Scenario Context
- Audit of multi-temporal coverage and multi-modal spectral datasets across the local workspace.

### Empirical Evaluation
- **Temporal Acquisitions:** The current local archive contains single-epoch Level-2 calibrated swaths for OHRC and TMC-2. Time-series repeat passes over the identical sub-meter footprint are currently absent.
- **Spectral Data:** Directory `data/real/iirs/` contains no raw `.xml` or `.qub` hyperspectral files.

### World Model Representation
- **Temporal Status:** **`INSUFFICIENT_REAL_TEMPORAL_DATA`**
  - Represented in the world model as `TemporalState.INSUFFICIENT_TEMPORAL_EVIDENCE`.
  - Triggers knowledge gap: `MISSING_TEMPORAL_OBSERVATION` (`OPEN`).
- **Spectral Status:** **`INSUFFICIENT_REAL_SPECTRAL_DATA`**
  - Modality explicitly recorded as `UNKNOWN`.
  - Triggers knowledge gap: `MISSING_SPECTRAL_VALIDATION` (`OPEN`).
  - Next-Best Observation suggests targeting `IIRS` across $0.8 - 5.0\,\mu\text{m}$ absorption bands (`POTENTIALLY_REDUCES_UNCERTAINTY`).
- **Conclusion:** The system preserves scientific truth by documenting data limitations rather than fabricating pseudo-measurements.
