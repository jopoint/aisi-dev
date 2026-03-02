from __future__ import annotations

from typing import List, Tuple
import math
from ...core.types import Pose2D, DetectedEntity


def marker_center_and_theta(corners: list[Tuple[float, float]]) -> Pose2D:
    """Compute approximate center (mean of corners) and orientation.

    Theta is estimated from the vector from corner[0] to corner[1].
    """
    xs = [p[0] for p in corners]
    ys = [p[1] for p in corners]
    cx = sum(xs) / len(xs)
    cy = sum(ys) / len(ys)
    dx = corners[1][0] - corners[0][0]
    dy = corners[1][1] - corners[0][1]
    theta = math.atan2(dy, dx)
    return Pose2D(x=float(cx), y=float(cy), theta=float(theta))


def detections_to_entities(detections: List[Tuple[int, list[Tuple[float, float]]]], kind_map: dict[int, str] | None = None) -> List[DetectedEntity]:
    """Convert ArUco detections into DetectedEntity with pixel Pose2D.

    kind_map can map marker ids to kinds (e.g., {10: 'table', 11: 'chair'}).
    Defaults to 'table' if unmapped.
    """
    entities: List[DetectedEntity] = []
    for mid, corners in detections:
        pose = marker_center_and_theta(corners)
        kind = kind_map.get(mid, "table") if kind_map else "table"
        entities.append(DetectedEntity(id=str(mid), kind=kind, pose=pose, confidence=1.0))
    return entities
