"""Physics Evidence & Sub-Pixel Registration Experiment Models."""

from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, Text, ForeignKey
from ..database.session import Base


class CorrespondenceEvidenceModel(Base):
    __tablename__ = "correspondence_evidence"

    id = Column(String(64), primary_key=True, index=True)
    correspondence_id = Column(String(64), ForeignKey("correspondences.id"), nullable=False, unique=True, index=True)

    visual_score = Column(Float, default=0.0)
    geometry_score = Column(Float, default=0.0)
    illumination_score = Column(Float, default=0.0)
    terrain_score = Column(Float, default=0.0)
    scale_score = Column(Float, default=0.0)
    spatial_score = Column(Float, default=0.0)

    mean_reprojection_error_px = Column(Float, default=0.0)
    condition_number = Column(Float, default=1.0)

    # Uncertainty decomposition
    total_uncertainty = Column(Float, default=0.5)
    evidence_disagreement = Column(Float, default=0.0)
    geometric_instability = Column(Float, default=0.0)
    feature_ambiguity = Column(Float, default=0.0)
    spatial_sparsity = Column(Float, default=0.0)
    calibration_status = Column(String(64), default="CALIBRATED")

    rejection_reasons_json = Column(Text, default="[]")
    created_at = Column(DateTime, default=datetime.utcnow)


class RegistrationExperimentModel(Base):
    __tablename__ = "registration_experiments"

    id = Column(String(64), primary_key=True, index=True)
    correspondence_id = Column(String(64), ForeignKey("correspondences.id"), nullable=False, index=True)

    is_success = Column(Boolean, default=False)
    transformation_matrix_json = Column(Text, default="[]")
    registered_image_path = Column(String(256), nullable=True)
    difference_image_path = Column(String(256), nullable=True)

    rmse = Column(Float, default=0.0)
    subpixel_error_px = Column(Float, default=0.0)
    inlier_ratio = Column(Float, default=0.0)
    spatial_coverage = Column(Float, default=0.0)
    algorithm = Column(String(32), default="SIFT")

    metadata_json = Column(Text, default="{}")
    created_at = Column(DateTime, default=datetime.utcnow)
