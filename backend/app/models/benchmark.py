"""Benchmark and Red Team Database Models."""

from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, DateTime, Text
from ..database.session import Base


class BenchmarkResultModel(Base):
    __tablename__ = "benchmark_results"

    id = Column(String(64), primary_key=True, index=True)
    scenario_id = Column(String(64), nullable=False)
    scenario_name = Column(String(128), nullable=False)
    algorithm_name = Column(String(64), nullable=False)

    candidate_matches = Column(Integer, default=0)
    inliers = Column(Integer, default=0)
    inlier_ratio = Column(Float, default=0.0)
    rmse = Column(Float, default=0.0)
    mean_reprojection_error_px = Column(Float, default=0.0)
    false_correspondence_rate = Column(Float, default=0.0)
    spatial_coverage = Column(Float, default=0.0)
    decision = Column(String(32), default="VERIFIED")

    created_at = Column(DateTime, default=datetime.utcnow)


class RedTeamResultModel(Base):
    __tablename__ = "red_team_results"

    id = Column(String(64), primary_key=True, index=True)
    test_id = Column(String(32), nullable=False)
    test_name = Column(String(128), nullable=False)
    attack_vector = Column(Text, nullable=False)

    raw_matcher_result = Column(String(128), nullable=False)
    physics_verification_result = Column(String(128), nullable=False)
    final_decision = Column(String(64), default="CORRECTLY_REJECTED")

    rejection_reasons_json = Column(Text, default="[]")
    evidence_breakdown_json = Column(Text, default="{}")
    explanation = Column(Text, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)
