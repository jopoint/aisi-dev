from __future__ import annotations

from typing import Dict, List
import math
from ..core.types import DetectedEntity, Pose2D


def _dist(a: Pose2D, b: Pose2D) -> float:
    return math.hypot(a.x - b.x, a.y - b.y)


class NaiveAssociator:
    """Naive ID stabilization using nearest-neighbor to previous entities by kind.

    If entities already have stable IDs (e.g., ArUco), they are preserved.
    For entities without IDs, assigns stable IDs per kind across frames.
    """

    def __init__(self, max_match_distance: float = 50.0) -> None:
        self.prev: Dict[str, List[DetectedEntity]] = {}
        self.counters: Dict[str, int] = {}
        self.max_match_distance = max_match_distance

    def update(self, entities: List[DetectedEntity]) -> List[DetectedEntity]:
        by_kind: Dict[str, List[DetectedEntity]] = {}
        for e in entities:
            by_kind.setdefault(e.kind, []).append(e)
        stabilized: List[DetectedEntity] = []
        for kind, cur in by_kind.items():
            prev = self.prev.get(kind, [])
            used_prev: set[int] = set()
            for e in cur:
                # Keep existing ID if looks like an ArUco/explicit id
                if e.id and e.id != "":
                    stabilized.append(e)
                    continue
                # Find nearest previous unmatched
                best_i = -1
                best_d = float("inf")
                for i, p in enumerate(prev):
                    if i in used_prev:
                        continue
                    d = _dist(e.pose, p.pose)
                    if d < best_d and d <= self.max_match_distance:
                        best_d = d
                        best_i = i
                if best_i >= 0:
                    used_prev.add(best_i)
                    assigned_id = prev[best_i].id
                else:
                    c = self.counters.get(kind, 0) + 1
                    self.counters[kind] = c
                    assigned_id = f"{kind}-{c}"
                stabilized.append(DetectedEntity(id=assigned_id, kind=kind, pose=e.pose, confidence=e.confidence))
            self.prev[kind] = stabilized.copy()
        return stabilized
