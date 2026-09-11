"""Next-Best Observation (NBO) Recommendation Service.
Calculates Expected Information Gain across payload sensors to optimize lunar observation targeting.
"""

import json
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session

from ..models.lunar_entity import LunarEntityModel, EntityObservationModel
from ..models.recommendation import RecommendationModel


class RecommendationService:
    """Calculates quantitative Expected Information Gain and ranks sensor recommendations."""

    def __init__(self, db: Session):
        self.db = db

        # Sensor relevance matrix relative to scientific inquiry targets
        self.relevance_matrix = {
            "fine morphology": {"OHRC": 0.96, "TMC-2": 0.52, "IIRS": 0.18},
            "terrain analysis": {"OHRC": 0.58, "TMC-2": 0.94, "IIRS": 0.32},
            "elevation analysis": {"OHRC": 0.42, "TMC-2": 0.98, "IIRS": 0.20},
            "spectral analysis": {"OHRC": 0.15, "TMC-2": 0.25, "IIRS": 0.97},
            "boulder hazard": {"OHRC": 0.98, "TMC-2": 0.60, "IIRS": 0.10},
            "water ice prospecting": {"OHRC": 0.35, "TMC-2": 0.40, "IIRS": 0.95},
        }

        # Sensor base physical measurement quality & operational feasibility
        self.sensor_specs = {
            "OHRC": {"quality": 0.94, "feasibility": 0.88, "band": "Optical High-Res (0.25m)", "role": "Sub-meter structural morphology"},
            "TMC-2": {"quality": 0.90, "feasibility": 0.92, "band": "Stereo Photogrammetry (5m)", "role": "Topographic 3D DEM & slope mapping"},
            "IIRS": {"quality": 0.88, "feasibility": 0.85, "band": "Hyperspectral SWIR (20m)", "role": "Mineral composition & 2.8μm OH/H2O absorption"},
        }

    def recommend_next_observation(
        self, entity_id: str, scientific_question: str = "spectral analysis"
    ) -> RecommendationModel:
        """Computes ranked recommendations using Expected Information Gain formula."""
        entity = self.db.query(LunarEntityModel).filter(LunarEntityModel.entity_id == entity_id).first()
        if not entity:
            raise ValueError(f"Entity not found: {entity_id}")

        # Current observations attached to entity
        obs_rels = self.db.query(EntityObservationModel).filter(
            EntityObservationModel.entity_id == entity_id
        ).all()
        observed_sensors = {r.sensor_type for r in obs_rels}

        target_q = scientific_question.lower()
        rel_map = self.relevance_matrix.get(target_q, {"OHRC": 0.60, "TMC-2": 0.60, "IIRS": 0.60})

        ranked: List[Dict[str, Any]] = []

        for sensor, spec in self.sensor_specs.items():
            relevance = rel_map.get(sensor, 0.5)
            # If sensor has never observed this entity, missing_info_factor is 1.0; else 0.45
            missing_factor = 1.0 if sensor not in observed_sensors else 0.45
            current_unc = max(entity.uncertainty, 0.25)
            quality = spec["quality"]
            feasibility = spec["feasibility"]

            # Expected Information Gain Calculation:
            # InfoGain = Uncertainty * Relevance * MissingFactor * Quality * Feasibility
            info_gain = float(current_unc * relevance * missing_factor * quality * feasibility)
            info_gain = round(float(info_gain), 4)

            unc_reduction = round(float(info_gain * 0.42), 3)

            explanation = (
                f"High priority: Entity lacks {spec['band']} data. "
                f"Expected to reduce {target_q} epistemic uncertainty by {unc_reduction*100:.1f}%."
                if sensor not in observed_sensors
                else f"Secondary priority: Repeated observation at orthogonal solar azimuth will refine existing measurements."
            )

            ranked.append({
                "sensor": sensor,
                "expected_information_gain": info_gain,
                "uncertainty_reduction": unc_reduction,
                "relevance_score": relevance,
                "feasibility": feasibility,
                "description": spec["role"],
                "explanation": explanation,
                "is_new_modality": (sensor not in observed_sensors),
            })

        # Sort by expected information gain descending
        ranked.sort(key=lambda x: x["expected_information_gain"], reverse=True)
        top = ranked[0]

        rec_id = f"REC-{entity_id[-5:]}-{top['sensor']}"
        existing = self.db.query(RecommendationModel).filter(RecommendationModel.id == rec_id).first()
        if existing:
            existing.scientific_question = scientific_question
            existing.recommended_sensor = top["sensor"]
            existing.expected_information_gain = top["expected_information_gain"]
            existing.uncertainty_reduction = top["uncertainty_reduction"]
            existing.feasibility = top["feasibility"]
            existing.explanation = top["explanation"]
            rec = existing
        else:
            rec = RecommendationModel(
                id=rec_id,
                entity_id=entity_id,
                scientific_question=scientific_question,
                recommended_sensor=top["sensor"],
                expected_information_gain=top["expected_information_gain"],
                uncertainty_reduction=top["uncertainty_reduction"],
                feasibility=top["feasibility"],
                explanation=top["explanation"],
            )
            self.db.add(rec)

        self.db.commit()
        self.db.refresh(rec)

        # Attach ranked list into python attribute for API response
        setattr(rec, "ranked_sensors", ranked)
        return rec
