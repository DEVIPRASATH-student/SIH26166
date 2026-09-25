# LUNARSYNAPSE CENTRAL SCIENTIFIC CLAIM LEDGER

**Project:** LunarSynapse — Physics-Aware, Self-Evolving Multi-Modal Lunar World Model  
**SIH Problem Statement:** SIH26166 — Multi-modal, Sun-angle and Scale Invariant Image Correspondence using Chandrayaan-2 OHRC, TMC-2 and IIRS  
**Framework Version:** Phase 8.7 Validated  
**Audited Date:** 2026-09-24  

---

## 1. Principles of Epistemic Integrity

The LunarSynapse research program operates under strict epistemic controls. No claim of universality, absolute certainty, or unverified real-world performance is permitted. 

Every scientific claim is classified under exactly one of four standardized statuses:
1. **`DEMONSTRATED FOR EVALUATED REAL PAIR`**: Evaluated on actual Chandrayaan-2 flight data products.
2. **`DEMONSTRATED UNDER CONTROLLED CONDITIONS`**: Proven inside rigorous, parameterized synthetic simulation baselines.
3. **`NOT VALIDATED`**: An active hypothesis or open problem where evidence is currently insufficient.
4. **`N/A`**: A metric or claim that cannot mathematically or empirically be established due to the absence of physical ground truth.

---

## 2. Master Scientific Claim Ledger

| ID | Scientific Claim | Status | Empirical Evidence | Scope | Known Limitations |
|---|---|---|---|---|---|
| **CLM-01** | Visual similarity alone produces false correspondence across disparate lunar swaths | **`DEMONSTRATED FOR EVALUATED REAL PAIR`** | Feature matchers (SIFT/ORB) find 1,489 visual candidates between non-overlapping OHRC and TMC-2 frames; rejected 100% by Gate 3 | Evaluated Chandrayaan-2 pair (`ch2_ohr_ncp_20210115` & `ch2_tmc_ncn_20200318`) | Demonstrates negative-control rejection on tested pair; does not establish positive correspondence on arbitrary real pairs |
| **CLM-02** | Real-lunar cross-sensor correspondence accuracy | **`N/A`** | No sub-meter independent lunar ground truth tie points exist for the evaluated flight images | Real Chandrayaan-2 flight data | Real-data accuracy cannot be computed without circular reasoning; real ground truth is unavailable |
| **CLM-03** | Calibrated physical gates reject out-of-bounds geometric candidates | **`DEMONSTRATED FOR EVALUATED REAL PAIR`** | Six physical gates reject candidate projections outside calibrated swath (`GATE3_TARGET_OUTSIDE_CALIBRATED_SWATH`) | Evaluated real flight pair and synthetic boundary controls | Relies on SPICE pushbroom ephemeris and SLDEM2015 datum accuracy |
| **CLM-04** | Scale-invariant correspondence across 20x GSD ratio | **`DEMONSTRATED UNDER CONTROLLED CONDITIONS`** | Scenario B multi-scale synthetic benchmark achieves sub-pixel alignment across 0.25m vs 5.0m resolution | Controlled synthetic simulation with procedural crater geology | Synthetic inlier control does NOT prove real-lunar flight accuracy |
| **CLM-05** | Illumination & sun-angle shadow deception detection | **`DEMONSTRATED UNDER CONTROLLED CONDITIONS`** | Scenario C detects 180° solar azimuth inversion and flags illumination evidence conflict | Controlled synthetic illumination sweep with simulated sun ephemeris | Operates as separate evidence module (Phase 6.2); illumination verification is NOT Gate 5 |
| **CLM-06** | Epistemic uncertainty quantification across multimodal evidence | **`DEMONSTRATED UNDER CONTROLLED CONDITIONS`** | Total uncertainty $U \in [0, 1]$ correctly tracks evidence disagreement, spatial sparsity, and geometric instability | Synthetic stress tests and evaluated real negative pair | Real-lunar empirical uncertainty calibration is NOT established; saturation limit >4 px preserved |
| **CLM-07** | Active Next-Best-Observation recommendation reduces knowledge gaps | **`DEMONSTRATED UNDER CONTROLLED CONDITIONS`** | Expected Information Gain ranks candidate sensors (IIRS, TMC-2, OHRC) to resolve targeted knowledge gaps | Synthetic entity belief updates and simulated sensor orbital profiles | Decision-support recommendation only; real-time spacecraft tasking is NOT performed or claimed |
| **CLM-08** | Persistent Lunar Entity resolution decouples identity from registration | **`DEMONSTRATED UNDER CONTROLLED CONDITIONS`** | Lunar entities maintain stable spatial identities across multiple simulated passes | Graph world model and database persistence | Entity association $\neq$ direct image correspondence; spatial proximity $\neq$ entity identity |
| **CLM-09** | End-to-End Pipeline deterministic reproducibility | **`DEMONSTRATED UNDER CONTROLLED CONDITIONS`** | Automated regression suite (375 tests, 0 failures) reproduces identical states across repeated runs | Local Python 3.13 / SQLite / FastAPI runtime | Production multi-node cloud deployment is NOT validated |

---

## 3. Prohibited Scientific Overclaims & Equivalencies

The following phrasing and concepts are strictly prohibited across all LunarSynapse documentation, code comments, and interfaces:

| Forbidden Claim / Term | Why It Is Scientifically Unsound | Mandated Honest Formulation |
|---|---|---|
| `100% accurate` / `perfect match` | Epistemic and aleatoric uncertainties are always non-zero in real lunar sensing | *Demonstrated under tested conditions* |
| `Confirmed lunar match` | No human or rover has verified ground coordinates in situ | *Candidate correspondence verified against physical models* |
| `WILL_RESOLVE` / `Guaranteed` | Future sensor acquisitions cannot guarantee complete uncertainty elimination | *`POTENTIALLY_REDUCES_UNCERTAINTY`* |
| `Real-time spacecraft tasking` | LunarSynapse produces decision-support telemetry recommendations, not command uploads | *Candidate sensor targeting proposal* |
| `Universally invariant` | Matchers degrade under extreme shadows and terrain slope collapse | *Invariant under evaluated synthetic control parameters* |
| `Gate 5 = Illumination` | Gate 5 is strictly reserved for elevation corridor parallax verification | *Gate 5 = `TARGET_OUTSIDE_ELEVATION_CORRIDOR`* |
| `Real-data accuracy = XX%` | Ground truth coordinates do not exist for evaluated real orbits | *`REAL-DATA ACCURACY = N/A`* |
