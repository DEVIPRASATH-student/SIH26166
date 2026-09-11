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

    def save_image_to_disk(self, obs_id: str, image_data: np.ndarray) -> str:
        """Saves image data as PNG to storage directory."""
        filename = f"{obs_id}.png"
        file_path = settings.IMAGES_DIR / filename

        # Ensure correct BGR conversion for OpenCV saving
        if image_data.ndim == 3 and image_data.shape[2] == 3:
            bgr = cv2.cvtColor(image_data, cv2.COLOR_RGB2BGR)
            cv2.imwrite(str(file_path), bgr)
        else:
            cv2.imwrite(str(file_path), image_data)

        return f"/api/observations/{obs_id}/image"

    def load_image_from_disk(self, obs_id: str) -> Optional[np.ndarray]:
        """Loads image data from disk as RGB or Grayscale."""
        file_path = settings.IMAGES_DIR / f"{obs_id}.png"
        if not file_path.exists():
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

    def get_observation(self, obs_id: str) -> Optional[ObservationModel]:
        return self.db.query(ObservationModel).filter(ObservationModel.id == obs_id).first()

    def list_observations(self) -> List[ObservationModel]:
        return self.db.query(ObservationModel).all()
