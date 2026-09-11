"""Physics Verification Engine.
The primary scientific gating layer of LunarSynapse.
Orchestrates Geometric, Illumination, Topographic, Scale, and Spatial verifiers.
Elevates visual correspondences into verified physical evidence.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
import numpy as np

from .geometry import GeometricVerifier, GeometryVerificationResult
from .illumination import IlluminationVerifier, IlluminationVerificationResult
from .terrain import TerrainVerifier, TerrainVerificationResult
from .scale_spatial import ScaleSpatialVerifier, ScaleSpatialResult
from ..matchers.base import MatchResult


@dataclass
class PhysicsEvidenceProfile:
    visual_score: float  # [0, 1] Raw matcher visual similarity
    geometry_score: float  # [0, 1] RANSAC inlier ratio & reprojection error
    illumination_score: float  # [0, 1] Solar ephemeris & shadow compatibility
    terrain_score: float  # [0, 1] DEM slope/roughness alignment
    scale_score: float  # [0, 1] Ground sampling distance consistency
    spatial_score: float  # [0, 1] Inlier convex hull coverage & entropy
    overall_confidence: float  # [0, 1] Composite scientific confidence
    status: str  # "VERIFIED", "UNCERTAIN", "REJECTED"
    rejection_reasons: List[str] = field(default_factory=list)
    geometry_result: Optional[GeometryVerificationResult] = None
    illumination_result: Optional[IlluminationVerificationResult] = None
    terrain_result: Optional[TerrainVerificationResult] = None
    scale_spatial_result: Optional[ScaleSpatialResult] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class PhysicsVerificationEngine:
    """Master physics verifier that checks physical plausibility of lunar correspondences."""

    def __init__(
        self,
        weights: Optional[Dict[str, float]] = None,
        verification_threshold: float = 0.72,
        rejection_threshold: float = 0.45,
    ):
        self.weights = weights or {
            "visual": 0.20,
            "geometry": 0.30,
            "illumination": 0.20,
            "terrain": 0.15,
            "scale": 0.08,
            "spatial": 0.07,
        }
        self.verification_threshold = verification_threshold
        self.rejection_threshold = rejection_threshold

        self.geo_verifier = GeometricVerifier()
        self.illum_verifier = IlluminationVerifier()
        self.terrain_verifier = TerrainVerifier()
        self.scale_spatial_verifier = ScaleSpatialVerifier()

    def verify_correspondence(
        self,
        src_image: np.ndarray,
        tgt_image: np.ndarray,
        src_meta: Dict[str, Any],
        tgt_meta: Dict[str, Any],
        match_result: MatchResult,
        src_dem: Optional[np.ndarray] = None,
        tgt_dem: Optional[np.ndarray] = None,
    ) -> PhysicsEvidenceProfile:
        """Runs the complete multi-pillar physics verification pipeline."""
        rejection_reasons: List[str] = []

        # 1. Raw Visual Score
        visual_score = float(np.clip(match_result.raw_confidence, 0.0, 1.0))
        if match_result.num_matches < 4:
            rejection_reasons.append("Insufficient candidate keypoint matches (N < 4)")
            return PhysicsEvidenceProfile(
                visual_score=visual_score,
                geometry_score=0.0,
                illumination_score=0.0,
                terrain_score=0.0,
                scale_score=0.0,
                spatial_score=0.0,
                overall_confidence=0.0,
                status="REJECTED",
                rejection_reasons=rejection_reasons,
                metadata={"total_matches": match_result.num_matches},
            )

        # 2. Geometric Verification
        geo_res = self.geo_verifier.verify(
            match_result.source_points,
            match_result.target_points,
            image_shape=src_image.shape[:2],
        )
        if not geo_res.is_valid:
            rejection_reasons.append(f"Geometric Failure: {geo_res.reason}")

        # 3. Solar Illumination Verification
        illum_res = self.illum_verifier.verify(
            src_image,
            tgt_image,
            src_meta,
            tgt_meta,
            transform_matrix=geo_res.transform_matrix,
        )
        if not illum_res.is_valid:
            rejection_reasons.append(f"Illumination Inconsistency: {illum_res.reason}")

        # 4. Topographic / Terrain Verification
        terrain_res = self.terrain_verifier.verify(
            src_image,
            tgt_image,
            match_result.source_points,
            match_result.target_points,
            inlier_mask=geo_res.inlier_mask,
            src_dem=src_dem,
            tgt_dem=tgt_dem,
        )
        if not terrain_res.is_valid:
            rejection_reasons.append(f"Terrain Inconsistency: {terrain_res.reason}")

        # 5. Scale & Spatial Distribution Verification
        src_res = float(src_meta.get("spatial_resolution_m", 0.5))
        tgt_res = float(tgt_meta.get("spatial_resolution_m", 5.0))
        scale_spatial_res = self.scale_spatial_verifier.verify(
            match_result.source_points,
            match_result.target_points,
            inlier_mask=geo_res.inlier_mask,
            src_res_m=src_res,
            tgt_res_m=tgt_res,
            transform_matrix=geo_res.transform_matrix,
            image_shape=src_image.shape[:2],
        )
        if not scale_spatial_res.is_valid:
            rejection_reasons.append(f"Scale/Spatial Anomaly: {scale_spatial_res.reason}")

        # 6. Weighted Composite Confidence
        composite_conf = float(
            self.weights["visual"] * visual_score
            + self.weights["geometry"] * geo_res.geometry_score
            + self.weights["illumination"] * illum_res.illumination_score
            + self.weights["terrain"] * terrain_res.terrain_score
            + self.weights["scale"] * scale_spatial_res.scale_score
            + self.weights["spatial"] * scale_spatial_res.spatial_score
        )

        # Critical Veto: If geometric verification fails completely, cap overall confidence
        if not geo_res.is_valid:
            composite_conf = min(composite_conf, 0.40)

        # Determine Final Status
        if composite_conf >= self.verification_threshold and len(rejection_reasons) == 0:
            status = "VERIFIED"
        elif composite_conf < self.rejection_threshold or len(rejection_reasons) >= 2:
            status = "REJECTED"
        else:
            status = "UNCERTAIN"

        return PhysicsEvidenceProfile(
            visual_score=round(visual_score, 4),
            geometry_score=round(geo_res.geometry_score, 4),
            illumination_score=round(illum_res.illumination_score, 4),
            terrain_score=round(terrain_res.terrain_score, 4),
            scale_score=round(scale_spatial_res.scale_score, 4),
            spatial_score=round(scale_spatial_res.spatial_score, 4),
            overall_confidence=round(composite_conf, 4),
            status=status,
            rejection_reasons=rejection_reasons,
            geometry_result=geo_res,
            illumination_result=illum_res,
            terrain_result=terrain_res,
            scale_spatial_result=scale_spatial_res,
            metadata={
                "algorithm": match_result.algorithm_name,
                "inlier_count": geo_res.num_inliers,
                "inlier_ratio": round(geo_res.inlier_ratio, 4),
                "mean_reprojection_error_px": round(geo_res.mean_reprojection_error_px, 3),
            },
        )
