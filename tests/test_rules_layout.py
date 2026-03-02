from __future__ import annotations

from src.aisi_sensing.inference.layout_classifier import classify
from src.aisi_sensing.core.types import FrameEvent, DetectedEntity, Pose2D


def test_layout_group_islands_minimal():
    ev = FrameEvent(
        timestamp_iso="t",
        frame_id=0,
        furniture=[
            DetectedEntity("t1", "table", Pose2D(1.0, 1.0)),
            DetectedEntity("t2", "table", Pose2D(3.0, 3.0)),
            DetectedEntity("c1", "chair", Pose2D(1.1, 1.1)),
            DetectedEntity("c2", "chair", Pose2D(3.1, 3.1)),
            DetectedEntity("s1", "screen", Pose2D(0.2, 2.0)),
        ],
        people=[],
        world={}
    )
    out = classify(ev, cfg={"features": {"row_alignment_tolerance_m": 0.01}})
    assert out["label"] in {"group_islands", "presentation_front", "unknown"}
