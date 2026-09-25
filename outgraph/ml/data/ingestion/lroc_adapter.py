"""LROC / LRO NAC Ingestion Adapter.
Handles LRO Narrow Angle Camera imagery and PDS label metadata extraction conservatively.
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


class LROCAdapter(BaseIngestionAdapter):
    """Adapter for NASA LRO Narrow Angle Camera (LROC NAC) products."""

    def __init__(self):
        super().__init__(source_name="LROC / LRO NAC")

    def can_ingest(self, file_path: Path) -> bool:
        name_upper = file_path.name.upper()
        return "LROC" in name_upper or "NAC" in name_upper or "M1" in name_upper or "M0" in name_upper

    def extract_metadata(self, file_path: Path) -> ProductMetadata:
        raw_meta: Dict[str, Any] = {}
        statuses: Dict[str, ValueStatus] = {}

        product_id = file_path.stem
        mission = "Lunar Reconnaissance Orbiter"
        instrument = "LROC NAC"
        gsd_m = None  # MUST remain None if not present in metadata!

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

                lid_elem = _find_first_elem(root, ["logical_identifier", "title"])
                if lid_elem is not None and lid_elem.text:
                    product_id = lid_elem.text.strip()

                # Solar geometry
                inc_elem = _find_first_elem(root, ["incidence_angle"])
                az_elem = _find_first_elem(root, ["sun_azimuth_angle"])
                el_elem = _find_first_elem(root, ["sun_elevation_angle"])

                if inc_elem is not None and inc_elem.text:
                    try:
                        solar.incidence_angle_deg = float(inc_elem.text)
                        solar.status = ValueStatus.KNOWN
                    except ValueError:
                        pass
                if az_elem is not None and az_elem.text:
                    try:
                        solar.sun_azimuth_deg = float(az_elem.text)
                    except ValueError:
                        pass
                if el_elem is not None and el_elem.text:
                    try:
                        solar.sun_elevation_deg = float(el_elem.text)
                    except ValueError:
                        pass

                # Resolution
                res_elem = _find_first_elem(root, ["pixel_resolution", "resolution"])
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
            product_type="Narrow Angle Camera Observation",
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
            warnings.append(f"Failed to read LROC image raster: {str(e)}")
            return None, warnings
