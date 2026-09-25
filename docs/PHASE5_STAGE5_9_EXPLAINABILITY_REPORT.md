# PHASE 5 — STAGE 5.9: WORLD-MODEL EXPLAINABILITY REPORT
**LunarSynapse — Physics-Aware, Self-Evolving Multi-Modal Lunar World Model**
**Date:** 2026-09-24
**Status:** VALIDATED
**Repository:** SIH 26166

---

## 1. Executive Summary

A core objective of LunarSynapse Phase 5 is to make every entity conclusion fully explainable and auditable. Rather than collapsing multi-modal findings into an opaque floating-point probability or confidence score, the world model maintains an explicit decomposition of:
1. **Entity Physical State** (`CANDIDATE`, `SUPPORTED`, `CONFIRMED`, `CONTRADICTED`, `REJECTED`, `INSUFFICIENT_EVIDENCE`)
2. **Supported Evidence** with individual sensor/method provenance
3. **Contradicting Evidence** with physical discrepancy metrics
4. **Unknown / Unvalidated Evidence** preserving missing facts as `UNKNOWN` rather than negative
5. **Identified Knowledge Gaps** stating the exact blocking reason
6. **Physical Uncertainty** across spatial, vertical, and coordinate bounds
7. **Active Next-Best Observation (NBO)** recommendation with qualitative potential impact

Stage 5.9 created the `ExplainabilityEngine` (`outgraph/ml/world_model/explainability.py`) and integrated it into the world model services and REST API (`GET /api/world-model/explain/{entity_id}`).

---

## 2. Explainability Architecture

The explainability module generates structured `EntityExplanationCard` objects adhering to strict scientific auditability principles:

```
+-----------------------------------------------------------------------------------+
|                            ENTITY EXPLANATION CARD                                |
+-----------------------------------------------------------------------------------+
|  Entity ID: crater_cand_001                                                       |
|  Current State: CANDIDATE                                                         |
|  Physical Feature: IMPACT_CRATER                                                  |
|  Centroid Coordinates: (19.851240 deg E, 70.123450 deg S, -1250.00 m)             |
+-----------------------------------------------------------------------------------+
|  SUPPORTED EVIDENCE:                                                              |
|   * [GEOMETRIC] High-resolution morphology resolved (sensor: OHRC)               |
|   * [TERRAIN] Co-located elevation depression detected (sensor: SLDEM2015)        |
+-----------------------------------------------------------------------------------+
|  CONTRADICTING EVIDENCE:                                                          |
|   * (None)                                                                        |
+-----------------------------------------------------------------------------------+
|  UNKNOWN EVIDENCE:                                                                |
|   * [SPECTRAL] Mineralogical absorption unobserved (IIRS data missing)           |
|   * [TEMPORAL] Multi-epoch stability unverified (single epoch available)          |
+-----------------------------------------------------------------------------------+
|  BLOCKING FACTORS:                                                                |
|   * TMC-2 footprint non-overlap (geodetic separation: 1.77 km)                    |
+-----------------------------------------------------------------------------------+
|  ACTIVE KNOWLEDGE GAPS:                                                           |
|   * GAP-01: FOOTPRINT_NON_OVERLAP (Required: adjacent track coverage)             |
|   * GAP-02: MISSING_SPECTRAL_VALIDATION (Required: IIRS cube ingestion)           |
+-----------------------------------------------------------------------------------+
|  RECOMMENDATIONS (NBO):                                                           |
|   * Status: FEASIBLE                                                              |
|   * Potential: HIGH_POTENTIAL                                                     |
|   * Statement: "Potentially reduces uncertainty via adjacent observation geometry"|
|   * Note: Orbital flight plan is UNKNOWN                                          |
+-----------------------------------------------------------------------------------+
```

---

## 3. Explainability Invariants Verified

1. **No Opaque Confidence Aggregations:**
   - Every claim is tied to an explicit `Evidence` entry containing `sensor_name`, `product_id`, `method`, and `uncertainty`.
2. **Missing Evidence Stays Unknown:**
   - The card displays missing modalities under `UNKNOWN EVIDENCE:` and explicitly states that absence of evidence is not contradiction.
3. **Traceability to Provenance:**
   - Every line in the card cites the exact source product ID and measurement stage.
4. **Transparent Uncertainty Disclosures:**
   - Spatial footprint bounds and vertical resolution limits (e.g. SLDEM2015 60 m grid limitation) are explicitly rendered.

---

## 4. API and Tooling Integration

- **Module:** `outgraph/ml/world_model/explainability.py`
- **Unit Test:** `outgraph/tests/test_phase5_explainability.py`
- **FastAPI Route:** `GET /api/world-model/explain/{entity_id}`
- **Automated Validation:** Test suite verifies formatted explanation rendering, dictionary serialization, and API query responses without runtime errors.
