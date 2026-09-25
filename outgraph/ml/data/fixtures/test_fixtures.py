"""Test Fixture Generator for Scientific Product Ingestion Tests.
Generates controlled PDS4 XML labels and scientific raster files for testing.
All generated test fixtures are explicitly tagged as TEST FIXTURES / SYNTHETIC DATA.
"""

from pathlib import Path
from typing import Tuple
import numpy as np
from PIL import Image


def create_ohrc_test_fixture(target_dir: Path, product_id: str = "OHRC_TEST_001") -> Tuple[Path, Path]:
    """Generates an OHRC-like PDS4 XML label and associated panchromatic image fixture."""
    target_dir.mkdir(parents=True, exist_ok=True)
    xml_path = target_dir / f"{product_id}.xml"
    img_path = target_dir / f"{product_id}.png"

    # Create PDS4 XML Label with known solar and geographic fields
    xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<Product_Observational xmlns="http://pds.nasa.gov/pds4/pds/v1">
    <Identification_Area>
        <logical_identifier>urn:isro:isda:ch2:ohrc:{product_id}</logical_identifier>
        <title>Chandrayaan-2 OHRC Test Observation Fixture</title>
        <product_class>Product_Observational</product_class>
    </Identification_Area>
    <Observation_Area>
        <comment>TEST FIXTURE ONLY - Explicitly synthetic test data</comment>
        <Investigation_Area>
            <name>Chandrayaan-2</name>
            <type>Mission</type>
        </Investigation_Area>
        <Observing_System>
            <Observing_System_Component>
                <name>Orbiter High Resolution Camera</name>
                <type>Instrument</type>
                <instrument_id>OHRC</instrument_id>
            </Observing_System_Component>
        </Observing_System>
        <Target_Identification>
            <name>Moon</name>
            <type>Satellite</type>
        </Target_Identification>
        <Discipline_Area>
            <Illumination_Geometry>
                <sun_azimuth_angle unit="deg">42.5</sun_azimuth_angle>
                <sun_elevation_angle unit="deg">35.0</sun_elevation_angle>
                <incidence_angle unit="deg">55.0</incidence_angle>
            </Illumination_Geometry>
            <Target_Position>
                <minimum_latitude unit="deg">-70.5</minimum_latitude>
                <maximum_latitude unit="deg">-70.4</maximum_latitude>
                <westernmost_longitude unit="deg">22.8</westernmost_longitude>
                <easternmost_longitude unit="deg">22.9</easternmost_longitude>
            </Target_Position>
            <Spatial_Resolution>
                <pixel_resolution unit="m">0.32</pixel_resolution>
            </Spatial_Resolution>
        </Discipline_Area>
    </Observation_Area>
</Product_Observational>
"""
    with open(xml_path, "w", encoding="utf-8") as f:
        f.write(xml_content)

    # Synthetic image raster
    arr = np.random.randint(20, 240, size=(256, 256), dtype=np.uint8)
    Image.fromarray(arr).save(img_path)

    return xml_path, img_path


def create_tmc2_test_fixture(target_dir: Path, product_id: str = "TMC2_TEST_001") -> Tuple[Path, Path]:
    """Generates a TMC-2-like test fixture with missing GSD to test UNKNOWN resolution handling."""
    target_dir.mkdir(parents=True, exist_ok=True)
    xml_path = target_dir / f"{product_id}.xml"
    img_path = target_dir / f"{product_id}.png"

    # XML label deliberately omitting spatial_resolution / pixel_resolution
    xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<Product_Observational xmlns="http://pds.nasa.gov/pds4/pds/v1">
    <Identification_Area>
        <logical_identifier>urn:isro:isda:ch2:tmc2:{product_id}</logical_identifier>
        <title>Chandrayaan-2 TMC-2 Test Observation Fixture</title>
    </Identification_Area>
    <Observation_Area>
        <Observing_System>
            <Observing_System_Component>
                <name>Terrain Mapping Camera 2</name>
                <type>Instrument</type>
                <instrument_id>TMC-2</instrument_id>
            </Observing_System_Component>
        </Observing_System>
        <Discipline_Area>
            <Illumination_Geometry>
                <sun_azimuth_angle unit="deg">65.0</sun_azimuth_angle>
                <sun_elevation_angle unit="deg">30.0</sun_elevation_angle>
            </Illumination_Geometry>
        </Discipline_Area>
    </Observation_Area>
</Product_Observational>
"""
    with open(xml_path, "w", encoding="utf-8") as f:
        f.write(xml_content)

    arr = np.random.randint(10, 250, size=(128, 128), dtype=np.uint8)
    Image.fromarray(arr).save(img_path)

    return xml_path, img_path


def create_iirs_multiband_test_fixture(target_dir: Path, product_id: str = "IIRS_TEST_001") -> Tuple[Path, Path]:
    """Generates an IIRS-like multi-band / hyperspectral product fixture with spectral band metadata."""
    target_dir.mkdir(parents=True, exist_ok=True)
    xml_path = target_dir / f"{product_id}.xml"
    img_path = target_dir / f"{product_id}.tif"

    xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<Product_Observational xmlns="http://pds.nasa.gov/pds4/pds/v1">
    <Identification_Area>
        <logical_identifier>urn:isro:isda:ch2:iirs:{product_id}</logical_identifier>
        <title>Chandrayaan-2 IIRS Hyperspectral Test Fixture</title>
    </Identification_Area>
    <Observation_Area>
        <Observing_System>
            <Observing_System_Component>
                <name>Imaging Infrared Spectrometer</name>
                <type>Instrument</type>
                <instrument_id>IIRS</instrument_id>
            </Observing_System_Component>
        </Observing_System>
        <Discipline_Area>
            <Band_Bin>
                <center_wavelength unit="nm">850.0</center_wavelength>
            </Band_Bin>
            <Band_Bin>
                <center_wavelength unit="nm">1250.0</center_wavelength>
            </Band_Bin>
            <Band_Bin>
                <center_wavelength unit="nm">2800.0</center_wavelength>
            </Band_Bin>
        </Discipline_Area>
    </Observation_Area>
</Product_Observational>
"""
    with open(xml_path, "w", encoding="utf-8") as f:
        f.write(xml_content)

    # 3-band spectral array
    band1 = np.random.randint(50, 200, size=(100, 100), dtype=np.uint8)
    band2 = np.random.randint(30, 220, size=(100, 100), dtype=np.uint8)
    band3 = np.random.randint(10, 180, size=(100, 100), dtype=np.uint8)
    multiband = np.stack([band1, band2, band3], axis=-1)

    Image.fromarray(multiband).save(img_path)

    return xml_path, img_path


def create_mock_ohrc_pds4_product(product_id: str = "OHRC_TEST_001") -> "LunarProduct":
    from outgraph.ml.data.models import (
        LunarProduct, ProductMetadata, ProvenanceRecord, ValidationResult, ValueStatus, SolarIllumination, GeographicBounds
    )
    meta = ProductMetadata(
        product_id=product_id,
        mission="Chandrayaan-2",
        instrument="Orbiter High Resolution Camera",
        data_type="uint8",
        gsd_m=0.32,
        solar_illumination=SolarIllumination(sun_azimuth_deg=45.0, sun_elevation_deg=35.0, status=ValueStatus.KNOWN),
        geographic_bounds=GeographicBounds(lat_min=-70.5, lat_max=-70.4, lon_min=22.8, lon_max=22.9, status=ValueStatus.KNOWN),
        value_statuses={"gsd_m": ValueStatus.KNOWN},
    )
    prov = ProvenanceRecord(source_name="ISSDC", original_filename=f"{product_id}.xml", product_id=product_id)
    val = ValidationResult(is_valid=True)
    raster = np.random.randint(10, 240, size=(256, 256), dtype=np.uint8)

    return LunarProduct(
        product_id=product_id,
        file_path=f"mock/{product_id}.xml",
        metadata=meta,
        provenance=prov,
        validation=val,
        raster_data=raster,
        is_synthetic=False,
    )


def create_mock_iirs_pds4_product(product_id: str = "IIRS_TEST_001") -> "LunarProduct":
    from outgraph.ml.data.models import (
        LunarProduct, ProductMetadata, ProvenanceRecord, ValidationResult, ValueStatus, BandInfo
    )
    meta = ProductMetadata(
        product_id=product_id,
        mission="Chandrayaan-2",
        instrument="Imaging Infrared Spectrometer",
        num_bands=3,
        bands=[
            BandInfo(band_index=0, center_wavelength_nm=850.0),
            BandInfo(band_index=1, center_wavelength_nm=1250.0),
            BandInfo(band_index=2, center_wavelength_nm=2800.0),
        ],
        value_statuses={"gsd_m": ValueStatus.UNKNOWN},
    )
    prov = ProvenanceRecord(source_name="ISSDC", original_filename=f"{product_id}.xml", product_id=product_id)
    val = ValidationResult(is_valid=True)
    raster = np.random.randint(10, 240, size=(100, 100, 3), dtype=np.uint8)

    return LunarProduct(
        product_id=product_id,
        file_path=f"mock/{product_id}.xml",
        metadata=meta,
        provenance=prov,
        validation=val,
        raster_data=raster,
        is_synthetic=False,
    )

