"""Lunar Product Abstraction Models.
Provides internal representation for real lunar observations and products.
Distinguishes KNOWN, UNKNOWN, and DERIVED metadata without fabricating missing values.
"""

from enum import Enum
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field
import numpy as np


class ValueStatus(str, Enum):
    KNOWN = "KNOWN"
    UNKNOWN = "UNKNOWN"
    DERIVED = "DERIVED"


class MetadataValue(BaseModel):
    """Metadata field with explicit provenance and value status."""
    status: ValueStatus = ValueStatus.UNKNOWN
    value: Optional[Any] = None
    source_key: Optional[str] = None
    description: Optional[str] = None

    @classmethod
    def known(cls, value: Any, source_key: Optional[str] = None) -> "MetadataValue":
        return cls(status=ValueStatus.KNOWN, value=value, source_key=source_key)

    @classmethod
    def unknown(cls, source_key: Optional[str] = None, description: Optional[str] = None) -> "MetadataValue":
        return cls(status=ValueStatus.UNKNOWN, value=None, source_key=source_key, description=description)

    @classmethod
    def derived(cls, value: Any, description: str) -> "MetadataValue":
        return cls(status=ValueStatus.DERIVED, value=value, description=description)


class SolarIllumination(BaseModel):
    """Solar illumination geometry extracted directly from metadata."""
    sun_azimuth_deg: Optional[float] = None
    sun_elevation_deg: Optional[float] = None
    incidence_angle_deg: Optional[float] = None
    emission_angle_deg: Optional[float] = None
    phase_angle_deg: Optional[float] = None
    status: ValueStatus = ValueStatus.UNKNOWN


class ViewingGeometry(BaseModel):
    """Orbital spacecraft viewing geometry."""
    sub_solar_latitude: Optional[float] = None
    sub_solar_longitude: Optional[float] = None
    sub_spacecraft_latitude: Optional[float] = None
    sub_spacecraft_longitude: Optional[float] = None
    spacecraft_altitude_km: Optional[float] = None
    status: ValueStatus = ValueStatus.UNKNOWN


class GeographicBounds(BaseModel):
    """Geographic bounding footprint (latitude / longitude)."""
    lat_min: Optional[float] = None
    lat_max: Optional[float] = None
    lon_min: Optional[float] = None
    lon_max: Optional[float] = None
    center_lat: Optional[float] = None
    center_lon: Optional[float] = None
    crs: Optional[str] = None
    status: ValueStatus = ValueStatus.UNKNOWN


class BandInfo(BaseModel):
    """Single band information for multi-band / spectral imagery."""
    band_index: int
    band_name: Optional[str] = None
    center_wavelength_nm: Optional[float] = None
    bandwidth_nm: Optional[float] = None
    description: Optional[str] = None


class ProvenanceRecord(BaseModel):
    """Complete provenance and transformation history."""
    source_name: str
    original_filename: str
    product_id: str
    ingestion_timestamp: datetime = Field(default_factory=datetime.utcnow)
    sha256_checksum: Optional[str] = None
    metadata_extraction_status: str = "COMPLETED"
    processing_history: List[Dict[str, Any]] = Field(default_factory=list)


class ValidationResult(BaseModel):
    """Product validation status and explicit issues."""
    is_valid: bool = True
    validation_errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    checked_rules: List[str] = Field(default_factory=list)


# Nominal Reference Specs for Documentation / Informational purposes ONLY.
# MUST NEVER overwrite actual product metadata or fill in missing GSD/resolution values.
NOMINAL_REFERENCE_SPECS: Dict[str, Dict[str, Any]] = {
    "OHRC": {
        "mission": "Chandrayaan-2",
        "instrument": "Orbiter High Resolution Camera",
        "nominal_gsd_m": 0.32,
        "type": "Panchromatic High-Resolution",
        "description": "High resolution lunar surface imaging from ~100 km orbit",
    },
    "TMC-2": {
        "mission": "Chandrayaan-2",
        "instrument": "Terrain Mapping Camera 2",
        "nominal_gsd_m": 5.0,
        "type": "Stereo Panchromatic",
        "description": "3D mapping of lunar surface in fore, AFT, and nadir views",
    },
    "IIRS": {
        "mission": "Chandrayaan-2",
        "instrument": "Imaging Infrared Spectrometer",
        "nominal_gsd_m": 20.0,
        "type": "Hyperspectral (0.8 - 5.0 um)",
        "description": "Mineralogical and hydration mapping of lunar surface",
    },
    "LROC_NAC": {
        "mission": "Lunar Reconnaissance Orbiter",
        "instrument": "Narrow Angle Camera",
        "nominal_gsd_m": 0.5,
        "type": "Panchromatic High-Resolution",
        "description": "Sub-meter scale lunar reconnaissance imaging",
    },
    "SELENE_TC": {
        "mission": "SELENE / Kaguya",
        "instrument": "Terrain Camera",
        "nominal_gsd_m": 10.0,
        "type": "Stereo Panchromatic",
        "description": "High-resolution global mapping of the Moon",
    },
}


class ProductMetadata(BaseModel):
    """Extracted scientific product metadata container.
    Guarantees explicit UNKNOWN / null representation when metadata is absent.
    """
    product_id: str
    mission: Optional[str] = None
    instrument: Optional[str] = None
    product_type: Optional[str] = None
    processing_level: Optional[str] = None
    acquisition_timestamp: Optional[datetime] = None

    # Spatial & Raster properties
    lines: Optional[int] = None
    samples: Optional[int] = None
    num_bands: int = 1
    data_type: str = "unknown"
    bit_depth: Optional[int] = None
    nodata_value: Optional[float] = None
    gsd_m: Optional[float] = None  # MUST come from metadata, NEVER nominal reference overwrite

    # Structural metadata containers
    geographic_bounds: GeographicBounds = Field(default_factory=GeographicBounds)
    solar_illumination: SolarIllumination = Field(default_factory=SolarIllumination)
    viewing_geometry: ViewingGeometry = Field(default_factory=ViewingGeometry)
    bands: List[BandInfo] = Field(default_factory=list)

    # Status tracking per category
    value_statuses: Dict[str, ValueStatus] = Field(default_factory=dict)
    raw_metadata: Dict[str, Any] = Field(default_factory=dict)


class LunarProduct:
    """Master in-memory scientific product abstraction."""

    def __init__(
        self,
        product_id: str,
        file_path: str,
        metadata: ProductMetadata,
        provenance: ProvenanceRecord,
        validation: ValidationResult,
        raster_data: Optional[np.ndarray] = None,
        is_synthetic: bool = False,
    ):
        self.product_id = product_id
        self.file_path = file_path
        self.metadata = metadata
        self.provenance = provenance
        self.validation = validation
        self.raster_data = raster_data
        self.is_synthetic = is_synthetic

    def get_band(self, band_index: int = 0) -> Optional[np.ndarray]:
        """Returns single 2D band array without destructive alterations."""
        if self.raster_data is None:
            return None
        if self.raster_data.ndim == 2:
            return self.raster_data
        if self.raster_data.ndim == 3 and band_index < self.raster_data.shape[2]:
            return self.raster_data[:, :, band_index]
        return None
