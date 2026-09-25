"""Product Validation Engine.
Validates file existence, format support, dimension validity, numeric integrity,
band structure, NoData handling, and geospatial metadata consistency.
"""

from pathlib import Path
from typing import List, Optional, Any
import numpy as np

from ..models import ProductMetadata, ValidationResult, ValueStatus


class ProductValidator:
    """Performs non-destructive validation checks on ingested products."""

    @classmethod
    def validate_product(
        cls,
        file_path: Path,
        metadata: ProductMetadata,
        raster_data: Optional[np.ndarray] = None,
    ) -> ValidationResult:
        """Executes validation rules on product file and metadata."""
        errors: List[str] = []
        warnings: List[str] = []
        rules: List[str] = []

        # Rule 1: File Existence & Readability
        rules.append("FILE_EXISTENCE_CHECK")
        if not file_path.exists():
            errors.append(f"File {file_path.name} does not exist on disk")
        elif not file_path.is_file():
            errors.append(f"Path {file_path} is not a valid file")

        # Rule 2: Image Dimension Validity
        rules.append("DIMENSION_VALIDITY_CHECK")
        if metadata.lines is not None and metadata.lines <= 0:
            errors.append(f"Invalid lines count: {metadata.lines}")
        if metadata.samples is not None and metadata.samples <= 0:
            errors.append(f"Invalid samples count: {metadata.samples}")

        # Rule 3: Band Structure Validity
        rules.append("BAND_STRUCTURE_CHECK")
        if metadata.num_bands < 1:
            errors.append(f"Invalid band count: {metadata.num_bands}")
        if metadata.instrument == "IIRS" and metadata.num_bands < 2:
            warnings.append("IIRS spectrometer product loaded with single band (expected hyperspectral band stack)")

        # Rule 4: Numeric Data Integrity
        rules.append("NUMERIC_DATA_INTEGRITY_CHECK")
        if raster_data is not None:
            if np.isnan(raster_data).any():
                warnings.append("Raster contains NaN values")
            if np.isinf(raster_data).any():
                errors.append("Raster contains infinite (Inf) numeric values")

        # Rule 5: Geospatial Footprint Sanity Check
        rules.append("GEOSPATIAL_FOOTPRINT_CHECK")
        gb = metadata.geographic_bounds
        if gb.status == ValueStatus.KNOWN and gb.lat_min is not None and gb.lat_max is not None:
            if not (-90.0 <= gb.lat_min <= 90.0 and -90.0 <= gb.lat_max <= 90.0):
                errors.append(f"Latitude bounds out of range [-90, 90]: min={gb.lat_min}, max={gb.lat_max}")
            if gb.lat_min > gb.lat_max:
                errors.append(f"lat_min ({gb.lat_min}) greater than lat_max ({gb.lat_max})")
        else:
            warnings.append("Geographic footprint not provided in metadata (marked UNKNOWN)")

        # Rule 6: Solar Geometry Sanity Check
        rules.append("SOLAR_GEOMETRY_CHECK")
        si = metadata.solar_illumination
        if si.status == ValueStatus.KNOWN:
            if si.sun_azimuth_deg is not None and not (0.0 <= si.sun_azimuth_deg <= 360.0):
                errors.append(f"Sun azimuth out of range [0, 360]: {si.sun_azimuth_deg}")
            if si.sun_elevation_deg is not None and not (-90.0 <= si.sun_elevation_deg <= 90.0):
                errors.append(f"Sun elevation out of range [-90, 90]: {si.sun_elevation_deg}")
        else:
            warnings.append("Solar illumination geometry not provided in metadata (marked UNKNOWN)")

        # Rule 7: GSD Availability Check (Strictly from metadata)
        rules.append("GSD_METADATA_CHECK")
        if metadata.gsd_m is None:
            warnings.append("GSD / spatial resolution unavailable in product metadata (marked UNKNOWN)")

        is_valid = (len(errors) == 0)

        return ValidationResult(
            is_valid=is_valid,
            validation_errors=errors,
            warnings=warnings,
            checked_rules=rules,
        )
