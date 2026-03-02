from __future__ import annotations

from typing import List, Tuple
from .geometry import distance


def cluster_points(points: List[Tuple[float, float]], threshold: float) -> List[List[int]]:
    """Cluster points using simple region-growing with distance threshold.

    Returns clusters as lists of point indices.
    """
    n = len(points)
    visited = [False] * n
    clusters: List[List[int]] = []
    for i in range(n):
        if visited[i]:
            continue
        # BFS/DFS from i
        stack = [i]
        cluster: List[int] = []
        visited[i] = True
        while stack:
            idx = stack.pop()
            cluster.append(idx)
            for j in range(n):
                if not visited[j] and distance(points[idx], points[j]) <= threshold:
                    visited[j] = True
                    stack.append(j)
        clusters.append(cluster)
    return clusters


def cluster_entities_xy(xys: List[Tuple[float, float]], threshold: float) -> List[List[int]]:
    return cluster_points(xys, threshold)
