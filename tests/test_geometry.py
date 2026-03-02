from __future__ import annotations

from src.aisi_sensing.features.geometry import distance, k_nearest, within_bounds


def test_distance():
    assert abs(distance((0, 0), (3, 4)) - 5.0) < 1e-6


def test_k_nearest():
    pts = [(0, 0), (1, 0), (0, 1), (5, 5)]
    adj = k_nearest(pts, k=2)
    assert len(adj) == 4
    assert set(adj[0]) == {1, 2}


def test_within_bounds():
    b = (0.0, 0.0, 2.0, 2.0)
    assert within_bounds((1.0, 1.0), b)
    assert not within_bounds((3.0, 1.0), b)
