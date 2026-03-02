from __future__ import annotations

from typing import List, Tuple
import math


def distance(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def k_nearest(points: List[Tuple[float, float]], k: int = 3) -> List[List[int]]:
    """Return adjacency indices for each point to k nearest neighbors (excluding self)."""
    n = len(points)
    adj: List[List[int]] = [[] for _ in range(n)]
    for i in range(n):
        dists = [(distance(points[i], points[j]), j) for j in range(n) if j != i]
        dists.sort(key=lambda x: x[0])
        adj[i] = [j for _, j in dists[:k]]
    return adj


def within_bounds(pt: Tuple[float, float], bounds: Tuple[float, float, float, float]) -> bool:
    x, y = pt
    min_x, min_y, max_x, max_y = bounds
    return (min_x <= x <= max_x) and (min_y <= y <= max_y)
