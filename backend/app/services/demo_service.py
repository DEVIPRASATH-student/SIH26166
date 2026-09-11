"""Automated Demo Mission Pipeline Service.
Executes the full end-to-end multi-modal lifecycle in a single deterministic, reproducible workflow.
"""

import time
from typing import Dict, Any
from sqlalchemy.orm import Session

from ..models.observation import ObservationModel
from ..models.lunar_entity import LunarEntityModel
from ..services.observation_service import ObservationService
from ..services.correspondence_service import CorrespondenceService
from ..services.registration_service import RegistrationService
from ..services.entity_service import EntityService
from ..services.knowledge_gap_service import KnowledgeGapService
from ..services.recommendation_service import RecommendationService
from outgraph.ml.synthetic_data.terrain_generator import SyntheticTerrainGenerator
from outgraph.ml.synthetic_data.sensor_simulator import SensorSimulator


class DemoService:
    """Executes the complete LunarSynapse end-to-end scientific workflow."""

    def __init__(self, db: Session):
        self.db = db
        self.obs_service = ObservationService(db)
        self.corr_service = CorrespondenceService(db)
        self.reg_service = RegistrationService(db)
        self.entity_service = EntityService(db)
        self.gap_service = KnowledgeGapService(db)
        self.rec_service = RecommendationService(db)

    def run_complete_demo_mission(self) -> Dict[str, Any]:
        """Executes full automated mission pipeline."""
        start_time = time.time()

        # Step 1: Generate Procedural Lunar Landscape & DEM
        terrain_gen = SyntheticTerrainGenerator(base_resolution=512, seed=42)
        landscape = terrain_gen.generate_landscape(lat_center=-70.5, lon_center=22.8)

        # Step 2: Simulate Multi-Modal Observations (OHRC, TMC-2, IIRS)
        sensor_sim = SensorSimulator(seed=42)

        ohrc_obs = sensor_sim.simulate_ohrc(
            landscape,
            observation_id="OBS-OHRC-001",
            sun_azimuth_deg=45.0,
            sun_elevation_deg=35.0,
            target_size=420,
        )

        tmc2_obs = sensor_sim.simulate_tmc2(
            landscape,
            observation_id="OBS-TMC2-001",
            sun_azimuth_deg=65.0,
            sun_elevation_deg=30.0,
            target_size=420,
        )

        iirs_obs = sensor_sim.simulate_iirs(
            landscape,
            observation_id="OBS-IIRS-001",
            sun_azimuth_deg=85.0,
            sun_elevation_deg=40.0,
            target_size=420,
        )

        # Step 3: Persist Observations to DB & Storage
        db_ohrc = self.obs_service.create_observation(
            obs_id=ohrc_obs.observation_id,
            sensor_type=ohrc_obs.sensor_type,
            image_data=ohrc_obs.image_data,
            spatial_resolution_m=ohrc_obs.spatial_resolution_m,
            sun_azimuth_deg=ohrc_obs.sun_azimuth_deg,
            sun_elevation_deg=ohrc_obs.sun_elevation_deg,
            incidence_angle_deg=ohrc_obs.incidence_angle_deg,
            emission_angle_deg=ohrc_obs.emission_angle_deg,
            phase_angle_deg=ohrc_obs.phase_angle_deg,
            lat_min=ohrc_obs.lat_min,
            lat_max=ohrc_obs.lat_max,
            lon_min=ohrc_obs.lon_min,
            lon_max=ohrc_obs.lon_max,
            metadata=ohrc_obs.metadata,
        )

        db_tmc2 = self.obs_service.create_observation(
            obs_id=tmc2_obs.observation_id,
            sensor_type=tmc2_obs.sensor_type,
            image_data=tmc2_obs.image_data,
            spatial_resolution_m=tmc2_obs.spatial_resolution_m,
            sun_azimuth_deg=tmc2_obs.sun_azimuth_deg,
            sun_elevation_deg=tmc2_obs.sun_elevation_deg,
            incidence_angle_deg=tmc2_obs.incidence_angle_deg,
            emission_angle_deg=tmc2_obs.emission_angle_deg,
            phase_angle_deg=tmc2_obs.phase_angle_deg,
            lat_min=tmc2_obs.lat_min,
            lat_max=tmc2_obs.lat_max,
            lon_min=tmc2_obs.lon_min,
            lon_max=tmc2_obs.lon_max,
            metadata=tmc2_obs.metadata,
        )

        db_iirs = self.obs_service.create_observation(
            obs_id=iirs_obs.observation_id,
            sensor_type=iirs_obs.sensor_type,
            image_data=iirs_obs.image_data,
            spatial_resolution_m=iirs_obs.spatial_resolution_m,
            sun_azimuth_deg=iirs_obs.sun_azimuth_deg,
            sun_elevation_deg=iirs_obs.sun_elevation_deg,
            incidence_angle_deg=iirs_obs.incidence_angle_deg,
            emission_angle_deg=iirs_obs.emission_angle_deg,
            phase_angle_deg=iirs_obs.phase_angle_deg,
            lat_min=iirs_obs.lat_min,
            lat_max=iirs_obs.lat_max,
            lon_min=iirs_obs.lon_min,
            lon_max=iirs_obs.lon_max,
            metadata=iirs_obs.metadata,
        )

        # Step 4: Perform Cross-Modal Matching & Physics Verification
        corr1, ev1, match_res1 = self.corr_service.analyze_correspondence(
            src_obs_id="OBS-OHRC-001",
            tgt_obs_id="OBS-TMC2-001",
            matcher_name="SIFT",
        )

        corr2, ev2, match_res2 = self.corr_service.analyze_correspondence(
            src_obs_id="OBS-OHRC-001",
            tgt_obs_id="OBS-IIRS-001",
            matcher_name="SIFT",
        )

        # Step 5: Execute Sub-Pixel Registration & Overlays
        reg_exp1 = self.reg_service.run_registration(
            correspondence_id=corr1.id,
            src_img=ohrc_obs.image_data,
            tgt_img=tmc2_obs.image_data,
            match_result=match_res1,
            apply_subpixel_ecc=True,
        )

        # Step 6: Resolve Persistent Lunar Entities
        entity1 = self.entity_service.resolve_entity(
            lat=-70.52,
            lon=22.84,
            entity_type="crater",
            spatial_extent_m=180.0,
            observation_id="OBS-OHRC-001",
            correspondence_id=corr1.id,
            sensor_type="OHRC",
            confidence=corr1.overall_confidence,
        )

        # Attach second observation to same entity
        self.entity_service._attach_observation(
            entity_id=entity1.entity_id,
            observation_id="OBS-TMC2-001",
            correspondence_id=corr1.id,
            sensor_type="TMC-2",
            confidence=0.88,
        )

        # Create secondary entity for boulder cluster
        entity2 = self.entity_service.resolve_entity(
            lat=-70.48,
            lon=22.92,
            entity_type="boulder",
            spatial_extent_m=35.0,
            observation_id="OBS-OHRC-001",
            sensor_type="OHRC",
            confidence=0.94,
        )

        # Step 7: Scan & Prioritize Knowledge Gaps
        gaps = self.gap_service.scan_knowledge_gaps()

        # Step 8: Calculate Next-Best Observation Recommendation
        rec = self.rec_service.recommend_next_observation(
            entity_id=entity1.entity_id,
            scientific_question="spectral analysis",
        )

        elapsed = round(time.time() - start_time, 2)

        return {
            "status": "SUCCESS",
            "message": "Complete LunarSynapse Mission Pipeline executed successfully.",
            "execution_time_seconds": elapsed,
            "observations_created": 3,
            "correspondences_analyzed": 2,
            "entities_resolved": 2,
            "knowledge_gaps_found": len(gaps),
            "top_recommendation": {
                "entity_id": rec.entity_id,
                "recommended_sensor": rec.recommended_sensor,
                "expected_information_gain": rec.expected_information_gain,
                "explanation": rec.explanation,
            },
        }
