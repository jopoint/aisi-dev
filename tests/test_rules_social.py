from __future__ import annotations

from src.aisi_sensing.inference.social_classifier import classify
from src.aisi_sensing.core.types import FrameEvent, DetectedEntity, Pose2D


def test_social_one_to_one():
    ev = FrameEvent(
        timestamp_iso="t",
        frame_id=0,
        furniture=[],
        people=[
            DetectedEntity("p1", "person", Pose2D(1.0, 1.0)),
            DetectedEntity("p2", "person", Pose2D(1.3, 1.1)),
        ],
        world={}
    )
    out = classify(ev, cfg={"features": {"clustering_distance_m": 0.5}})
    assert out["label"] == "one_to_one"
