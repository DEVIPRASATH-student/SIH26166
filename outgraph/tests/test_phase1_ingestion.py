"""Phase 1 Test Suite: Real Lunar Data Foundation.
Tests Product Abstraction, Metadata Extraction, Missing Metadata (UNKNOWN/null),
NoData Handling, Data Validation, SHA256 Provenance Tracking, Synthetic vs Real Flagging,
Multi-Band IIRS Representation, and Observation Database / API Integration.
"""

import tempfile
from pathlib import Path
import numpy as np
from PIL import Image
import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from outgraph.ml.data.models import (
    LunarProduct,
    ProductMetadata,
    ValueStatus,
    NOMINAL_REFERENCE_SPECS,
)
from outgraph.ml.data.ingestion.factory import ProductIngestionEngine
from outgraph.ml.data.ingestion.issdc_adapter import ISSDCAdapter
from outgraph.ml.data.ingestion.lroc_adapter import LROCAdapter
from outgraph.ml.data.ingestion.selene_adapter import SELENEAdapter
from outgraph.ml.data.ingestion.generic_adapter import GenericAdapter
from outgraph.ml.data.validation.validator import ProductValidator
from outgraph.ml.data.provenance.tracker import ProvenanceTracker
from outgraph.ml.data.preprocessing.interface import SensorAwarePreprocessor
from outgraph.ml.data.fixtures.test_fixtures import (
    create_ohrc_test_fixture,
    create_tmc2_test_fixture,
    create_iirs_multiband_test_fixture,
)
from outgraph.backend.app.database.session import Base
from outgraph.backend.app.services.observation_service import ObservationService


@pytest.fixture
def temp_workspace():
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def in_memory_db():
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_ohrc_metadata_extraction_and_ingestion(temp_workspace):
    xml_path, img_path = create_ohrc_test_fixture(temp_workspace, "OHRC_TEST_01")
    engine = ProductIngestionEngine()
    product = engine.ingest_product(xml_path, source="ISSDC")

    assert isinstance(product, LunarProduct)
    assert product.is_synthetic is False  # Real product ingestion path
    assert product.product_id == "urn:isro:isda:ch2:ohrc:OHRC_TEST_01" or "OHRC_TEST_01" in product.product_id
    assert product.metadata.instrument == "OHRC"
    assert product.metadata.mission == "Chandrayaan-2"

    # Check GSD extracted directly from metadata
    assert product.metadata.gsd_m == 0.32
    assert product.metadata.value_statuses["gsd_m"] == ValueStatus.KNOWN

    # Check Solar Geometry extracted directly from metadata
    assert product.metadata.solar_illumination.sun_azimuth_deg == 42.5
    assert product.metadata.solar_illumination.sun_elevation_deg == 35.0

    # Check Geographic Footprint
    assert product.metadata.geographic_bounds.lat_min == -70.5
    assert product.metadata.geographic_bounds.lon_min == 22.8

    # Validation & Provenance
    assert product.validation.is_valid is True
    assert product.provenance.sha256_checksum is not None


def test_missing_metadata_handling_guardrail(temp_workspace):
    """MANDATORY GUARDRAIL TEST: Missing metadata MUST be represented as UNKNOWN/null.
    Nominal specs must NEVER overwrite missing GSD values or corrupt actual product metadata.
    """
    xml_path, img_path = create_tmc2_test_fixture(temp_workspace, "TMC2_NO_GSD_01")
    engine = ProductIngestionEngine()
    product = engine.ingest_product(xml_path, source="ISSDC")

    # Instrument identified, but GSD omitted from PDS label
    assert product.metadata.instrument == "TMC-2"
    assert product.metadata.gsd_m is None  # MUST NOT be overwritten with nominal 5.0m
    assert product.metadata.value_statuses["gsd_m"] == ValueStatus.UNKNOWN

    # Nominal specs exist strictly as reference documentation dictionary
    assert NOMINAL_REFERENCE_SPECS["TMC-2"]["nominal_gsd_m"] == 5.0
    # Confirm nominal reference dict did NOT overwrite product metadata
    assert product.metadata.gsd_m != NOMINAL_REFERENCE_SPECS["TMC-2"]["nominal_gsd_m"]


def test_iirs_multiband_spectral_representation(temp_workspace):
    """Test IIRS hyperspectral multi-band preservation without destructive grayscale conversion."""
    xml_path, img_path = create_iirs_multiband_test_fixture(temp_workspace, "IIRS_SPECTRAL_01")
    engine = ProductIngestionEngine()
    product = engine.ingest_product(xml_path, source="ISSDC")

    assert product.metadata.instrument == "IIRS"
    assert product.metadata.num_bands == 3
    assert len(product.metadata.bands) == 3
    assert product.metadata.bands[0].center_wavelength_nm == 850.0
    assert product.metadata.bands[2].center_wavelength_nm == 2800.0

    # Preserve 3D raster stack
    assert product.raster_data is not None
    assert product.raster_data.ndim == 3
    assert product.raster_data.shape[2] == 3

    # Test non-destructive correspondence view extraction
    view_2d, prod_ref = SensorAwarePreprocessor.extract_correspondence_ready_view(product, selected_band=1)
    assert view_2d.ndim == 2
    assert prod_ref.raster_data.shape[2] == 3  # Original multi-band raster untouched!


def test_lroc_nac_and_selene_adapters(temp_workspace):
    lroc_path = temp_workspace / "LROC_NAC_M100.png"
    selene_path = temp_workspace / "SELENE_TC_001.png"

    # Create dummy image files
    arr = np.random.randint(0, 255, size=(64, 64), dtype=np.uint8)
    Image.fromarray(arr).save(lroc_path)
    Image.fromarray(arr).save(selene_path)

    engine = ProductIngestionEngine()

    lroc_prod = engine.ingest_product(lroc_path, source="LROC")
    assert lroc_prod.metadata.instrument == "LROC NAC"

    selene_prod = engine.ingest_product(selene_path, source="SELENE")
    assert selene_prod.metadata.mission == "SELENE / Kaguya"


def test_sha256_provenance_tracking(temp_workspace):
    file_path = temp_workspace / "sample_raster.png"
    arr = np.ones((32, 32), dtype=np.uint8) * 128
    Image.fromarray(arr).save(file_path)

    checksum1 = ProvenanceTracker.calculate_sha256(file_path)
    assert checksum1 is not None
    assert len(checksum1) == 64

    # Re-calculate to verify deterministic hashing
    checksum2 = ProvenanceTracker.calculate_sha256(file_path)
    assert checksum1 == checksum2


def test_database_and_api_integration(temp_workspace, in_memory_db):
    xml_path, img_path = create_ohrc_test_fixture(temp_workspace, "OHRC_DB_TEST")
    obs_service = ObservationService(in_memory_db)

    obs_model = obs_service.ingest_real_product(file_path=str(xml_path), source="ISSDC")
    assert obs_model.id is not None
    assert obs_model.is_synthetic is False
    assert obs_model.sensor_type == "OHRC"
    assert obs_model.spatial_resolution_m == 0.32
    assert obs_model.product_id is not None

    # Retrieve from DB
    retrieved = obs_service.get_observation(obs_model.id)
    assert retrieved is not None
    assert retrieved.is_synthetic is False
