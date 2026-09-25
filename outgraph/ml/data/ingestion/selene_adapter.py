"""SELENE / Kaguya Ingestion Adapter.
Handles JAXA SELENE (Kaguya) Terrain Camera & Multiband Imager products conservatively.
"""

import xml.etree.ElementTree as ET
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


def _find_first_elem(root: ET.Element, tags: List[str]) -> Optional[ET.Element]:
    for tag in tags:
        elem = root.find(f".//{tag}")
        if elem is not None:
            return elem
    return None


class SELENEAdapter(BaseIngestionAdapter):
    """Adapter for JAXA SELENE (Kaguya) lunar imagery products."""

    def __init__(self):
        super().__init__(source_name="SELENE / Kaguya")

    def can_ingest(self, file_path: Path) -> bool:
        name_upper = file_path.name.upper()
        return "SELENE" in name_upper or "KAGUYA" in name_upper or "TC_" in name_upper or "MI_" in name_upper

    def extract_metadata(self, file_path: Path) -> ProductMetadata:
        raw_meta: Dict[str, Any] = {}
        statuses: Dict[str, ValueStatus] = {}

        product_id = file_path.stem
        mission = "SELENE / Kaguya"
        instrument = "Terrain Camera" if "TC" in file_path.name.upper() else "Multiband Imager"
        gsd_m = None  # MUST remain None if missing in metadata!

        solar = SolarIllumination()
        geo = GeographicBounds()
        view = ViewingGeometry()

        xml_path = file_path if file_path.suffix.lower() == ".xml" else file_path.with_suffix(".xml")
        if xml_path.exists() and xml_path.is_file():
            try:
                tree = ET.parse(xml_path)
                root = tree.getroot()

                for elem in root.iter():
                    if '}' in elem.tag:
                        elem.tag = elem.tag.split('}', 1)[1]
                    if elem.text and elem.text.strip():
                        raw_meta[elem.tag] = elem.text.strip()

                # Resolution
                res_elem = _find_first_elem(root, ["resolution", "pixel_resolution"])
                if res_elem is not None and res_elem.text:
                    try:
                        gsd_m = float(res_elem.text)
                    except ValueError:
                        pass

            except Exception as e:
                raw_meta["parse_error"] = str(e)

        statuses["solar_illumination"] = solar.status
        statuses["geographic_bounds"] = geo.status
        statuses["gsd_m"] = ValueStatus.KNOWN if gsd_m is not None else ValueStatus.UNKNOWN

        return ProductMetadata(
            product_id=product_id,
            mission=mission,
            instrument=instrument,
            product_type="SELENE Lunar Imagery",
            gsd_m=gsd_m,
            geographic_bounds=geo,
            solar_illumination=solar,
            viewing_geometry=view,
            value_statuses=statuses,
            raw_metadata=raw_meta,
        )

    def load_raster_data(self, file_path: Path, metadata: ProductMetadata) -> Tuple[Optional[np.ndarray], List[str]]:
        warnings: List[str] = []
        if file_path.suffix.lower() == ".xml":
            for ext in [".tif", ".tiff", ".img", ".png", ".jpg"]:
                companion = file_path.with_suffix(ext)
                if companion.exists():
                    file_path = companion
                    break

        if not file_path.exists() or file_path.suffix.lower() == ".xml":
            return None, ["Raster image file not found"]

        try:
            img_pil = Image.open(file_path)
            arr = np.array(img_pil)
            metadata.lines = arr.shape[0]
            metadata.samples = arr.shape[1]
            metadata.num_bands = arr.shape[2] if arr.ndim == 3 else 1
            metadata.data_type = str(arr.dtype)
            return arr, warnings
        except Exception as e:
            warnings.append(f"Failed to read SELENE image raster: {str(e)}")
            return None, warnings
