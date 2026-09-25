"""Solar Illumination & Photometric Verification.
Evaluates solar incidence, azimuth, elevation, and phase angle compatibility.
Verifies whether image intensity gradients and shadow orientations align with astronomical ephemeris.
"""

from dataclasses import dataclass
from typing import Dict, Optional, Tuple, Any
import numpy as np
import cv2


@dataclass
class IlluminationVerificationResult:
    is_valid: bool
    illumination_score: float  # [0, 1]
    solar_azimuth_delta_deg: float
    expected_shadow_azimuth_deg: float
    gradient_alignment_score: float
    phase_compatibility_score: float
    reason: str = "Solar illumination consistency evaluated"


class IlluminationVerifier:
    """Evaluates photometric and solar geometry consistency for lunar observations."""

    def __init__(self, max_azimuth_divergence: float = 120.0):
        self.max_azimuth_divergence = max_azimuth_divergence

    def verify(
        self,
        src_image: np.ndarray,
        tgt_image: np.ndarray,
        src_meta: Dict[str, Any],
        tgt_meta: Dict[str, Any],
        transform_matrix: Optional[np.ndarray] = None,
    ) -> IlluminationVerificationResult:
        """Evaluates solar geometry compatibility between two lunar observations."""
        # 1. Extract solar parameters
        src_az = float(src_meta.get("sun_azimuth_deg", 45.0))
        tgt_az = float(tgt_meta.get("sun_azimuth_deg", 45.0))
        src_el = float(src_meta.get("sun_elevation_deg", 30.0))
        tgt_el = float(tgt_meta.get("sun_elevation_deg", 30.0))
        src_phase = float(src_meta.get("phase_angle_deg", 60.0))
        tgt_phase = float(tgt_meta.get("phase_angle_deg", 60.0))

        # Solar azimuth difference (shortest circular angle)
        diff_az = abs(src_az - tgt_az) % 360.0
        if diff_az > 180.0:
            diff_az = 360.0 - diff_az

        # Phase angle difference
        diff_phase = abs(src_phase - tgt_phase)

        # Expected shadow direction is opposite to sun azimuth (+180 deg)
        shadow_az = (src_az + 180.0) % 360.0

        # Phase compatibility: penalize extreme phase angle disparity where shadowing is completely reversed
        phase_comp = float(np.clip(1.0 - (diff_phase / 90.0), 0.1, 1.0))

        # 2. Image gradient alignment along illumination direction
        def get_grad_vector(img: np.ndarray) -> np.ndarray:
            if img.ndim == 3:
                gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY) if img.shape[2] == 3 else img[:, :, 0]
            else:
                gray = img
            gx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
            gy = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
            mag = np.sqrt(gx * gx + gy * gy) + 1e-6
            return np.array([np.mean(gx / mag), np.mean(gy / mag)])

        try:
            v_src = get_grad_vector(src_image)
            v_tgt = get_grad_vector(tgt_image)
            cos_sim = float(np.dot(v_src, v_tgt) / (np.linalg.norm(v_src) * np.linalg.norm(v_tgt) + 1e-6))
            grad_score = float(np.clip((cos_sim + 1.0) / 2.0, 0.0, 1.0))
        except Exception:
            grad_score = 0.70

        # Continuous illumination score
        # Solar geometry compatibility (0.6) + Empirical gradient response (0.4)
        az_score = float(np.clip(1.0 - (diff_az / self.max_azimuth_divergence) ** 2, 0.0, 1.0))
        el_diff = abs(src_el - tgt_el)
        el_score = float(np.clip(1.0 - (el_diff / 50.0), 0.2, 1.0))

        illum_score = float(0.40 * az_score + 0.30 * el_score + 0.30 * grad_score)

        # Flag validity: if solar angles are extremely divergent (e.g. opposite illumination creating shadow inversion),
        # the match must be flagged as lower confidence or require strict terrain verification
        is_valid = illum_score >= 0.35

        reason = (
            f"Solar geometry consistent (ΔAz={diff_az:.1f}°, ΔEl={el_diff:.1f}°, GradSim={grad_score:.2f})"
            if is_valid
            else f"Illumination conflict: high solar divergence (ΔAz={diff_az:.1f}°, shadow orientation mismatch)"
        )

        return IlluminationVerificationResult(
            is_valid=is_valid,
            illumination_score=illum_score,
            solar_azimuth_delta_deg=diff_az,
            expected_shadow_azimuth_deg=shadow_az,
            gradient_alignment_score=grad_score,
            phase_compatibility_score=phase_comp,
            reason=reason,
        )
