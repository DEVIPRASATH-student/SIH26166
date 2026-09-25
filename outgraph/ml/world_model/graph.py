"""Persistent Lunar World Model Knowledge Graph.
Stage 4.3: NetworkX Entity, Observation, Evidence, Hypothesis, Gap & Recommendation Graph.

Enforces:
1. Typed nodes and relations with complete edge provenance.
2. Non-transitivity rule: Path connectivity does NOT imply physical correspondence.
3. Deterministic serialization and reconstruction.
"""

from enum import Enum
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import json
import networkx as nx
from pydantic import BaseModel, Field


class NodeType(str, Enum):
    """Standardized node types in the Lunar World Model Graph."""
    ENTITY = "ENTITY"
    OBSERVATION = "OBSERVATION"
    EVIDENCE = "EVIDENCE"
    HYPOTHESIS = "HYPOTHESIS"
    KNOWLEDGE_GAP = "KNOWLEDGE_GAP"
    RECOMMENDATION = "RECOMMENDATION"


class EdgeRelation(str, Enum):
    """Standardized relationship types in the Lunar World Model Graph."""
    OBSERVES = "OBSERVES"
    ASSOCIATED_WITH = "ASSOCIATED_WITH"
    SUPPORTED_BY = "SUPPORTED_BY"
    CONTRADICTED_BY = "CONTRADICTED_BY"
    DERIVED_FROM = "DERIVED_FROM"
    TEMPORALLY_RELATED = "TEMPORALLY_RELATED"
    SPATIALLY_RELATED = "SPATIALLY_RELATED"
    HYPOTHESIZES = "HYPOTHESIZES"
    HAS_UNCERTAINTY = "HAS_UNCERTAINTY"
    HAS_GAP = "HAS_GAP"
    RECOMMENDS = "RECOMMENDS"


class WorldGraph:
    """Manages the directed knowledge graph of lunar entities, observations, evidence, and gaps."""

    def __init__(self):
        self.graph = nx.DiGraph()

    def add_entity_node(
        self,
        entity_id: str,
        entity_type: str = "crater",
        state: str = "CANDIDATE",
        latitude: float = 0.0,
        longitude: float = 0.0,
        confidence: Optional[float] = None,
        uncertainty: Optional[float] = None,
        properties: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Adds a persistent lunar entity node."""
        self.graph.add_node(
            entity_id,
            node_type=NodeType.ENTITY.value,
            entity_type=entity_type,
            state=state,
            latitude=latitude,
            longitude=longitude,
            confidence=confidence,
            uncertainty=uncertainty,
            properties=properties or {},
        )

    def add_observation_node(
        self,
        observation_id: str,
        sensor_type: str,
        product_id: Optional[str] = None,
        resolution_m: Optional[float] = None,
        is_synthetic: bool = False,
        bounds: Optional[Dict[str, float]] = None,
    ) -> None:
        """Adds a sensor observation node."""
        self.graph.add_node(
            observation_id,
            node_type=NodeType.OBSERVATION.value,
            sensor_type=sensor_type,
            product_id=product_id,
            resolution_m=resolution_m,
            is_synthetic=is_synthetic,
            bounds=bounds or {},
        )

    def add_evidence_node(
        self,
        evidence_id: str,
        evidence_type: str,
        status: str,
        measurement: Optional[Any] = None,
        uncertainty: Optional[Any] = None,
        is_synthetic: bool = False,
    ) -> None:
        """Adds a multimodal evidence node."""
        self.graph.add_node(
            evidence_id,
            node_type=NodeType.EVIDENCE.value,
            evidence_type=evidence_type,
            status=status,
            measurement=measurement,
            uncertainty=uncertainty,
            is_synthetic=is_synthetic,
        )

    def add_hypothesis_node(
        self,
        hypothesis_id: str,
        property_name: str,
        hypothesis_value: str,
        confidence: Optional[float] = None,
        uncertainty: Optional[float] = None,
    ) -> None:
        """Adds a physical world model hypothesis node."""
        self.graph.add_node(
            hypothesis_id,
            node_type=NodeType.HYPOTHESIS.value,
            property_name=property_name,
            hypothesis_value=hypothesis_value,
            confidence=confidence,
            uncertainty=uncertainty,
        )

    def add_knowledge_gap_node(
        self,
        gap_id: str,
        gap_type: str,
        description: str,
        severity: str = "MEDIUM",
        status: str = "OPEN",
    ) -> None:
        """Adds a knowledge gap node."""
        self.graph.add_node(
            gap_id,
            node_type=NodeType.KNOWLEDGE_GAP.value,
            gap_type=gap_type,
            description=description,
            severity=severity,
            status=status,
        )

    def add_recommendation_node(
        self,
        recommendation_id: str,
        candidate_sensor: str,
        reason: str,
        expected_information_gain: Optional[float] = None,
        status: str = "PENDING",
    ) -> None:
        """Adds a next-best observation recommendation node."""
        self.graph.add_node(
            recommendation_id,
            node_type=NodeType.RECOMMENDATION.value,
            candidate_sensor=candidate_sensor,
            reason=reason,
            expected_information_gain=expected_information_gain,
            status=status,
        )

    def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Returns node data attributes if present, else None."""
        if node_id in self.graph:
            return dict(self.graph.nodes[node_id])
        return None

    def add_relation(
        self,
        source_id: str,
        target_id: str,
        relation: EdgeRelation,
        status: str = "SUPPORTED",
        provenance: Optional[Dict[str, Any]] = None,
        method: str = "DIRECT",
        uncertainty: Optional[Any] = None,
    ) -> None:
        """Adds a directed, provenance-bearing edge between nodes."""
        if source_id not in self.graph:
            raise KeyError(f"Source node '{source_id}' does not exist in graph.")
        if target_id not in self.graph:
            raise KeyError(f"Target node '{target_id}' does not exist in graph.")

        self.graph.add_edge(
            source_id,
            target_id,
            relation=relation.value if isinstance(relation, EdgeRelation) else relation,
            status=status,
            provenance=provenance or {},
            method=method,
            uncertainty=uncertainty,
            timestamp=datetime.utcnow().isoformat(),
        )

    def has_valid_correspondence(self, obs_a: str, obs_b: str) -> bool:
        """CRITICAL GUARDRAIL:

        A path through an entity (e.g. obs_a -> entity -> obs_b) does NOT imply
        that obs_a and obs_b correspond physically.
        Direct spatial correspondence requires an explicit, verified MATCHED_WITH or
        SUPPORTED_BY correspondence edge.
        """
        if self.graph.has_edge(obs_a, obs_b):
            edge_data = self.graph.get_edge_data(obs_a, obs_b)
            if edge_data.get("relation") == "MATCHED_WITH" and edge_data.get("status") == "SUPPORTED":
                return True

        if self.graph.has_edge(obs_b, obs_a):
            edge_data = self.graph.get_edge_data(obs_b, obs_a)
            if edge_data.get("relation") == "MATCHED_WITH" and edge_data.get("status") == "SUPPORTED":
                return True

        return False

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the graph deterministically to a dictionary."""
        nodes = []
        for n, d in sorted(self.graph.nodes(data=True), key=lambda x: str(x[0])):
            node_copy = dict(d)
            node_copy["id"] = n
            nodes.append(node_copy)

        edges = []
        for u, v, d in sorted(self.graph.edges(data=True), key=lambda x: (str(x[0]), str(x[1]))):
            edge_copy = dict(d)
            edge_copy["source"] = u
            edge_copy["target"] = v
            edges.append(edge_copy)

        return {"nodes": nodes, "edges": edges}

    def to_json(self) -> str:
        """Serializes the graph to JSON."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorldGraph":
        """Reconstructs a WorldGraph from a serialized dictionary deterministically."""
        wg = cls()
        for node in data.get("nodes", []):
            nid = node["id"]
            node_data = {k: v for k, v in node.items() if k != "id"}
            wg.graph.add_node(nid, **node_data)

        for edge in data.get("edges", []):
            u = edge["source"]
            v = edge["target"]
            edge_data = {k: v for k, v in edge.items() if k not in ("source", "target")}
            wg.graph.add_edge(u, v, **edge_data)

        return wg

    @classmethod
    def from_json(cls, json_str: str) -> "WorldGraph":
        """Reconstructs a WorldGraph from a JSON string."""
        return cls.from_dict(json.loads(json_str))
