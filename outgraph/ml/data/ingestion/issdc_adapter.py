"""ISSDC / Chandrayaan-2 Ingestion Adapter.
Handles OHRC, TMC-2, and IIRS products with conservative PDS4 XML parsing.
Never fabricates missing metadata or overwrites actual GSD with nominal specifications.
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
    BandInfo,
    ValueStatus,
)


def _find_first_elem(root: ET.Element, tags: List[str]) -> Optional[ET.Element]:
    """Safely finds first matching XML element without Element boolean evaluation gotchas."""
    for tag in tags:
        elem = root.find(f".//{tag}")
        if elem is not None:
            return elem
    return None


class ISSDCAdapter(BaseIngestionAdapter):
    """Adapter for ISRO ISSDC Chandrayaan-2 payload products (OHRC, TMC-2, IIRS)."""

    def __init__(self):
        super().__init__(source_name="ISSDC / Chandrayaan-2")

    def can_ingest(self, file_path: Path) -> bool:
        """Checks if filename or label matches Chandrayaan-2 naming patterns or XML PDS4 tags."""
        name_upper = file_path.name.upper()
        if any(token in name_upper for token in ["OHRC", "TMC2", "TMC-2", "TMC", "IIRS", "CH2", "CHANDRAYAAN"]):
            return True
        if file_path.suffix.lower() == ".xml":
            try:
                tree = ET.parse(file_path)
                root = tree.getroot()
                if "pds" in root.tag.lower() or "product_observational" in root.tag.lower():
                    return True
            except Exception:
                pass
        return False

    def extract_metadata(self, file_path: Path) -> ProductMetadata:
        """Extracts available metadata from PDS4 XML label or associated sidecar files conservatively."""
        raw_meta: Dict[str, Any] = {}
        statuses: Dict[str, ValueStatus] = {}

        # Look for XML sidecar if file_path is an image
        xml_path = file_path if file_path.suffix.lower() == ".xml" else file_path.with_suffix(".xml")

        product_id = file_path.stem
        instrument = None
        mission = "Chandrayaan-2"
        processing_level = None
        acquisition_time = None

        lines = None
        samples = None
        num_bands = 1
        data_type = "unknown"
        nodata_val = None
        gsd_m = None  # MUST originate from metadata if present, NEVER nominal reference

        solar = SolarIllumination()
        geo = GeographicBounds()
        view = ViewingGeometry()
        bands: List[BandInfo] = []

        if xml_path.exists() and xml_path.is_file():
            try:
                tree = ET.parse(xml_path)
                root = tree.getroot()

                # Strip XML namespaces for reliable conservative tag matching
                for elem in root.iter():
                    if '}' in elem.tag:
                        elem.tag = elem.tag.split('}', 1)[1]

                # Save raw tag structure
                for elem in root.iter():
                    if elem.text and elem.text.strip():
                        raw_meta[elem.tag] = elem.text.strip()

                # Extract basic identification
                lid_elem = _find_first_elem(root, ["logical_identifier", "title"])
                if lid_elem is not None and lid_elem.text:
                    product_id = lid_elem.text.strip()

                # Extract Mission & Spacecraft
                for comp in root.findall(".//Observing_System_Component"):
                    t_elem = comp.find("type")
                    n_elem = comp.find("name")
                    if t_elem is not None and t_elem.text and n_elem is not None and n_elem.text:
                        c_type = t_elem.text.strip().upper()
                        c_name = n_elem.text.strip()
                        if "MISSION" in c_type or "INVESTIGATION" in c_type:
                            mission = c_name
                        elif "INSTRUMENT" in c_type:
                            inst_text = c_name.upper()
                            if "OHRC" in inst_text or "HIGH RESOLUTION CAMERA" in inst_text:
                                instrument = "OHRC"
                            elif "TMC" in inst_text or "TERRAIN MAPPING CAMERA" in inst_text:
                                instrument = "TMC-2"
                            elif "IIRS" in inst_text or "INFRARED SPECTROMETER" in inst_text:
                                instrument = "IIRS"
                            else:
                                instrument = c_name

                # Fallback to direct instrument tags if not resolved from Observing_System_Component
                if instrument is None:
                    inst_elem = _find_first_elem(root, ["instrument_name", "instrument_id"])
                    if inst_elem is not None and inst_elem.text:
                        inst_text = inst_elem.text.strip().upper()
                        if "OHRC" in inst_text or "HIGH RESOLUTION CAMERA" in inst_text:
                            instrument = "OHRC"
                        elif "TMC" in inst_text or "TERRAIN MAPPING CAMERA" in inst_text:
                            instrument = "TMC-2"
                        elif "IIRS" in inst_text or "INFRARED SPECTROMETER" in inst_text:
                            instrument = "IIRS"
                        else:
                            instrument = inst_elem.text.strip()

                # Processing level
                proc_elem = _find_first_elem(root, ["processing_level"])
                if proc_elem is not None and proc_elem.text:
                    processing_level = proc_elem.text.strip()

                # Acquisition time
                acq_elem = _find_first_elem(root, ["start_date_time", "start_time", "observation_start_time"])
                if acq_elem is not None and acq_elem.text:
                    try:
                        time_str = acq_elem.text.strip().replace("Z", "+00:00")
                        acquisition_time = datetime.fromisoformat(time_str)
                    except Exception:
                        pass

                # Extract Solar Illumination conservatively
                az_elem = _find_first_elem(root, ["sun_azimuth", "sun_azimuth_angle", "solar_azimuth"])
                el_elem = _find_first_elem(root, ["sun_elevation", "sun_elevation_angle", "solar_elevation"])
                inc_elem = _find_first_elem(root, ["solar_incidence", "incidence_angle", "solar_incidence_angle"])
                em_elem = _find_first_elem(root, ["emission_angle"])
                phase_elem = _find_first_elem(root, ["phase_angle"])

                if inc_elem is not None and inc_elem.text:
                    try:
                        solar.incidence_angle_deg = float(inc_elem.text)
                        solar.status = ValueStatus.KNOWN
                    except ValueError:
                        pass
                if az_elem is not None and az_elem.text:
                    try:
                        solar.sun_azimuth_deg = float(az_elem.text)
                        solar.status = ValueStatus.KNOWN
                    except ValueError:
                        pass
                if el_elem is not None and el_elem.text:
                    try:
                        solar.sun_elevation_deg = float(el_elem.text)
                        solar.status = ValueStatus.KNOWN
                    except ValueError:
                        pass
                if em_elem is not None and em_elem.text:
                    try:
                        solar.emission_angle_deg = float(em_elem.text)
                        solar.status = ValueStatus.KNOWN
                    except ValueError:
                        pass
                if phase_elem is not None and phase_elem.text:
                    try:
                        solar.phase_angle_deg = float(phase_elem.text)
                        solar.status = ValueStatus.KNOWN
                    except ValueError:
                        pass

                # Extract Viewing Geometry conservatively
                alt_elem = _find_first_elem(root, ["spacecraft_altitude", "altitude"])
                if alt_elem is not None and alt_elem.text:
                    try:
                        view.spacecraft_altitude_km = float(alt_elem.text)
                        view.status = ValueStatus.KNOWN
                    except ValueError:
                        pass

                # Extract Geographic Footprint conservatively
                corner_lats: List[float] = []
                corner_lons: List[float] = []
                for lat_tag in ["upper_left_latitude", "upper_right_latitude", "lower_left_latitude", "lower_right_latitude"]:
                    e = _find_first_elem(root, [lat_tag])
                    if e is not None and e.text:
                        try:
                            corner_lats.append(float(e.text))
                        except ValueError:
                            pass
                for lon_tag in ["upper_left_longitude", "upper_right_longitude", "lower_left_longitude", "lower_right_longitude"]:
                    e = _find_first_elem(root, [lon_tag])
                    if e is not None and e.text:
                        try:
                            corner_lons.append(float(e.text))
                        except ValueError:
                            pass

                lat_min_e = _find_first_elem(root, ["minimum_latitude", "south_bounding_latitude"])
                lat_max_e = _find_first_elem(root, ["maximum_latitude", "north_bounding_latitude"])
                lon_min_e = _find_first_elem(root, ["westernmost_longitude", "west_bounding_longitude"])
                lon_max_e = _find_first_elem(root, ["easternmost_longitude", "east_bounding_longitude"])

                if corner_lats and corner_lons:
                    geo.lat_min = min(corner_lats)
                    geo.lat_max = max(corner_lats)
                    geo.lon_min = min(corner_lons)
                    geo.lon_max = max(corner_lons)
                    geo.status = ValueStatus.KNOWN
                else:
                    if lat_min_e is not None and lat_min_e.text:
                        try:
                            geo.lat_min = float(lat_min_e.text)
                            geo.status = ValueStatus.KNOWN
                        except ValueError:
                            pass
                    if lat_max_e is not None and lat_max_e.text:
                        try:
                            geo.lat_max = float(lat_max_e.text)
                        except ValueError:
                            pass
                    if lon_min_e is not None and lon_min_e.text:
                        try:
                            geo.lon_min = float(lon_min_e.text)
                        except ValueError:
                            pass
                    if lon_max_e is not None and lon_max_e.text:
                        try:
                            geo.lon_max = float(lon_max_e.text)
                        except ValueError:
                            pass

                proj_elem = _find_first_elem(root, ["projection", "coordinate_system_name", "reference_frame_id"])
                if proj_elem is not None and proj_elem.text:
                    geo.crs = proj_elem.text.strip()

                # Extract GSD / Pixel Resolution conservatively from label if present
                res_elem = _find_first_elem(root, ["pixel_resolution", "spatial_resolution", "map_scale"])
                if res_elem is not None and res_elem.text:
                    try:
                        gsd_m = float(res_elem.text)
                        statuses["gsd_m"] = ValueStatus.KNOWN
                    except ValueError:
                        pass

                # Extract Array Dimensions & Data Type from PDS4 Array structure
                arr_elem = root.find(".//Array_2D_Image") or root.find(".//Array_3D_Image") or root.find(".//Array_2D")
                if arr_elem is not None:
                    dt_elem = arr_elem.find(".//Element_Array/data_type") or arr_elem.find(".//data_type")
                    if dt_elem is not None and dt_elem.text:
                        data_type = dt_elem.text.strip()

                    for axis in arr_elem.findall(".//Axis_Array"):
                        name_e = axis.find("axis_name")
                        elem_e = axis.find("elements")
                        if name_e is not None and elem_e is not None and name_e.text and elem_e.text:
                            axis_n = name_e.text.strip().lower()
                            try:
                                cnt = int(elem_e.text.strip())
                                if "line" in axis_n:
                                    lines = cnt
                                elif "sample" in axis_n:
                                    samples = cnt
                                elif "band" in axis_n:
                                    num_bands = cnt
                            except ValueError:
                                pass

                # Extract Band Structure for IIRS/spectrometers
                band_elems = root.findall(".//Band_Bin") or root.findall(".//band")
                if band_elems:
                    num_bands = len(band_elems)
                    for idx, b in enumerate(band_elems):
                        w_elem = b.find("center_wavelength")
                        w_val = float(w_elem.text) if (w_elem is not None and w_elem.text) else None
                        bands.append(BandInfo(band_index=idx, band_name=f"Band_{idx+1}", center_wavelength_nm=w_val))

            except Exception as parse_err:
                raw_meta["pds4_parse_error"] = str(parse_err)

        # Infer instrument name conservatively from filename tokens if PDS4 label missing
        if instrument is None:
            name_upper = file_path.name.upper()
            if "OHRC" in name_upper or "_OHR_" in name_upper:
                instrument = "OHRC"
            elif "TMC2" in name_upper or "TMC-2" in name_upper or "_TMC_" in name_upper:
                instrument = "TMC-2"
            elif "IIRS" in name_upper or "_IIR_" in name_upper:
                instrument = "IIRS"

        # Explicit status marking
        statuses["solar_illumination"] = solar.status
        statuses["geographic_bounds"] = geo.status
        statuses["gsd_m"] = ValueStatus.KNOWN if gsd_m is not None else ValueStatus.UNKNOWN

        return ProductMetadata(
            product_id=product_id,
            mission=mission,
            instrument=instrument,
            product_type="Orbital Observation",
            processing_level=processing_level,
            acquisition_timestamp=acquisition_time,
            lines=lines,
            samples=samples,
            num_bands=num_bands,
            data_type=data_type,
            nodata_value=nodata_val,
            gsd_m=gsd_m,  # MUST remain None if not present in metadata!
            geographic_bounds=geo,
            solar_illumination=solar,
            viewing_geometry=view,
            bands=bands,
            value_statuses=statuses,
            raw_metadata=raw_meta,
        )

    def load_raster_data(self, file_path: Path, metadata: ProductMetadata) -> Tuple[Optional[np.ndarray], List[str]]:
        """Loads raster image file as numpy/memmap array preserving multi-band structure."""
        warnings: List[str] = []
        if file_path.suffix.lower() == ".xml":
            # Look for companion image file
            for ext in [".img", ".tif", ".tiff", ".png", ".jpg"]:
                companion = file_path.with_suffix(ext)
                if companion.exists():
                    file_path = companion
                    break

        if not file_path.exists() or file_path.suffix.lower() == ".xml":
            return None, ["Raster image file not found for PDS label"]

        try:
            # For raw PDS4 binary .img rasters
            if file_path.suffix.lower() == ".img":
                dt_map = {
                    "unsignedbyte": np.dtype("uint8"),
                    "uint8": np.dtype("uint8"),
                    "unsignedlsb2": np.dtype("<u2"),
                    "unsignedmsb2": np.dtype(">u2"),
                    "signedbyte": np.dtype("int8"),
                    "signedlsb2": np.dtype("<i2"),
                    "signedmsb2": np.dtype(">i2"),
                    "ieee754msbsingle": np.dtype(">f4"),
                    "ieee754lsbsingle": np.dtype("<f4"),
                }
                dt_key = metadata.data_type.lower() if metadata.data_type else "unsignedbyte"
                np_dtype = dt_map.get(dt_key, np.dtype("uint8"))

                if metadata.lines and metadata.samples:
                    shape = (metadata.lines, metadata.samples)
                    if metadata.num_bands > 1:
                        shape = (metadata.lines, metadata.samples, metadata.num_bands)
                    
                    file_size = file_path.stat().st_size
                    expected_size = int(np.prod(shape)) * np_dtype.itemsize
                    if file_size >= expected_size:
                        # Memory-mapped read for safe memory footprint
                        arr = np.memmap(file_path, dtype=np_dtype, mode="r", shape=shape)
                        return arr, warnings

            # Fallback to PIL Image open for standard formats
            img_pil = Image.open(file_path)
            arr = np.array(img_pil)

            metadata.lines = arr.shape[0]
            metadata.samples = arr.shape[1]
            if arr.ndim == 3:
                metadata.num_bands = arr.shape[2]
            else:
                metadata.num_bands = 1
            metadata.data_type = str(arr.dtype)

            return arr, warnings
        except Exception as e:
            warnings.append(f"Failed to read image raster: {str(e)}")
            return None, warnings
