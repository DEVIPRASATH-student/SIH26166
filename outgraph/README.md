# 🌙 LunarSynapse
### Physics-Aware, Self-Evolving Multi-Modal Lunar World Model

[![SIH26166](https://img.shields.io/badge/SIH%20Challenge-SIH26166-38bdf8.svg?style=flat)]()
[![Backend](https://img.shields.io/badge/Backend-FastAPI%20%7C%20Python%203.13-009688.svg?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Frontend](https://img.shields.io/badge/Frontend-React%2018%20%7C%20Vite%206%20%7C%20TS-61DAFB.svg?style=flat&logo=react&logoColor=black)](https://react.dev)
[![Status](https://img.shields.io/badge/Phase-8.7%20Validated-brightgreen.svg?style=flat)]()

> **System-Level Novelty Statement:**  
> *"LunarSynapse shifts lunar image correspondence from finding visually similar pixels to building and reasoning over physically validated, uncertainty-aware evidence about persistent lunar entities."*

---

## 🧭 Project Overview & Scientific Demarcation

LunarSynapse addresses SIH Problem Statement **SIH26166** (*Multi-modal, Sun-angle and Scale Invariant Image Correspondence using Chandrayaan-2 OHRC, TMC-2 and IIRS*).

The system replaces naive feature registration with a physics-gated world model reasoning loop:
1. **Raw Observation Ingestion:** Reads flight PDS4 images (OHRC, TMC-2) and controlled synthetic scenarios.
2. **Feature Candidate Extraction:** Generates initial tie-point candidates using standard extractors (SIFT, ORB, LoFTR adapters).
3. **Six Immutable Physical Gates:**
   - Gate 1: `INVALID_SOURCE_GROUNDGRID`
   - Gate 2: `DEM_OUT_OF_BOUNDS_OR_NODATA`
   - Gate 3: `TARGET_OUTSIDE_CALIBRATED_SWATH`
   - Gate 4: `TARGET_CLAMPED_TO_SWATH_BOUNDARY`
   - Gate 5: `TARGET_OUTSIDE_ELEVATION_CORRIDOR`
   - Gate 6: `BIDIRECTIONAL_RESIDUAL_TOO_LARGE`
   - *Note:* Illumination verification operates as a separate evidence module (Phase 6.2); it is **NOT Gate 5**.
4. **Epistemic Uncertainty Quantification:** Aggregates geometric instability, feature ambiguity, spatial sparsity, and evidence disagreement into $U \in [0, 1]$.
5. **Persistent Lunar Entity Resolution:** Maps verified correspondences into persistent entities (`LUNAR-ENTITY-XXX`) in an interactive NetworkX knowledge graph.
6. **Knowledge Gap & Next-Best-Observation Engine:** Autonomously detects open scientific questions and formulates ranked sensor recommendations under the strict operator `POTENTIALLY_REDUCES_UNCERTAINTY`.

---

## ⚡ Quick Start

### Installation
```bash
# Setup Python Environment
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r outgraph/requirements.txt

# Setup Frontend
cd outgraph/frontend
npm install
cd ../..
```

### Execution
```bash
# Backend (Port 8000)
python -m uvicorn outgraph.backend.app.main:app --host 127.0.0.1 --port 8000

# Frontend (Port 5173)
cd outgraph/frontend
npm run dev
```

### Testing & Verification
```bash
# Phase 8.6 Reliability Suite
pytest outgraph/tests/test_phase8_6_reliability.py -v

# Phase 8.7 Reproducibility Suite
pytest outgraph/tests/test_phase8_7_reproducibility.py -v

# Complete Regression Suite
pytest outgraph/tests/ -v

# Frontend Production Build
cd outgraph/frontend
npm run build
```

---

## 📊 Scientific Claims & Statuses

| Claim | Status |
|---|---|
| Visual similarity produces false matches on non-overlapping real lunar frames | `DEMONSTRATED FOR EVALUATED REAL PAIR` |
| Real-lunar cross-sensor correspondence accuracy | `N/A` (no independent ground truth tie points exist) |
| Six physical gates reject spurious candidates | `DEMONSTRATED FOR EVALUATED REAL PAIR` |
| Scale invariance across 20x GSD ratio | `DEMONSTRATED UNDER CONTROLLED CONDITIONS` |
| Illumination & shadow deception rejection | `DEMONSTRATED UNDER CONTROLLED CONDITIONS` |
| Multi-dimensional uncertainty quantification | `DEMONSTRATED UNDER CONTROLLED CONDITIONS` |
| Active Next-Best-Observation targeting | `DEMONSTRATED UNDER CONTROLLED CONDITIONS` |
| Production Cloud Deployment | `DEPLOYMENT ARCHITECTURE DOCUMENTED — PRODUCTION DEPLOYMENT NOT VALIDATED` |

For full details, see the central [Claim Ledger](../docs/CLAIM_LEDGER.md).
