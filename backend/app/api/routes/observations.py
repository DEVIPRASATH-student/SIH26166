"""Observation API Endpoints."""

import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from ...database.session import get_db
from ...core.config import settings
from ...services.observation_service import ObservationService
from ...schemas.observation import ObservationResponse, ObservationSummary
from ...models.observation import ObservationModel

router = APIRouter(prefix="/observations", tags=["Observations"])


@router.get("", response_model=List[ObservationResponse])
def get_all_observations(db: Session = Depends(get_db)):
    """Retrieves all registered multi-modal lunar observations."""
    obs_service = ObservationService(db)
    observations = obs_service.list_observations()
    result = []
    for obs in observations:
        result.append(
            ObservationResponse(
                id=obs.id,
                sensor_type=obs.sensor_type,
                image_url=obs.image_path,
                acquisition_timestamp=obs.acquisition_timestamp,
                lat_min=obs.lat_min,
                lat_max=obs.lat_max,
                lon_min=obs.lon_min,
                lon_max=obs.lon_max,
                spatial_resolution_m=obs.spatial_resolution_m,
                sun_azimuth_deg=obs.sun_azimuth_deg,
                sun_elevation_deg=obs.sun_elevation_deg,
                incidence_angle_deg=obs.incidence_angle_deg,
                emission_angle_deg=obs.emission_angle_deg,
                phase_angle_deg=obs.phase_angle_deg,
                metadata=json.loads(obs.metadata_json) if obs.metadata_json else {},
                preprocessing_history=json.loads(obs.preprocessing_history) if obs.preprocessing_history else [],
                is_synthetic=obs.is_synthetic,
            )
        )
    return result


@router.get("/{observation_id}", response_model=ObservationResponse)
def get_observation_by_id(observation_id: str, db: Session = Depends(get_db)):
    """Retrieves metadata for a specific observation."""
    obs_service = ObservationService(db)
    obs = obs_service.get_observation(observation_id)
    if not obs:
        raise HTTPException(status_code=404, detail=f"Observation {observation_id} not found")

    return ObservationResponse(
        id=obs.id,
        sensor_type=obs.sensor_type,
        image_url=obs.image_path,
        acquisition_timestamp=obs.acquisition_timestamp,
        lat_min=obs.lat_min,
        lat_max=obs.lat_max,
        lon_min=obs.lon_min,
        lon_max=obs.lon_max,
        spatial_resolution_m=obs.spatial_resolution_m,
        sun_azimuth_deg=obs.sun_azimuth_deg,
        sun_elevation_deg=obs.sun_elevation_deg,
        incidence_angle_deg=obs.incidence_angle_deg,
        emission_angle_deg=obs.emission_angle_deg,
        phase_angle_deg=obs.phase_angle_deg,
        metadata=json.loads(obs.metadata_json) if obs.metadata_json else {},
        preprocessing_history=json.loads(obs.preprocessing_history) if obs.preprocessing_history else [],
        is_synthetic=obs.is_synthetic,
    )


@router.get("/{observation_id}/image")
def get_observation_image(observation_id: str):
    """Serves the raw PNG image of an observation."""
    file_path = settings.IMAGES_DIR / f"{observation_id}.png"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Image for {observation_id} not found on disk")
    return FileResponse(path=str(file_path), media_type="image/png")


@router.get("/experiments/{filename}")
def get_experiment_image(filename: str):
    """Serves registered or difference overlay artifact images."""
    file_path = settings.IMAGES_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Experiment image {filename} not found")
    return FileResponse(path=str(file_path), media_type="image/png")
