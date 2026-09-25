"""Enhanced Correlation Coefficient (ECC) & Phase Correlation Sub-Pixel Refiner.
Performs intensity-invariant sub-pixel alignment of lunar observations.
"""

from dataclasses import dataclass
from typing import Optional, Tuple
import numpy as np
import cv2


@dataclass
class SubPixelResult:
    refined_warp_matrix: np.ndarray
    final_correlation: float
    subpixel_displacement_px: float
    iterations: int
    converged: bool


class ECCRefiner:
    """Sub-pixel optimization engine using parametric image alignment (ECC)."""

    def __init__(self, max_iterations: int = 40, termination_eps: float = 1e-4):
        self.max_iterations = max_iterations
        self.termination_eps = termination_eps

    def _to_gray_f32(self, img: np.ndarray) -> np.ndarray:
        if img.ndim == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY) if img.shape[2] == 3 else img[:, :, 0]
        else:
            gray = img
        return gray.astype(np.float32) / 255.0

    def refine_affine(
        self,
        src_image: np.ndarray,
        tgt_image: np.ndarray,
        initial_affine_2x3: Optional[np.ndarray] = None,
    ) -> SubPixelResult:
        """Refines affine transformation matrix using iterative ECC optimization."""
        src_f = self._to_gray_f32(src_image)
        tgt_f = self._to_gray_f32(tgt_image)

        if initial_affine_2x3 is None:
            warp_matrix = np.eye(2, 3, dtype=np.float32)
        else:
            warp_matrix = initial_affine_2x3[:2, :3].astype(np.float32).copy()

        criteria = (
            cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT,
            self.max_iterations,
            self.termination_eps,
        )

        try:
            # Find transform using ECC
            cc, refined_warp = cv2.findTransformECC(
                templateImage=src_f,
                inputImage=tgt_f,
                warpMatrix=warp_matrix,
                motionType=cv2.MOTION_AFFINE,
                criteria=criteria,
            )
            # Estimate subpixel shift offset magnitude
            disp = float(np.linalg.norm(refined_warp[:, 2] - warp_matrix[:, 2]))
            return SubPixelResult(
                refined_warp_matrix=refined_warp,
                final_correlation=float(cc),
                subpixel_displacement_px=disp,
                iterations=self.max_iterations,
                converged=True,
            )
        except cv2.error:
            # If standard ECC fails due to ill-conditioned gradient, fall back to initial with phase correlation
            shift, response = cv2.phaseCorrelate(src_f, tgt_f)
            fallback_warp = warp_matrix.copy()
            fallback_warp[0, 2] += shift[0] * 0.1
            fallback_warp[1, 2] += shift[1] * 0.1
            return SubPixelResult(
                refined_warp_matrix=fallback_warp,
                final_correlation=float(response),
                subpixel_displacement_px=float(np.linalg.norm(shift) * 0.1),
                iterations=1,
                converged=False,
            )
