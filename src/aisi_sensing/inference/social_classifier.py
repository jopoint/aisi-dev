from __future__ import annotations

from typing import Dict, Any
from .rulesets.default_rules import infer_social
from ..core.types import FrameEvent


def classify(frame_event: FrameEvent, cfg: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Classify social constellation from a FrameEvent.

    Returns dict: {label, score, debug}
    """
    cfg = cfg or {}
    label, score, debug = infer_social(frame_event, cfg)
    return {"label": label, "score": float(score), "debug": debug}
