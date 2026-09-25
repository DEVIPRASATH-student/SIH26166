# PHASE 4 STAGE 4.3 REPORT: PERSISTENT LUNAR ENTITY GRAPH
**Project:** LunarSynapse (SIH 26166)  
**Date:** September 2026  
**Status:** COMPLETE & VERIFIED  
**Stage:** 4.3 — Persistent Lunar Entity Knowledge Graph

---

## 1. Objective

Stage 4.3 establishes the structured knowledge graph representation for the Lunar World Model.

The graph interconnects:
- Lunar Entities (`ENTITY`)
- Sensor Observations (`OBSERVATION`)
- Multimodal Scientific Evidence (`EVIDENCE`)
- Physical World Hypotheses (`HYPOTHESIS`)
- Detected Knowledge Gaps (`KNOWLEDGE_GAP`)
- Sensor Recommendations (`RECOMMENDATION`)

### Critical Graph Non-Transitivity Guardrail
A core scientific failure mode in naive knowledge graphs is inferring transitivity across spatial observations:
$$\text{Observation}_{\text{OHRC}} \xrightarrow{\text{OBSERVES}} \text{Entity} \xleftarrow{\text{OBSERVES}} \text{Observation}_{\text{TMC-2}}$$
The world graph strictly rejects the assumption that this path implies an $\text{OHRC} \leftrightarrow \text{TMC-2}$ physical correspondence. Direct physical correspondence strictly requires an explicit, verified `MATCHED_WITH` or `SUPPORTED_BY` edge backed by geometric validation.

---

## 2. Implementation Overview

Implemented in [`outgraph/ml/world_model/graph.py`](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/outgraph/ml/world_model/graph.py) via class [`WorldGraph`](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/outgraph/ml/world_model/graph.py#L36-L235).

### 2.1 Standardized Node Types
- `ENTITY`: Persistent lunar landforms (craters, ridges, boulders).
- `OBSERVATION`: Image swaths and spectral cubes from OHRC, TMC-2, IIRS, etc.
- `EVIDENCE`: Multimodal evidence nodes holding measurements, bounds, and statuses.
- `HYPOTHESIS`: Physical properties and morphology beliefs.
- `KNOWLEDGE_GAP`: Unobserved modalities or high-epistemic-risk blind spots.
- `RECOMMENDATION`: Prioritized payload targeting recommendations.

### 2.2 Standardized Directed Relationships
- `OBSERVES`: Observation views an entity.
- `ASSOCIATED_WITH`: Entity connected to another entity or context.
- `SUPPORTED_BY`: Entity/hypothesis corroborated by evidence.
- `CONTRADICTED_BY`: Entity/hypothesis disputed by evidence.
- `DERIVED_FROM`: Feature derived from raw observation.
- `TEMPORALLY_RELATED`: Time-series acquisitions over the same region.
- `SPATIALLY_RELATED`: Proximity relation without claiming pixel-level correspondence.
- `HYPOTHESIZES`: Entity possesses a physical hypothesis.
- `HAS_UNCERTAINTY`: Edge or node linked to uncertainty breakdown.
- `HAS_GAP`: Entity associated with a specific knowledge gap.
- `RECOMMENDS`: Gap suggests a next-best observation.

### 2.3 Deterministic Serialization
The graph supports exact, deterministic bidirectional serialization to JSON / dictionary formats, sorting nodes and edges alphabetically to guarantee reproducibility across sessions.

---

## 3. Verification & Test Results

The test suite in [`outgraph/tests/test_world_graph.py`](file:///c:/Users/Devi%20Prasath%20S/OneDrive/Scans/Desktop/SIH%2026166/outgraph/tests/test_world_graph.py) validated:
1. `test_graph_creation_and_node_types`: Validates all 6 node types.
2. `test_edge_provenance_and_relations`: Verifies relation types, metadata, and timestamps on edges.
3. `test_non_transitivity_guardrail`: Proves that paths through shared entities do not produce false correspondence claims.
4. `test_contradictory_edge_representation`: Verifies explicit modeling of contradictory evidence edges.
5. `test_graph_serialization_and_deterministic_reconstruction`: Verifies exact round-trip dictionary and JSON serialization.

**Test Result:** 5 passed, 0 failed.
Baseline 97 tests remain completely untouched and green. Total test count: $97 + 7 + 7 + 5 = 116$.
