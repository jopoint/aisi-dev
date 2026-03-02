from __future__ import annotations

from typing import Iterable, Optional, Tuple
import numpy as np
from ...core.types import Pose2D


def apply_homography(pt: Tuple[float, float], H: np.ndarray) -> Tuple[float, float]:
    """Apply a 3x3 homography to a 2D point (x,y)."""
    x, y = pt
    v = np.array([x, y, 1.0], dtype=float)
    w = H @ v
    if w[2] == 0:
        return float(w[0]), float(w[1])
    return float(w[0] / w[2]), float(w[1] / w[2])


def map_pose_with_h(p: Pose2D, H: Optional[np.ndarray]) -> Pose2D:
    """Map a pose using homography if provided. Theta is unchanged."""
    if H is None:
        return p
    x, y = apply_homography((p.x, p.y), H)
    return Pose2D(x=x, y=y, theta=p.theta)


def map_points_with_h(points: Iterable[Tuple[float, float]], H: Optional[np.ndarray]) -> list[Tuple[float, float]]:
    return [apply_homography(pt, H) if H is not None else pt for pt in points]
