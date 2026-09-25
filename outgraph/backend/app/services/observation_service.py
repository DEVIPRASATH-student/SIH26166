"""Observation Service for Managing Lunar Remote Sensing Payloads."""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from sqlalchemy.orm import Session
import cv2
import numpy as np

from ..core.config import settings
from ..models.observation import ObservationModel
from ..schemas.observation import ObservationResponse


class ObservationService:
    """Handles storage, retrieval, and disk persistence of multi-modal observations."""

    def __init__(self, db: Session):
        self.db = db

    def _sanitize_filename(self, obs_id: str) -> str:
        safe_id = obs_id.replace(":", "_").replace("/", "_").replace("\\", "_")
        return f"{safe_id}.png"

    def save_image_to_disk(self, obs_id: str, image_data: np.ndarray) -> str:
        """Saves image data as PNG to storage directory."""
        filename = self._sanitize_filename(obs_id)
        file_path = settings.IMAGES_DIR / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Ensure correct BGR conversion for OpenCV saving
        if image_data.ndim == 3 and image_data.shape[2] == 3:
            bgr = cv2.cvtColor(image_data, cv2.COLOR_RGB2BGR)
            cv2.imwrite(str(file_path), bgr)
        else:
            cv2.imwrite(str(file_path), image_data)

        return f"/api/observations/{obs_id}/image"

    def load_image_from_disk(self, obs_id: str) -> Optional[np.ndarray]:
        """Loads image data from disk as RGB or Grayscale."""
        filename = self._sanitize_filename(obs_id)
        file_path = settings.IMAGES_DIR / filename
        if not file_path.exists():
            # Check if this is a real product with a browse or raw image
            obs = self.get_observation(obs_id)
            if obs and obs.raw_path:
                raw_p = Path(obs.raw_path)
                # Look for browse png in product directory
                cand_pngs = []
                curr = raw_p.parent
                for _ in range(5):
                    cand_pngs.extend(list(curr.glob("browse/**/*.png")))
                    cand_pngs.extend(list(curr.glob("*.png")))
                    if cand_pngs:
                        break
                    curr = curr.parent
                if cand_pngs:
                    img = cv2.imread(str(cand_pngs[0]), cv2.IMREAD_UNCHANGED)
                    if img is not None:
                        # Cache it in IMAGES_DIR
                        self.save_image_to_disk(obs_id, img)
                        if img.ndim == 3 and img.shape[2] == 3:
                            return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                        return img
            return None
        img = cv2.imread(str(file_path), cv2.IMREAD_UNCHANGED)
        if img is not None and img.ndim == 3 and img.shape[2] == 3:
            return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        return img

    def create_observation(
        self,
        obs_id: str,
        sensor_type: str,
        image_data: np.ndarray,
        spatial_resolution_m: float,
        sun_azimuth_deg: float,
        sun_elevation_deg: float,
        incidence_angle_deg: float,
        emission_angle_deg: float,
        phase_angle_deg: float,
        lat_min: float,
        lat_max: float,
        lon_min: float,
        lon_max: float,
        metadata: Dict[str, Any],
        is_synthetic: bool = True,
    ) -> ObservationModel:
        """Stores metadata in DB and image on disk."""
        img_url = self.save_image_to_disk(obs_id, image_data)

        # Check existing
        existing = self.db.query(ObservationModel).filter(ObservationModel.id == obs_id).first()
        if existing:
            return existing

        obs = ObservationModel(
            id=obs_id,
            sensor_type=sensor_type,
            image_path=img_url,
            spatial_resolution_m=spatial_resolution_m,
            sun_azimuth_deg=sun_azimuth_deg,
            sun_elevation_deg=sun_elevation_deg,
            incidence_angle_deg=incidence_angle_deg,
            emission_angle_deg=emission_angle_deg,
            phase_angle_deg=phase_angle_deg,
            lat_min=lat_min,
            lat_max=lat_max,
            lon_min=lon_min,
            lon_max=lon_max,
            metadata_json=json.dumps(metadata),
            preprocessing_history=json.dumps(["Sensor Calibrated", "Photometric Normalized"]),
            is_synthetic=is_synthetic,
        )
        self.db.add(obs)
        self.db.commit()
        self.db.refresh(obs)
        return obs

    def ingest_real_product(
        self,
        file_path: str,
        source: Optional[str] = None,
    ) -> ObservationModel:
        """Ingests a real scientific lunar product (OHRC, TMC-2, IIRS, LROC, SELENE)
        using the Phase 1 ingestion engine, persisting metadata and provenance to DB.
        """
        from outgraph.ml.data.ingestion.factory import ProductIngestionEngine
        from outgraph.ml.data.preprocessing.interface import SensorAwarePreprocessor

        engine = ProductIngestionEngine()
        lunar_prod = engine.ingest_product(file_path, source=source)

        meta = lunar_prod.metadata
        prov = lunar_prod.provenance

        # Prepare 2D visualization view for disk storage if raster is available
        img_url = f"/api/observations/{lunar_prod.product_id}/image"
        if lunar_prod.raster_data is not None:
            try:
                view_2d, _ = SensorAwarePreprocessor.extract_correspondence_ready_view(lunar_prod)
                img_url = self.save_image_to_disk(lunar_prod.product_id, view_2d)
            except Exception:
                pass

        # Geographic bounds strictly from metadata or 0.0 fallback
        gb = meta.geographic_bounds
        lat_min = gb.lat_min if gb.lat_min is not None else 0.0
        lat_max = gb.lat_max if gb.lat_max is not None else 0.0
        lon_min = gb.lon_min if gb.lon_min is not None else 0.0
        lon_max = gb.lon_max if gb.lon_max is not None else 0.0

        # Solar geometry strictly from metadata or 0.0 fallback
        si = meta.solar_illumination
        sun_az = si.sun_azimuth_deg if si.sun_azimuth_deg is not None else 0.0
        sun_el = si.sun_elevation_deg if si.sun_elevation_deg is not None else 0.0
        inc_ang = si.incidence_angle_deg if si.incidence_angle_deg is not None else 0.0
        em_ang = si.emission_angle_deg if si.emission_angle_deg is not None else 0.0
        phase_ang = si.phase_angle_deg if si.phase_angle_deg is not None else 0.0

        # GSD strictly from metadata or 0.0 fallback
        gsd = meta.gsd_m if meta.gsd_m is not None else 0.0

        sensor_type = meta.instrument or "GENERIC_LUNAR_SENSOR"

        # Check existing
        existing = self.db.query(ObservationModel).filter(ObservationModel.id == lunar_prod.product_id).first()
        if existing:
            return existing

        obs = ObservationModel(
            id=lunar_prod.product_id,
            sensor_type=sensor_type,
            image_path=img_url,
            raw_path=str(file_path),
            spatial_resolution_m=gsd,
            sun_azimuth_deg=sun_az,
            sun_elevation_deg=sun_el,
            incidence_angle_deg=inc_ang,
            emission_angle_deg=em_ang,
            phase_angle_deg=phase_ang,
            lat_min=lat_min,
            lat_max=lat_max,
            lon_min=lon_min,
            lon_max=lon_max,
            metadata_json=json.dumps(meta.raw_metadata),
            preprocessing_history=json.dumps([p.get("description", p.get("step")) for p in prov.processing_history]),
            is_synthetic=lunar_prod.is_synthetic,  # False for real products
            product_id=lunar_prod.product_id,
            mission=meta.mission,
            instrument=meta.instrument,
            product_type=meta.product_type,
            processing_level=meta.processing_level,
            num_bands=float(meta.num_bands),
            data_type=meta.data_type,
            nodata_value=meta.nodata_value,
            provenance_json=json.dumps(prov.dict(), default=str),
            metadata_source_json=json.dumps({k: v.value for k, v in meta.value_statuses.items()}),
        )

        self.db.add(obs)
        self.db.commit()
        self.db.refresh(obs)
        return obs

    def get_observation(self, obs_id: str) -> Optional[ObservationModel]:
        return self.db.query(ObservationModel).filter(ObservationModel.id == obs_id).first()

    def list_observations(self) -> List[ObservationModel]:
        return self.db.query(ObservationModel).all()

