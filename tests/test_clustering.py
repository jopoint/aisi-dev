from __future__ import annotations

from src.aisi_sensing.features.clustering import cluster_points


def test_cluster_points_threshold():
    pts = [(0, 0), (0.5, 0.2), (3, 3), (3.2, 3.1)]
    clusters = cluster_points(pts, threshold=0.6)
    sizes = sorted(len(c) for c in clusters)
    assert sizes == [2, 2]
