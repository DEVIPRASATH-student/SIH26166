"""Observation API Endpoints."""

import json
from pathlib import Path
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from ...database.session import get_db
from ...core.config import settings
from ...services.observation_service import ObservationService
from ...schemas.observation import ObservationCreate, ObservationResponse, ObservationSummary
from ...models.observation import ObservationModel

router = APIRouter(prefix="/observations", tags=["Observations"])


def _build_observation_response(obs: ObservationModel) -> ObservationResponse:
    prov = json.loads(obs.provenance_json) if getattr(obs, "provenance_json", None) else {}
    src_meta = json.loads(obs.metadata_source_json) if getattr(obs, "metadata_source_json", None) else {}

    footprint = {
        "lat_min": obs.lat_min if obs.lat_min is not None else 0.0,
        "lat_max": obs.lat_max if obs.lat_max is not None else 0.0,
        "lon_min": obs.lon_min if obs.lon_min is not None else 0.0,
        "lon_max": obs.lon_max if obs.lon_max is not None else 0.0,
    }
    solar_geo = {
        "sun_azimuth_deg": obs.sun_azimuth_deg if obs.sun_azimuth_deg is not None else 0.0,
        "sun_elevation_deg": obs.sun_elevation_deg if obs.sun_elevation_deg is not None else 0.0,
        "incidence_angle_deg": obs.incidence_angle_deg if obs.incidence_angle_deg is not None else 0.0,
        "emission_angle_deg": obs.emission_angle_deg if obs.emission_angle_deg is not None else 0.0,
        "phase_angle_deg": obs.phase_angle_deg if obs.phase_angle_deg is not None else 0.0,
    }
    spacecraft_geo = {
        "mission": getattr(obs, "mission", "CHANDRAYAAN-2"),
        "instrument": getattr(obs, "instrument", obs.sensor_type),
        "altitude_km": 100.0,
        "orbit_type": "POLAR_CIRCULAR",
    }
    data_prov = {
        "type": "SYNTHETIC" if obs.is_synthetic else "REAL_LUNAR",
        "is_synthetic": bool(obs.is_synthetic),
        "source": getattr(obs, "mission", "ISRO") if not obs.is_synthetic else "LUNARSYNAPSE_SYNTHETIC_SIMULATOR",
    }
    acq_time_str = obs.acquisition_timestamp.isoformat() if obs.acquisition_timestamp else None

    return ObservationResponse(
        id=obs.id,
        sensor_type=obs.sensor_type,
        sensor=obs.sensor_type,
        image_url=obs.image_path,
        acquisition_timestamp=obs.acquisition_timestamp,
        acquisition_time=acq_time_str,
        lat_min=obs.lat_min,
        lat_max=obs.lat_max,
        lon_min=obs.lon_min,
        lon_max=obs.lon_max,
        footprint=footprint,
        spatial_resolution_m=obs.spatial_resolution_m,
        spatial_resolution=obs.spatial_resolution_m,
        sun_azimuth_deg=obs.sun_azimuth_deg,
        sun_elevation_deg=obs.sun_elevation_deg,
        incidence_angle_deg=obs.incidence_angle_deg,
        emission_angle_deg=obs.emission_angle_deg,
        phase_angle_deg=obs.phase_angle_deg,
        solar_geometry=solar_geo,
        spacecraft_geometry=spacecraft_geo,
        metadata=json.loads(obs.metadata_json) if obs.metadata_json else {},
        preprocessing_history=json.loads(obs.preprocessing_history) if obs.preprocessing_history else [],
        is_synthetic=obs.is_synthetic,
        product_id=getattr(obs, "product_id", obs.id),
        mission=getattr(obs, "mission", None),
        instrument=getattr(obs, "instrument", obs.sensor_type),
        product_type=getattr(obs, "product_type", None),
        processing_level=getattr(obs, "processing_level", None),
        num_bands=getattr(obs, "num_bands", 1.0),
        data_type=getattr(obs, "data_type", "uint8"),
        nodata_value=getattr(obs, "nodata_value", None),
        source=getattr(obs, "raw_path", None) or ("REAL_DATA_CORPUS" if not obs.is_synthetic else "SYNTHETIC_GENERATOR"),
        provenance=prov or data_prov,
        metadata_provenance=src_meta,
        data_provenance=data_prov,
    )


@router.get("", response_model=List[ObservationResponse])
def get_all_observations(db: Session = Depends(get_db)):
    """Retrieves all registered multi-modal lunar observations."""
    obs_service = ObservationService(db)
    observations = obs_service.list_observations()
    return [_build_observation_response(obs) for obs in observations]


@router.post("", response_model=ObservationResponse, status_code=status.HTTP_201_CREATED)
def create_observation(payload: ObservationCreate, db: Session = Depends(get_db)):
    """Registers an observation with validation of coordinates, sensor type, and synthetic provenance."""
    allowed_sensors = [
        "OHRC", "TMC-2", "IIRS", "LROC_NAC", "SELENE_TC", "SIMULATED_OPTICAL",
        "OPTICAL_HIGH_RES", "OPTICAL_STEREO", "HYPERSPECTRAL"
    ]
    if payload.sensor_type not in allowed_sensors:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported sensor: '{payload.sensor_type}'. Must be one of: {allowed_sensors}",
        )

    # Validate coordinate bounds
    if payload.lat_min > payload.lat_max or payload.lon_min > payload.lon_max:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid geographic coordinates: lat_min ({payload.lat_min}) > lat_max ({payload.lat_max}) or lon_min ({payload.lon_min}) > lon_max ({payload.lon_max})",
        )
    if not (-90.0 <= payload.lat_min <= 90.0 and -90.0 <= payload.lat_max <= 90.0):
        raise HTTPException(status_code=400, detail="Latitude must be in range [-90, 90]")
    if not (-180.0 <= payload.lon_min <= 360.0 and -180.0 <= payload.lon_max <= 360.0):
        raise HTTPException(status_code=400, detail="Longitude must be in range [-180, 360]")

    # CRITICAL RULE 12: API clients MUST NOT be able to silently convert synthetic observations into real observations
    if not payload.is_synthetic:
        obs_service = ObservationService(db)
        existing = obs_service.get_observation(payload.id)
        if not existing or existing.is_synthetic:
            raise HTTPException(
                status_code=400,
                detail="Forbidden: Cannot register non-synthetic observation without authenticated real flight product data",
            )

    obs_service = ObservationService(db)
    existing = obs_service.get_observation(payload.id)
    if existing:
        return _build_observation_response(existing)

    import numpy as np
    import base64
    import cv2
    image_data = None
    if payload.image_data_base64:
        try:
            img_bytes = base64.b64decode(payload.image_data_base64)
            nparr = np.frombuffer(img_bytes, np.uint8)
            image_data = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
        except Exception:
            pass

    if image_data is None:
        rng = np.random.RandomState(42)
        noise = rng.normal(128, 20, size=(256, 256))
        import scipy.ndimage as ndimage
        image_data = np.clip(ndimage.gaussian_filter(noise, sigma=3.0), 0, 255).astype(np.uint8)


    obs = obs_service.create_observation(
        obs_id=payload.id,
        sensor_type=payload.sensor_type,
        image_data=image_data,
        spatial_resolution_m=payload.spatial_resolution_m,
        sun_azimuth_deg=payload.sun_azimuth_deg,
        sun_elevation_deg=payload.sun_elevation_deg,
        incidence_angle_deg=payload.incidence_angle_deg,
        emission_angle_deg=payload.emission_angle_deg,
        phase_angle_deg=payload.phase_angle_deg,
        lat_min=payload.lat_min,
        lat_max=payload.lat_max,
        lon_min=payload.lon_min,
        lon_max=payload.lon_max,
        metadata=payload.metadata,
        is_synthetic=payload.is_synthetic,
    )
    return _build_observation_response(obs)



@router.post("/ingest", response_model=ObservationResponse)
def ingest_real_observation(file_path: str, source: str = None, db: Session = Depends(get_db)):
    """Ingests a real scientific lunar product (OHRC, TMC-2, IIRS, LROC, SELENE) from disk path."""
    obs_service = ObservationService(db)
    try:
        obs = obs_service.ingest_real_product(file_path=file_path, source=source)
        return _build_observation_response(obs)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to ingest product: {str(e)}")


@router.get("/{observation_id}", response_model=ObservationResponse)
def get_observation_by_id(observation_id: str, db: Session = Depends(get_db)):
    """Retrieves metadata for a specific observation."""
    obs_service = ObservationService(db)
    obs = obs_service.get_observation(observation_id)
    if not obs:
        raise HTTPException(status_code=404, detail=f"Observation {observation_id} not found")

    return _build_observation_response(obs)


@router.get("/{observation_id}/image")
def get_observation_image(observation_id: str):
    """Serves the raw PNG image of an observation with path traversal protection."""
    safe_id = Path(observation_id).name
    file_path = (settings.IMAGES_DIR / f"{safe_id}.png").resolve()
    images_dir_resolved = settings.IMAGES_DIR.resolve()
    if not str(file_path).startswith(str(images_dir_resolved)) or not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Image for {observation_id} not found on disk")
    return FileResponse(path=str(file_path), media_type="image/png")


@router.get("/experiments/{filename}")
def get_experiment_image(filename: str):
    """Serves registered or difference overlay artifact images with path traversal protection."""
    safe_name = Path(filename).name
    file_path = (settings.IMAGES_DIR / safe_name).resolve()
    images_dir_resolved = settings.IMAGES_DIR.resolve()
    if not str(file_path).startswith(str(images_dir_resolved)) or not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Experiment image {filename} not found")
    return FileResponse(path=str(file_path), media_type="image/png")

