from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, List, Dict


@dataclass
class Pose2D:
    """2D pose with optional orientation.

    Units can be pixels or meters depending on stage. If homography is
    configured and applied, use meters in world coordinates.
    """
    x: float
    y: float
    theta: Optional[float] = None


@dataclass
class DetectedEntity:
    """A detected/tracked entity (furniture or person)."""
    id: str
    kind: str  # table, chair, screen, partition, person
    pose: Pose2D
    confidence: Optional[float] = None


@dataclass
class FrameEvent:
    """Sensing-to-inference contract for each frame.

    Attributes:
        timestamp_iso: ISO8601 timestamp string.
        frame_id: Monotonic frame index.
        furniture: List of detected furniture entities.
        people: List of detected person entities.
        world: Arbitrary dictionary for world metadata (bounds, homography id...).
    """
    timestamp_iso: str
    frame_id: int
    furniture: List[DetectedEntity]
    people: List[DetectedEntity]
    world: Dict

    def to_dict(self) -> dict:
        """Convert FrameEvent to a serializable dict."""
        return {
            'timestamp_iso': self.timestamp_iso,
            'frame_id': self.frame_id,
            'furniture': [
                {
                    'id': e.id,
                    'kind': e.kind,
                    'pose': {'x': e.pose.x, 'y': e.pose.y, 'theta': e.pose.theta},
                    'confidence': e.confidence,
                } for e in self.furniture
            ],
            'people': [
                {
                    'id': e.id,
                    'kind': e.kind,
                    'pose': {'x': e.pose.x, 'y': e.pose.y, 'theta': e.pose.theta},
                    'confidence': e.confidence,
                } for e in self.people
            ],
            'world': self.world,
        }

    @staticmethod
    def from_dict(d: dict) -> 'FrameEvent':
        """Create FrameEvent from dict."""
        def entity_from_dict(ed: dict) -> DetectedEntity:
            pose = Pose2D(
                x=ed['pose']['x'],
                y=ed['pose']['y'],
                theta=ed['pose'].get('theta'),
            )
            return DetectedEntity(
                id=ed['id'],
                kind=ed['kind'],
                pose=pose,
                confidence=ed.get('confidence'),
            )
        return FrameEvent(
            timestamp_iso=d['timestamp_iso'],
            frame_id=d['frame_id'],
            furniture=[entity_from_dict(e) for e in d.get('furniture', [])],
            people=[entity_from_dict(e) for e in d.get('people', [])],
            world=d.get('world', {}),
        )
