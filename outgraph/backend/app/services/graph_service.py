"""Lunar Entity Graph Service using NetworkX.
Maintains relational knowledge graph of entities, observations, sensors, evidence, and hypotheses.
Exports React Flow compatible graph visualizations.
"""

import json
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
import networkx as nx

from ..models.lunar_entity import LunarEntityModel, EntityObservationModel, WorldModelHypothesisModel
from ..models.observation import ObservationModel
from ..models.correspondence import CorrespondenceModel
from ..models.evidence import CorrespondenceEvidenceModel, RegistrationExperimentModel
from ..schemas.graph import ReactFlowNode, ReactFlowEdge, ReactFlowGraphResponse


class GraphService:
    """Builds and queries the multi-modal Lunar Entity Knowledge Graph."""

    def __init__(self, db: Session):
        self.db = db

    def build_full_graph(self) -> nx.DiGraph:
        """Constructs NetworkX DiGraph from database entities, observations, and evidence."""
        G = nx.DiGraph()

        # 1. Add Entity Nodes
        entities = self.db.query(LunarEntityModel).all()
        for e in entities:
            G.add_node(
                e.entity_id,
                node_type="LunarEntity",
                label=f"{e.entity_id} ({e.entity_type.upper()})",
                confidence=e.confidence,
                uncertainty=e.uncertainty,
                lat=e.latitude,
                lon=e.longitude,
            )

        # 2. Add Observation & Sensor Nodes
        observations = self.db.query(ObservationModel).all()
        sensors_added = set()

        for obs in observations:
            # Observation Node
            G.add_node(
                obs.id,
                node_type="Observation",
                label=f"{obs.sensor_type} ({obs.id})",
                sensor=obs.sensor_type,
                resolution=obs.spatial_resolution_m,
                is_synthetic=obs.is_synthetic,
            )

            # Sensor Node
            if obs.sensor_type not in sensors_added:
                sensor_node_id = f"SENSOR-{obs.sensor_type}"
                G.add_node(
                    sensor_node_id,
                    node_type="Sensor",
                    label=f"PAYLOAD: {obs.sensor_type}",
                    sensor=obs.sensor_type,
                )
                sensors_added.add(obs.sensor_type)

            G.add_edge(obs.id, f"SENSOR-{obs.sensor_type}", relation="ACQUIRED_BY")

        # 3. Add Entity-to-Observation Edges
        rels = self.db.query(EntityObservationModel).all()
        for r in rels:
            G.add_edge(r.entity_id, r.observation_id, relation="OBSERVED_BY", confidence=r.confidence)

        # 4. Add Correspondence & Registration Edges
        corrs = self.db.query(CorrespondenceModel).all()
        for c in corrs:
            G.add_edge(
                c.source_observation_id,
                c.target_observation_id,
                relation="MATCHED_WITH",
                status=c.status,
                confidence=c.overall_confidence,
            )

            # Check evidence node
            ev = self.db.query(CorrespondenceEvidenceModel).filter(
                CorrespondenceEvidenceModel.correspondence_id == c.id
            ).first()
            if ev:
                ev_node_id = f"EV-{c.id}"
                G.add_node(
                    ev_node_id,
                    node_type="PhysicsEvidence",
                    label=f"Physics Verification ({c.status})",
                    confidence=ev.visual_score,
                    uncertainty=ev.total_uncertainty,
                )
                G.add_edge(c.source_observation_id, ev_node_id, relation="EVALUATED_BY")
                G.add_edge(ev_node_id, c.target_observation_id, relation="VERIFIES")

        # 5. Add Hypothesis Nodes
        hypotheses = self.db.query(WorldModelHypothesisModel).all()
        for h in hypotheses:
            hyp_node_id = f"HYP-{h.id}"
            G.add_node(
                hyp_node_id,
                node_type="Hypothesis",
                label=f"{h.property_name.replace('_', ' ').title()}",
                value=h.hypothesis_value,
                confidence=h.confidence,
                uncertainty=h.uncertainty,
            )
            G.add_edge(h.entity_id, hyp_node_id, relation="BELIEVES", confidence=h.confidence)

        return G

    def get_react_flow_graph(self, filter_entity_id: Optional[str] = None) -> ReactFlowGraphResponse:
        """Converts graph to React Flow format with automated layered coordinate layout."""
        G = self.build_full_graph()

        nodes: List[ReactFlowNode] = []
        edges: List[ReactFlowEdge] = []

        total_entities = 0
        total_obs = 0
        total_ev = 0

        # Layered coordinate placement
        col_x = {
            "LunarEntity": 80.0,
            "Observation": 360.0,
            "Sensor": 640.0,
            "PhysicsEvidence": 480.0,
            "Hypothesis": 80.0,
        }

        row_y = {
            "LunarEntity": 80.0,
            "Observation": 60.0,
            "Sensor": 60.0,
            "PhysicsEvidence": 220.0,
            "Hypothesis": 320.0,
        }

        for node_id, data in G.nodes(data=True):
            ntype = data.get("node_type", "Observation")
            if ntype == "LunarEntity":
                total_entities += 1
            elif ntype == "Observation":
                total_obs += 1
            else:
                total_ev += 1

            pos_x = col_x.get(ntype, 200.0)
            pos_y = row_y.get(ntype, 100.0)
            row_y[ntype] = pos_y + 110.0

            nodes.append(
                ReactFlowNode(
                    id=node_id,
                    type=ntype,
                    position={"x": pos_x, "y": pos_y},
                    data={
                        "label": data.get("label", node_id),
                        "node_type": ntype,
                        "confidence": data.get("confidence", 0.9),
                        "uncertainty": data.get("uncertainty", 0.1),
                        "details": data,
                    },
                )
            )

        edge_counter = 0
        for u, v, data in G.edges(data=True):
            edge_counter += 1
            rel = data.get("relation", "CONNECTED_TO")
            status = data.get("status", "VERIFIED")

            stroke_color = "#3b82f6"
            if status == "VERIFIED":
                stroke_color = "#10b981"
            elif status == "REJECTED":
                stroke_color = "#ef4444"
            elif status == "UNCERTAIN":
                stroke_color = "#f59e0b"

            edges.append(
                ReactFlowEdge(
                    id=f"e-{u}-{v}-{edge_counter}",
                    source=u,
                    target=v,
                    label=rel,
                    animated=(status == "VERIFIED"),
                    style={"stroke": stroke_color, "strokeWidth": 2},
                )
            )

        return ReactFlowGraphResponse(
            nodes=nodes,
            edges=edges,
            total_entities=total_entities,
            total_observations=total_obs,
            total_evidence_nodes=total_ev,
        )
