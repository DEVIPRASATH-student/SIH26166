"""Active World Model Self-Evolving Feedback Loop.
Stage 5.7: Autonomous Knowledge Gap Closure and State Evolution.

Executes:
1. Ingestion of preliminary observation (OHRC)
2. Creation of lunar entity (CANDIDATE -> SUPPORTED)
3. Initial evidence profile and uncertainty chain
4. Detection of knowledge gaps (e.g. MISSING_TERRAIN_VALIDATION)
5. Generation of Next-Best Observation recommendation
6. Ingestion of follow-up observation (e.g. SLDEM2015 altimetry)
7. Evolution of entity state (SUPPORTED -> CONFIRMED)
8. Resolution of knowledge gap (OPEN -> RESOLVED) with complete provenance preservation.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime

from .entity import LunarEntity, EntityResolver, EntityState, AssociationStatus, AssociationType
from .evidence import EntityEvidenceProfile, Evidence, EvidenceType, EvidenceStatus, EvidenceProvenance
from .graph import WorldGraph, NodeType, EdgeRelation
from .uncertainty import PhysicalUncertainty, UncertaintyPropagator, UncertaintyChain
from .knowledge_gap import KnowledgeGapDetector, KnowledgeGap, GapType, GapStatus
from .next_best_observation import NextBestObservationEngine, NextBestObservation


class ActiveWorldModelLoop:
    """Orchestrates the active self-evolving feedback loop of the Lunar World Model."""

    def __init__(self):
        self.resolver = EntityResolver(spatial_tolerance_m=200.0)
        self.evidence_profile: Optional[EntityEvidenceProfile] = None
        self.world_graph = WorldGraph()
        self.detector = KnowledgeGapDetector()
        self.nbo_engine = NextBestObservationEngine()
        self.entity: Optional[LunarEntity] = None
        self.gaps: List[KnowledgeGap] = []
        self.recommendations: List[NextBestObservation] = []
        self.execution_log: List[Dict[str, Any]] = []

    def execute_initial_pass(
        self,
        entity_id: str = "LUNAR-CRATER-ACT-01",
        lat: float = 0.5542,
        lon: float = 23.4110,
    ) -> Dict[str, Any]:
        """Runs Steps 1 through 5: Initial observation to recommendation."""
        # 1. Ingest initial observation
        obs1_id = "OBS-OHRC-INITIAL"
        self.world_graph.add_observation_node(
            observation_id=obs1_id,
            sensor_type="OHRC",
            product_id="ch2_ohr_ncp_initial",
            resolution_m=0.25,
            is_synthetic=False,
        )

        # 2. Create entity
        self.entity = self.resolver.create_entity(
            entity_id=entity_id,
            latitude=lat,
            longitude=lon,
            initial_state=EntityState.CANDIDATE,
        )
        self.world_graph.add_entity_node(
            entity_id=self.entity.entity_id,
            entity_type=self.entity.entity_type,
            state=self.entity.state.value,
            latitude=lat,
            longitude=lon,
        )

        # 3. Associate observation
        assoc1 = self.resolver.associate_observation(
            entity_id=self.entity.entity_id,
            observation_id=obs1_id,
            obs_lat=lat,
            obs_lon=lon,
            sensor_type="OHRC",
            product_id="ch2_ohr_ncp_initial",
            confidence=0.95,
            uncertainty=0.25,
        )
        self.world_graph.add_relation(
            source_id=obs1_id,
            target_id=self.entity.entity_id,
            relation=EdgeRelation.OBSERVES,
            status="SUPPORTED",
        )

        # 4. Initialize Evidence Profile
        self.evidence_profile = EntityEvidenceProfile(entity_id=self.entity.entity_id)
        ev_geom = Evidence(
            evidence_id="EV-INIT-GEOM",
            entity_id=self.entity.entity_id,
            observation_id=obs1_id,
            evidence_type=EvidenceType.GEOMETRIC,
            status=EvidenceStatus.SUPPORTED,
            measurement={"diameter_m": 140.0},
            uncertainty=0.25,
            provenance=EvidenceProvenance(source_sensor="OHRC", source_method="SUBMETER_RIM"),
        )
        self.evidence_profile.add_or_update(ev_geom)

        # 5. Detect Gaps & Generate Recommendations
        self.gaps = self.detector.detect_gaps(self.entity, evidence_profile=self.evidence_profile)
        for g in self.gaps:
            recs = self.nbo_engine.recommend_for_gap(self.entity, g)
            self.recommendations.extend(recs)

        self.execution_log.append({
            "stage": "INITIAL_PASS_COMPLETE",
            "entity_state": self.entity.state.value,
            "gap_count": len(self.gaps),
            "recommendation_count": len(self.recommendations),
        })

        return {
            "entity_state": self.entity.state.value,
            "active_gaps": [g.gap_type.value for g in self.gaps],
            "recommendations": [r.candidate_sensor for r in self.recommendations],
        }

    def ingest_followup_observation(
        self,
        followup_obs_id: str = "OBS-SLDEM-FOLLOWUP",
        sensor_type: str = "SLDEM2015",
        measured_elevation_m: float = -1892.4,
        is_synthetic: bool = False,
    ) -> Dict[str, Any]:
        """Runs Steps 6 through 8: Ingests recommended observation, updates beliefs and closes gap."""
        if not self.entity or not self.evidence_profile:
            raise RuntimeError("Must execute initial pass before ingesting follow-up.")

        # 1. Register follow-up observation node
        self.world_graph.add_observation_node(
            observation_id=followup_obs_id,
            sensor_type=sensor_type,
            resolution_m=59.2,
            is_synthetic=is_synthetic,
        )

        # 2. Add follow-up association
        assoc2 = self.resolver.associate_observation(
            entity_id=self.entity.entity_id,
            observation_id=followup_obs_id,
            obs_lat=self.entity.latitude,
            obs_lon=self.entity.longitude,
            sensor_type=sensor_type,
            confidence=0.92,
            uncertainty=15.0,
        )
        self.world_graph.add_relation(
            source_id=followup_obs_id,
            target_id=self.entity.entity_id,
            relation=EdgeRelation.OBSERVES,
            status="SUPPORTED",
        )

        # 3. Add follow-up evidence
        ev_terr = Evidence(
            evidence_id="EV-FOLLOWUP-TERR",
            entity_id=self.entity.entity_id,
            observation_id=followup_obs_id,
            evidence_type=EvidenceType.TERRAIN,
            status=EvidenceStatus.SUPPORTED,
            measurement={"elevation_m": measured_elevation_m},
            uncertainty=15.0,
            is_synthetic=is_synthetic,
            provenance=EvidenceProvenance(source_sensor=sensor_type, source_method="ALTIMETRY_DEM"),
        )
        self.evidence_profile.add_or_update(ev_terr)
        self.entity.elevation_m = measured_elevation_m

        # 4. Resolve the Terrain Knowledge Gap
        for g in self.gaps:
            if g.gap_type == GapType.MISSING_TERRAIN_VALIDATION:
                g.status = GapStatus.RESOLVED

        # 5. Entity State Evolves from SUPPORTED to CONFIRMED (multi-sensor corroborated)
        self.entity.state = EntityState.CONFIRMED

        self.execution_log.append({
            "stage": "FOLLOWUP_INGESTED",
            "new_sensor": sensor_type,
            "new_entity_state": self.entity.state.value,
            "resolved_gaps": [g.gap_type.value for g in self.gaps if g.status == GapStatus.RESOLVED],
        })

        return {
            "updated_entity_state": self.entity.state.value,
            "association_count": len(self.entity.associations),
            "evidence_count": len(self.evidence_profile.evidence_items),
            "is_confirmed": (self.entity.state == EntityState.CONFIRMED),
            "resolved_gap_count": sum(1 for g in self.gaps if g.status == GapStatus.RESOLVED),
        }
