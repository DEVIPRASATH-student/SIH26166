"""Dataset Discovery & Sensor Identity Verification Engine.

Recursively scans the workspace for lunar data products, parses per-product metadata via
Phase 1 ProductIngestionEngine, and verifies sensor identity from authoritative label structures
(NEVER guessing sensor identity from filename alone).
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import logging

from ..data.ingestion.factory import ProductIngestionEngine
from ..data.models import LunarProduct, ValueStatus

logger = logging.getLogger("LunarSynapse.ML.DatasetInventory")


@dataclass
class DatasetInventoryItem:
    filename: str
    full_path: str
    extension: str
    file_size_bytes: int
    dimensions: str
    num_bands: int
    data_type: str
    sensor: str  # Confirmed from metadata label, or UNKNOWN
    product_id: str
    acquisition_time: str
    gsd_m: str
    solar_geometry: str
    geographic_bounds: str
    projection: str
    metadata_source: str
    is_real_data: bool
    sha256: str
    sensor_verification_status: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "filename": self.filename,
            "full_path": self.full_path,
            "extension": self.extension,
            "file_size_bytes": self.file_size_bytes,
            "dimensions": self.dimensions,
            "num_bands": self.num_bands,
            "data_type": self.data_type,
            "sensor": self.sensor,
            "product_id": self.product_id,
            "acquisition_time": self.acquisition_time,
            "gsd_m": self.gsd_m,
            "solar_geometry": self.solar_geometry,
            "geographic_bounds": self.geographic_bounds,
            "projection": self.projection,
            "metadata_source": self.metadata_source,
            "is_real_data": self.is_real_data,
            "sha256": self.sha256,
            "sensor_verification_status": self.sensor_verification_status,
        }


class DatasetScanner:
    """Recursively scans workspace for lunar products and builds scientific inventory."""

    SUPPORTED_EXTENSIONS = {
        ".xml", ".lbl", ".tif", ".tiff", ".img", ".jp2", ".fits", ".cub", ".h5", ".hdf", ".nc", ".png"
    }

    def __init__(self, workspace_root: str = "."):
        self.workspace_root = os.path.abspath(workspace_root)
        self.ingestion_engine = ProductIngestionEngine()

    def scan_workspace(self) -> List[DatasetInventoryItem]:
        """Scans workspace recursively for candidate lunar dataset files."""
        inventory: List[DatasetInventoryItem] = []
        visited_paths = set()

        for root, dirs, files in os.walk(self.workspace_root):
            # Skip virtualenv, git, node_modules, and cache folders
            if any(skip in root.lower() for skip in [".venv", "venv", ".git", "node_modules", ".pytest_cache", "__pycache__"]):
                continue

            for fn in files:
                ext = os.path.splitext(fn)[1].lower()
                if ext in self.SUPPORTED_EXTENSIONS:
                    file_path = os.path.join(root, fn)
                    abs_path = os.path.abspath(file_path)
                    if abs_path in visited_paths:
                        continue
                    visited_paths.add(abs_path)

                    item = self._inspect_file(abs_path)
                    if item:
                        inventory.append(item)

        return inventory

    def _inspect_file(self, file_path: str) -> Optional[DatasetInventoryItem]:
        """Parses product through ProductIngestionEngine and extracts authoritative inventory attributes."""
        try:
            p_path = Path(file_path)
            size = os.path.getsize(file_path)
            ext = p_path.suffix.lower()

            # Attempt Phase 1 ingestion
            product: LunarProduct = self.ingestion_engine.ingest_product(p_path)
            meta = product.metadata

            # STRICT SENSOR IDENTITY GUARDRAIL:
            # Confirm sensor identity ONLY if confirmed in metadata label / instrument field.
            # DO NOT infer sensor from filename alone.
            sensor_str = meta.instrument or "UNKNOWN"
            if sensor_str.upper() in ["UNKNOWN", "GENERIC_RASTER", "UNSPECIFIED"]:
                # Double-check raw_metadata for reliable instrument tags
                raw = meta.raw_metadata or {}
                if "instrument_id" in raw:
                    sensor_str = str(raw["instrument_id"]).upper()
                elif "instrument_name" in raw:
                    sensor_str = str(raw["instrument_name"]).upper()
                else:
                    sensor_str = "UNKNOWN"

            # Format GSD
            gsd_status = meta.value_statuses.get("gsd_m", ValueStatus.UNKNOWN)
            if gsd_status == ValueStatus.KNOWN and meta.gsd_m is not None:
                gsd_str = f"{meta.gsd_m:.2f} m/px"
            else:
                gsd_str = "UNKNOWN"

            # Format solar geometry
            sun = meta.solar_illumination
            if sun.status == ValueStatus.KNOWN and sun.sun_azimuth_deg is not None:
                sun_str = f"Az={sun.sun_azimuth_deg:.1f}°, El={sun.sun_elevation_deg:.1f}°"
            else:
                sun_str = "UNKNOWN"

            # Format geographic bounds
            gb = meta.geographic_bounds
            if gb.status == ValueStatus.KNOWN and gb.lat_min is not None:
                gb_str = f"[{gb.lat_min:.2f}°, {gb.lat_max:.2f}° N, {gb.lon_min:.2f}°, {gb.lon_max:.2f}° E]"
            else:
                gb_str = "UNKNOWN"

            # Format dimensions
            lines = meta.lines or (product.raster_data.shape[0] if product.raster_data is not None else 0)
            samples = meta.samples or (product.raster_data.shape[1] if product.raster_data is not None else 0)
            dims_str = f"{lines}x{samples}" if lines and samples else "UNKNOWN"

            # Format acquisition time
            acq_str = meta.acquisition_timestamp.strftime("%Y-%m-%d %H:%M:%S") if meta.acquisition_timestamp else "UNKNOWN"

            # Compute SHA256
            import hashlib
            h = hashlib.sha256()
            with open(file_path, "rb") as f:
                while chunk := f.read(65536):
                    h.update(chunk)
            sha256_hex = h.hexdigest()

            # Determine sensor verification status
            if sensor_str.upper() in ["UNKNOWN", "GENERIC_RASTER", "UNSPECIFIED"]:
                sensor_ver = "UNKNOWN"
            elif sensor_str.upper() in ["OHRC", "TMC-2", "TMC2", "IIRS", "LRO_NAC", "NAC", "TC", "MI"]:
                # Only mark VERIFIED if parsed from label metadata or under data/real/
                if ext in [".xml", ".lbl"] or "data/real" in file_path.replace("\\", "/").lower():
                    sensor_ver = "VERIFIED"
                else:
                    sensor_ver = "UNKNOWN"
            else:
                sensor_ver = "REJECTED"

            # Determine if real dataset file vs synthetic/demo fixture
            norm_path = file_path.replace("\\", "/").lower()
            is_synthetic_path = "synthetic" in norm_path or "outgraph/data/storage" in norm_path
            is_real = ("data/real" in norm_path or ext in [".xml", ".lbl"]) and not is_synthetic_path and not product.is_synthetic

            # Metadata source
            meta_src = meta.processing_level or ("PDS4 XML Label" if ext in [".xml", ".lbl"] else "Raster Metadata")

            return DatasetInventoryItem(
                filename=p_path.name,
                full_path=file_path,
                extension=ext,
                file_size_bytes=size,
                dimensions=dims_str,
                num_bands=meta.num_bands,
                data_type=meta.data_type,
                sensor=sensor_str,
                product_id=meta.product_id,
                acquisition_time=acq_str,
                gsd_m=gsd_str,
                solar_geometry=sun_str,
                geographic_bounds=gb_str,
                projection=gb.crs or "UNKNOWN",
                metadata_source=meta_src,
                is_real_data=is_real,
                sha256=sha256_hex,
                sensor_verification_status=sensor_ver,
            )
        except Exception as e:
            logger.debug(f"File {file_path} skipped during inventory scan: {e}")
            return None
