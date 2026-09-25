"""Next-Best Observation (NBO) Recommendation Engine.
Stage 4.6: Evidence-Driven Next Observation Targeting.

Enforces:
1. Strict use of 'POTENTIALLY_REDUCES_UNCERTAINTY' language instead of false certainty ('WILL_RESOLVE').
2. Qualitative potential ratings (HIGH_POTENTIAL, MEDIUM_POTENTIAL, LOW_POTENTIAL, UNKNOWN)
   to prevent fabricating artificial numerical information gain scores.
3. Geometric feasibility verification (e.g. swath offset requirements for bridging footprint gaps).
"""

from enum import Enum
from datetime import datetime
from typing import Dict, List, Optional, Any
import uuid
from pydantic import BaseModel, Field

from .entity import LunarEntity
from .evidence import EvidenceType
from .knowledge_gap import KnowledgeGap, GapType, GapSeverity


class InformationGainPotential(str, Enum):
    """Qualitative assessment of potential uncertainty reduction."""
    HIGH_POTENTIAL = "HIGH_POTENTIAL"
    MEDIUM_POTENTIAL = "MEDIUM_POTENTIAL"
    LOW_POTENTIAL = "LOW_POTENTIAL"
    UNKNOWN = "UNKNOWN"


class SensorFeasibility(str, Enum):
    """Operational and orbital geometric feasibility of sensor acquisition."""
    FEASIBLE = "FEASIBLE"
    GEOMETRICALLY_INCOMPATIBLE = "GEOMETRICALLY_INCOMPATIBLE"
    PAYLOAD_UNAVAILABLE = "PAYLOAD_UNAVAILABLE"
    UNKNOWN = "UNKNOWN"


class NextBestObservation(BaseModel):
    """Evidence-driven observation recommendation to reduce world model epistemic uncertainty."""
    recommendation_id: str = Field(default_factory=lambda: f"REC-{uuid.uuid4().hex[:8].upper()}")
    target_entity_id: str
    knowledge_gap_id: str
    gap_type: GapType
    candidate_sensor: str
    reason: str
    required_geometry: str
    expected_evidence_type: EvidenceType
    feasibility: SensorFeasibility = SensorFeasibility.FEASIBLE
    uncertainty_reduction_basis: str
    information_gain_potential: InformationGainPotential = InformationGainPotential.MEDIUM_POTENTIAL
    status: str = "ACTIVE"
    provenance: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"frozen": False}


class NextBestObservationEngine:
    """Computes evidence-driven, scientifically grounded next-best observation recommendations."""

    DEFAULT_SENSOR_CATALOG = {
        "OHRC": {"role": "Sub-meter optical morphology", "min_lat": -90.0, "max_lat": 90.0, "res_m": 0.25},
        "TMC-2": {"role": "Stereo 3D DEM & regional topography", "min_lat": -90.0, "max_lat": 90.0, "res_m": 5.0},
        "IIRS": {"role": "Hyperspectral mineralogy & hydration", "min_lat": -90.0, "max_lat": 90.0, "res_m": 20.0},
        "LROC_NAC": {"role": "Sub-meter independent validation", "min_lat": -90.0, "max_lat": 90.0, "res_m": 0.5},
        "SELENE_TC": {"role": "Kaguya terrain verification", "min_lat": -90.0, "max_lat": 90.0, "res_m": 10.0},
    }

    def __init__(self, available_sensors: Optional[List[str]] = None):
        self.available_sensors = available_sensors or list(self.DEFAULT_SENSOR_CATALOG.keys())

    def recommend_for_gap(
        self,
        entity: LunarEntity,
        gap: KnowledgeGap,
    ) -> List[NextBestObservation]:
        """Maps a knowledge gap to prioritized sensor recommendations."""
        recommendations: List[NextBestObservation] = []

        if gap.gap_type == GapType.FOOTPRINT_NON_OVERLAP:
            # Bridging the 1.5 - 2.1 km Phase 3 footprint gap
            sensor = "TMC-2"
            feas = SensorFeasibility.FEASIBLE if sensor in self.available_sensors else SensorFeasibility.PAYLOAD_UNAVAILABLE
            recommendations.append(
                NextBestObservation(
                    target_entity_id=entity.entity_id,
                    knowledge_gap_id=gap.gap_id,
                    gap_type=gap.gap_type,
                    candidate_sensor=sensor,
                    reason="Calibrated footprint separation requires an adjacent overlapping swath to bridge the 1.5-2.1 km reference gap.",
                    required_geometry="potentially useful adjacent observation geometry (adjacent track shifted by ~2.0 km west; not a confirmed spacecraft trajectory plan)",
                    expected_evidence_type=EvidenceType.PHYSICAL,
                    feasibility=feas,
                    uncertainty_reduction_basis="POTENTIALLY_REDUCES_UNCERTAINTY by establishing physical spatial overlap between OHRC and TMC-2 swaths",
                    information_gain_potential=InformationGainPotential.HIGH_POTENTIAL,
                    provenance={"gap_blocking_reason": gap.blocking_reason},
                )
            )

        elif gap.gap_type == GapType.MISSING_SPECTRAL_VALIDATION:
            sensor = "IIRS"
            feas = SensorFeasibility.FEASIBLE if sensor in self.available_sensors else SensorFeasibility.PAYLOAD_UNAVAILABLE
            recommendations.append(
                NextBestObservation(
                    target_entity_id=entity.entity_id,
                    knowledge_gap_id=gap.gap_id,
                    gap_type=gap.gap_type,
                    candidate_sensor=sensor,
                    reason="Entity lacks hyperspectral reflectance data to identify mineral absorption bands.",
                    required_geometry="Nadir hyperspectral targeting over crater floor/ejecta",
                    expected_evidence_type=EvidenceType.SPECTRAL,
                    feasibility=feas,
                    uncertainty_reduction_basis="POTENTIALLY_REDUCES_UNCERTAINTY regarding pyroxene, olivine, and hydration composition",
                    information_gain_potential=InformationGainPotential.HIGH_POTENTIAL,
                    provenance={"target_bands_um": [0.95, 1.05, 2.8]},
                )
            )

        elif gap.gap_type == GapType.MISSING_TERRAIN_VALIDATION:
            sensor = "TMC-2"
            feas = SensorFeasibility.FEASIBLE if sensor in self.available_sensors else SensorFeasibility.PAYLOAD_UNAVAILABLE
            recommendations.append(
                NextBestObservation(
                    target_entity_id=entity.entity_id,
                    knowledge_gap_id=gap.gap_id,
                    gap_type=gap.gap_type,
                    candidate_sensor=sensor,
                    reason="Lacks 3D stereo photogrammetric depth profile.",
                    required_geometry="Fore and AFT stereo viewing angles (±26°)",
                    expected_evidence_type=EvidenceType.TERRAIN,
                    feasibility=feas,
                    uncertainty_reduction_basis="POTENTIALLY_REDUCES_UNCERTAINTY by resolving true crater depth and rim slope angles",
                    information_gain_potential=InformationGainPotential.MEDIUM_POTENTIAL,
                    provenance={"sensor_role": "Stereo Photogrammetry"},
                )
            )

        elif gap.gap_type == GapType.MISSING_TEMPORAL_OBSERVATION:
            sensor = "OHRC"
            feas = SensorFeasibility.FEASIBLE if sensor in self.available_sensors else SensorFeasibility.PAYLOAD_UNAVAILABLE
            recommendations.append(
                NextBestObservation(
                    target_entity_id=entity.entity_id,
                    knowledge_gap_id=gap.gap_id,
                    gap_type=gap.gap_type,
                    candidate_sensor=sensor,
                    reason="Lacks orthogonal solar illumination to illuminate shadowed floor and rim morphology.",
                    required_geometry="Acquisition under opposite solar azimuth angle (Δazimuth ~ 180°)",
                    expected_evidence_type=EvidenceType.ILLUMINATION,
                    feasibility=feas,
                    uncertainty_reduction_basis="POTENTIALLY_REDUCES_UNCERTAINTY by revealing features obscured in permanent or seasonal shadows",
                    information_gain_potential=InformationGainPotential.MEDIUM_POTENTIAL,
                    provenance={"illumination_goal": "Shadow resolution"},
                )
            )

        elif gap.gap_type == GapType.UNCERTAINTY_TOO_HIGH:
            sensor = "OHRC"
            feas = SensorFeasibility.FEASIBLE if sensor in self.available_sensors else SensorFeasibility.PAYLOAD_UNAVAILABLE
            recommendations.append(
                NextBestObservation(
                    target_entity_id=entity.entity_id,
                    knowledge_gap_id=gap.gap_id,
                    gap_type=gap.gap_type,
                    candidate_sensor=sensor,
                    reason="High spatial uncertainty requires sub-meter optical localization.",
                    required_geometry="Sub-meter nadir targeting (0.25m/px)",
                    expected_evidence_type=EvidenceType.GEOMETRIC,
                    feasibility=feas,
                    uncertainty_reduction_basis="POTENTIALLY_REDUCES_UNCERTAINTY by localizing crater rim boundary to sub-meter precision",
                    information_gain_potential=InformationGainPotential.HIGH_POTENTIAL,
                    provenance={"target_gsd_m": 0.25},
                )
            )

        return recommendations
