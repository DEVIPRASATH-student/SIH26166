"""Observation Pydantic Schemas."""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class ObservationCreate(BaseModel):
    id: str
    sensor_type: str = Field(..., description="OHRC, TMC-2, or IIRS")
    image_url: str
    lat_min: float
    lat_max: float
    lon_min: float
    lon_max: float
    spatial_resolution_m: float
    sun_azimuth_deg: float
    sun_elevation_deg: float
    incidence_angle_deg: float
    emission_angle_deg: float
    phase_angle_deg: float
    metadata: Dict[str, Any] = Field(default_factory=dict)
    is_synthetic: bool = True


class ObservationSummary(BaseModel):
    id: str
    sensor_type: str
    spatial_resolution_m: float
    sun_azimuth_deg: float
    sun_elevation_deg: float
    phase_angle_deg: float
    is_synthetic: bool
    image_url: str


class ObservationResponse(BaseModel):
    id: str
    sensor_type: str
    image_url: str
    acquisition_timestamp: datetime
    lat_min: float
    lat_max: float
    lon_min: float
    lon_max: float
    spatial_resolution_m: float
    sun_azimuth_deg: float
    sun_elevation_deg: float
    incidence_angle_deg: float
    emission_angle_deg: float
    phase_angle_deg: float
    metadata: Dict[str, Any]
    preprocessing_history: List[str]
    is_synthetic: bool

    class Config:
        from_attributes = True
