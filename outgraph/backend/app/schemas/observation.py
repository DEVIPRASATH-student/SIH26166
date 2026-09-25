"""Observation Pydantic Schemas."""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class ObservationCreate(BaseModel):
    id: str
    sensor_type: str = Field(..., description="OHRC, TMC-2, IIRS, LROC_NAC, SELENE_TC, or SIMULATED_OPTICAL")
    image_url: Optional[str] = None
    image_data_base64: Optional[str] = None
    lat_min: float
    lat_max: float
    lon_min: float
    lon_max: float
    spatial_resolution_m: float
    sun_azimuth_deg: float = 0.0
    sun_elevation_deg: float = 0.0
    incidence_angle_deg: float = 0.0
    emission_angle_deg: float = 0.0
    phase_angle_deg: float = 0.0
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
    sensor: Optional[str] = None
    image_url: str
    acquisition_timestamp: Optional[datetime] = None
    acquisition_time: Optional[str] = None
    lat_min: Optional[float] = None
    lat_max: Optional[float] = None
    lon_min: Optional[float] = None
    lon_max: Optional[float] = None
    footprint: Optional[Dict[str, float]] = None
    spatial_resolution_m: Optional[float] = None
    spatial_resolution: Optional[float] = None
    sun_azimuth_deg: Optional[float] = None
    sun_elevation_deg: Optional[float] = None
    incidence_angle_deg: Optional[float] = None
    emission_angle_deg: Optional[float] = None
    phase_angle_deg: Optional[float] = None
    solar_geometry: Optional[Dict[str, float]] = None
    spacecraft_geometry: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    preprocessing_history: List[Any] = Field(default_factory=list)
    is_synthetic: bool = True

    # Real Product Attributes
    product_id: Optional[str] = None
    mission: Optional[str] = None
    instrument: Optional[str] = None
    product_type: Optional[str] = None
    processing_level: Optional[str] = None
    num_bands: Optional[float] = 1.0
    data_type: Optional[str] = "uint8"
    nodata_value: Optional[float] = None
    source: Optional[str] = None
    provenance: Optional[Dict[str, Any]] = None
    metadata_provenance: Optional[Dict[str, Any]] = None
    data_provenance: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


