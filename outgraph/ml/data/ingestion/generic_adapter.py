"""Generic Lunar Raster Ingestion Adapter.
Fallback loader for standard scientific GeoTIFF, TIFF, PNG, and JPEG files.
Extracts header tags when available; represents missing metadata strictly as UNKNOWN.
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
from PIL import Image

from .base import BaseIngestionAdapter
from ..models import (
    ProductMetadata,
    SolarIllumination,
    ViewingGeometry,
    GeographicBounds,
    ValueStatus,
)


class GenericAdapter(BaseIngestionAdapter):
    """Fallback adapter for standard image formats and generic GeoTIFFs."""

    def __init__(self):
        super().__init__(source_name="Generic Raster Loader")

    def can_ingest(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in [".tif", ".tiff", ".png", ".jpg", ".jpeg", ".bmp"]

    def extract_metadata(self, file_path: Path) -> ProductMetadata:
        raw_meta: Dict[str, Any] = {}
        statuses: Dict[str, ValueStatus] = {}

        product_id = file_path.stem
        solar = SolarIllumination()
        geo = GeographicBounds()
        view = ViewingGeometry()
        gsd_m = None

        try:
            with Image.open(file_path) as img:
                raw_meta["format"] = img.format
                raw_meta["mode"] = img.mode
                raw_meta["size"] = img.size

                # Extract TIFF / EXIF tags if present
                if hasattr(img, "tag_v2"):
                    for k, v in img.tag_v2.items():
                        raw_meta[f"tiff_tag_{k}"] = str(v)
        except Exception as e:
            raw_meta["read_error"] = str(e)

        statuses["solar_illumination"] = solar.status
        statuses["geographic_bounds"] = geo.status
        statuses["gsd_m"] = ValueStatus.UNKNOWN

        return ProductMetadata(
            product_id=product_id,
            mission=None,  # UNKNOWN
            instrument=None,  # UNKNOWN
            product_type="Generic Raster Product",
            gsd_m=gsd_m,  # None (UNKNOWN)
            geographic_bounds=geo,
            solar_illumination=solar,
            viewing_geometry=view,
            value_statuses=statuses,
            raw_metadata=raw_meta,
        )

    def load_raster_data(self, file_path: Path, metadata: ProductMetadata) -> Tuple[Optional[np.ndarray], List[str]]:
        warnings: List[str] = []
        try:
            img = Image.open(file_path)
            arr = np.array(img)
            metadata.lines = arr.shape[0]
            metadata.samples = arr.shape[1]
            metadata.num_bands = arr.shape[2] if arr.ndim == 3 else 1
            metadata.data_type = str(arr.dtype)
            return arr, warnings
        except Exception as e:
            warnings.append(f"Failed to load image array: {str(e)}")
            return None, warnings
