from __future__ import annotations

from typing import Dict
from ..core.types import DetectedEntity, Pose2D


class EMAFilter:
    """Exponential Moving Average filter for smoothing 2D poses per entity id."""

    def __init__(self, alpha: float = 0.5) -> None:
        self.alpha = alpha
        self.state: Dict[str, Pose2D] = {}

    def update(self, e: DetectedEntity) -> DetectedEntity:
        prev = self.state.get(e.id)
        if prev is None:
            self.state[e.id] = e.pose
            return e
        a = self.alpha
        new_pose = Pose2D(
            x=a * e.pose.x + (1 - a) * prev.x,
            y=a * e.pose.y + (1 - a) * prev.y,
            theta=e.pose.theta if e.pose.theta is not None else prev.theta,
        )
        self.state[e.id] = new_pose
        return DetectedEntity(id=e.id, kind=e.kind, pose=new_pose, confidence=e.confidence)
