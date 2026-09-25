"""Observation Database Model."""

from datetime import datetime
from sqlalchemy import Column, String, Float, Boolean, DateTime, Text
from ..database.session import Base


class ObservationModel(Base):
    __tablename__ = "observations"

    id = Column(String(64), primary_key=True, index=True)
    sensor_type = Column(String(32), nullable=False, index=True)  # OHRC, TMC-2, IIRS
    image_path = Column(String(256), nullable=False)
    raw_path = Column(String(256), nullable=True)
    acquisition_timestamp = Column(DateTime, default=datetime.utcnow)

    lat_min = Column(Float, nullable=False)
    lat_max = Column(Float, nullable=False)
    lon_min = Column(Float, nullable=False)
    lon_max = Column(Float, nullable=False)
    spatial_resolution_m = Column(Float, nullable=False)

    sun_azimuth_deg = Column(Float, nullable=False)
    sun_elevation_deg = Column(Float, nullable=False)
    incidence_angle_deg = Column(Float, nullable=False)
    emission_angle_deg = Column(Float, nullable=False)
    phase_angle_deg = Column(Float, nullable=False)

    metadata_json = Column(Text, default="{}")
    preprocessing_history = Column(Text, default="[]")
    is_synthetic = Column(Boolean, default=True)

    # Real Product Extensions (Phase 1)
    product_id = Column(String(128), nullable=True)
    mission = Column(String(64), nullable=True)
    instrument = Column(String(64), nullable=True)
    product_type = Column(String(64), nullable=True)
    processing_level = Column(String(32), nullable=True)
    num_bands = Column(Float, default=1.0)
    data_type = Column(String(32), default="uint8")
    nodata_value = Column(Float, nullable=True)
    provenance_json = Column(Text, default="{}")
    metadata_source_json = Column(Text, default="{}")

    created_at = Column(DateTime, default=datetime.utcnow)

