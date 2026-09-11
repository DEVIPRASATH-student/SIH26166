"""SIFT Feature Matcher for Lunar Imagery."""

from typing import List, Tuple, Optional
import numpy as np
import cv2

from .base import BaseMatcher, MatchResult, KeypointFeature


class SIFTMatcher(BaseMatcher):
    """Scale-Invariant Feature Transform (SIFT) classical matcher with FLANN Lowe ratio test."""

    def __init__(
        self,
        n_features: int = 2000,
        contrast_threshold: float = 0.03,
        edge_threshold: float = 10.0,
        sigma: float = 1.6,
    ):
        super().__init__(name="SIFT")
        self.detector = cv2.SIFT_create(
            nfeatures=n_features,
            contrastThreshold=contrast_threshold,
            edgeThreshold=edge_threshold,
            sigma=sigma,
        )

        # FLANN index parameters for SIFT (KDTree)
        FLANN_INDEX_KDTREE = 1
        index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
        search_params = dict(checks=50)
        self.flann = cv2.FlannBasedMatcher(index_params, search_params)

    def _prepare_gray(self, img: np.ndarray) -> np.ndarray:
        if img.ndim == 3:
            if img.shape[2] == 3:
                return cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
            return img[:, :, 0]
        return img

    def extract_features(
        self, image: np.ndarray
    ) -> Tuple[List[KeypointFeature], np.ndarray]:
        gray = self._prepare_gray(image)
        # Apply CLAHE to enhance lunar shadow/ejecta contrast
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)

        cv_kps, desc = self.detector.detectAndCompute(enhanced, None)
        if cv_kps is None or desc is None or len(cv_kps) == 0:
            return [], np.zeros((0, 128), dtype=np.float32)

        kps = [
            KeypointFeature(
                x=kp.pt[0],
                y=kp.pt[1],
                size=kp.size,
                angle=kp.angle,
                response=kp.response,
                octave=kp.octave,
            )
            for kp in cv_kps
        ]
        return kps, desc

    def match(
        self,
        source_image: np.ndarray,
        target_image: np.ndarray,
        ratio_threshold: float = 0.80,
    ) -> MatchResult:
        gray_src = self._prepare_gray(source_image)
        gray_tgt = self._prepare_gray(target_image)

        kps1, desc1 = self.extract_features(gray_src)
        kps2, desc2 = self.extract_features(gray_tgt)

        if len(kps1) < 4 or len(kps2) < 4 or desc1.shape[0] < 4 or desc2.shape[0] < 4:
            return MatchResult(
                source_points=np.zeros((0, 2), dtype=np.float32),
                target_points=np.zeros((0, 2), dtype=np.float32),
                match_distances=np.zeros((0,), dtype=np.float32),
                raw_confidence=0.0,
                algorithm_name=self.name,
                metadata={"total_kps_src": len(kps1), "total_kps_tgt": len(kps2)},
            )

        # KNN matching with k=2 for Lowe's ratio test
        knn_matches = self.flann.knnMatch(desc1, desc2, k=2)

        good_src_pts = []
        good_tgt_pts = []
        distances = []

        for m_pair in knn_matches:
            if len(m_pair) == 2:
                m, n = m_pair
                if m.distance < ratio_threshold * n.distance:
                    kp1 = kps1[m.queryIdx]
                    kp2 = kps2[m.trainIdx]
                    good_src_pts.append([kp1.x, kp1.y])
                    good_tgt_pts.append([kp2.x, kp2.y])
                    distances.append(m.distance)

        if len(good_src_pts) == 0:
            return MatchResult(
                source_points=np.zeros((0, 2), dtype=np.float32),
                target_points=np.zeros((0, 2), dtype=np.float32),
                match_distances=np.zeros((0,), dtype=np.float32),
                raw_confidence=0.0,
                algorithm_name=self.name,
                metadata={"total_kps_src": len(kps1), "total_kps_tgt": len(kps2)},
            )

        src_arr = np.array(good_src_pts, dtype=np.float32)
        tgt_arr = np.array(good_tgt_pts, dtype=np.float32)
        dist_arr = np.array(distances, dtype=np.float32)

        # Raw confidence based on distance distribution and match volume
        avg_dist = float(np.mean(dist_arr))
        conf = float(np.clip(1.0 / (1.0 + avg_dist / 150.0), 0.0, 1.0))

        return MatchResult(
            source_points=src_arr,
            target_points=tgt_arr,
            match_distances=dist_arr,
            raw_confidence=conf,
            algorithm_name=self.name,
            metadata={
                "total_kps_src": len(kps1),
                "total_kps_tgt": len(kps2),
                "ratio_threshold": ratio_threshold,
                "avg_distance": avg_dist,
            },
        )
