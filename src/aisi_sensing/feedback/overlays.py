from __future__ import annotations

from typing import List, Tuple
import numpy as np

from ..core.types import DetectedEntity


def draw_entities(image: np.ndarray, furniture: List[DetectedEntity], people: List[DetectedEntity]) -> np.ndarray:
    """Draw simple circles and labels for entities on an RGB image (numpy array)."""
    try:
        import cv2  # type: ignore
    except Exception:
        # Fallback: return image unchanged
        return image
    out = image.copy()
    for e in furniture:
        color = (0, 200, 0) if e.kind == "table" else (0, 150, 200)
        cv2.circle(out, (int(e.pose.x), int(e.pose.y)), 8, color, -1)
        cv2.putText(out, f"{e.kind}:{e.id}", (int(e.pose.x) + 6, int(e.pose.y) - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
    for p in people:
        color = (220, 50, 50)
        cv2.circle(out, (int(p.pose.x), int(p.pose.y)), 6, color, -1)
        cv2.putText(out, f"P:{p.id}", (int(p.pose.x) + 6, int(p.pose.y) - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
    return out
