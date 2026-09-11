"""Correspondence Database Model."""

from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, DateTime, Text, ForeignKey
from ..database.session import Base


class CorrespondenceModel(Base):
    __tablename__ = "correspondences"

    id = Column(String(64), primary_key=True, index=True)
    source_observation_id = Column(String(64), ForeignKey("observations.id"), nullable=False, index=True)
    target_observation_id = Column(String(64), ForeignKey("observations.id"), nullable=False, index=True)

    matcher_algorithm = Column(String(32), default="SIFT")
    num_candidate_matches = Column(Integer, default=0)
    num_inliers = Column(Integer, default=0)
    inlier_ratio = Column(Float, default=0.0)

    visual_confidence = Column(Float, default=0.0)
    overall_confidence = Column(Float, default=0.0)
    status = Column(String(32), default="UNCERTAIN", index=True)  # VERIFIED, UNCERTAIN, REJECTED

    matches_data_json = Column(Text, default="{}")  # Serialized 2D keypoints and inlier indices
    created_at = Column(DateTime, default=datetime.utcnow)
