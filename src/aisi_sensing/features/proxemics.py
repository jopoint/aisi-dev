from __future__ import annotations

from typing import Dict, List, Tuple
import statistics
from ..core.types import FrameEvent
from .clustering import cluster_points
from .geometry import distance


def people_clusters(frame: FrameEvent, threshold: float) -> List[List[int]]:
    people_xy = [(p.pose.x, p.pose.y) for p in frame.people]
    return cluster_points(people_xy, threshold) if people_xy else []


def cluster_centroids(points: List[Tuple[float, float]], clusters: List[List[int]]) -> List[Tuple[float, float]]:
    cents: List[Tuple[float, float]] = []
    for c in clusters:
        xs = [points[i][0] for i in c]
        ys = [points[i][1] for i in c]
        cents.append((sum(xs) / len(xs), sum(ys) / len(ys)))
    return cents


def relations_to_objects(points: List[Tuple[float, float]], objects: List[Tuple[str, Tuple[float, float]]], near_dist: float) -> Dict[str, int]:
    """Count how many points are near each object kind (aggregated)."""
    counts: Dict[str, int] = {}
    for pt in points:
        for kind, obj_pt in objects:
            if distance(pt, obj_pt) <= near_dist:
                counts[kind] = counts.get(kind, 0) + 1
    return counts


def circle_variance(points: List[Tuple[float, float]]) -> float:
    """Variance of distances to centroid; lower implies circular arrangement."""
    if not points:
        return 0.0
    cx = sum(p[0] for p in points) / len(points)
    cy = sum(p[1] for p in points) / len(points)
    dists = [((p[0] - cx) ** 2 + (p[1] - cy) ** 2) ** 0.5 for p in points]
    return statistics.pvariance(dists) if len(dists) > 1 else 0.0


def row_alignment_score(points: List[Tuple[float, float]]) -> float:
    """Return min variance across x or y to estimate row alignment (lower is better)."""
    if not points:
        return 0.0
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    vx = statistics.pvariance(xs) if len(xs) > 1 else 0.0
    vy = statistics.pvariance(ys) if len(ys) > 1 else 0.0
    return min(vx, vy)
