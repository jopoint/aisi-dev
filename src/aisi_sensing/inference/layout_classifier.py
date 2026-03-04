from __future__ import annotations

from typing import Dict, Any
from .rulesets.default_rules import infer_layout
from ..core.types import FrameEvent


def classify(frame_event: FrameEvent, cfg: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Classify layout from a FrameEvent.

    Returns dict: {label, score, debug}
    """
    cfg = cfg or {}
    label, score, debug = infer_layout(frame_event, cfg)
    # Confidence gating
    min_conf = float((cfg or {}).get("features", {}).get("layout_min_confidence", 0.55))
    out = {"label": label, "score": float(score), "debug": dict(debug)}
    out["debug"]["chosen_before_gate"] = {"label": label, "score": float(score)}
    gated = False
    if score < min_conf:
        gated = True
        out["label"] = "unknown"
        out["score"] = float(score)
    out["debug"]["gated_to_unknown"] = gated
    return out
