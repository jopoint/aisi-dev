from __future__ import annotations

"""Export summary stats of classes over time to data/exports (skeleton)."""

import argparse
import json
import os
from typing import Dict, Any, Iterator

from ..core.logging import get_logger
from ..core.types import FrameEvent, DetectedEntity, Pose2D
from ..inference.layout_classifier import classify as classify_layout
from ..inference.social_classifier import classify as classify_social


def load_events(path: str) -> Iterator[FrameEvent]:
    if path.endswith(".jsonl"):
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                d = json.loads(line)
                yield dict_to_frame(d)
    else:
        with open(path, "r", encoding="utf-8") as f:
            d = json.loads(f.read())
            yield dict_to_frame(d)


def dict_to_frame(d: Dict[str, Any]) -> FrameEvent:
    furn = [DetectedEntity(id=e["id"], kind=e["kind"], pose=Pose2D(**e["pose"]), confidence=e.get("confidence")) for e in d.get("furniture", [])]
    peep = [DetectedEntity(id=e["id"], kind=e["kind"], pose=Pose2D(**e["pose"]), confidence=e.get("confidence")) for e in d.get("people", [])]
    return FrameEvent(timestamp_iso=d.get("timestamp_iso", ""), frame_id=int(d.get("frame_id", 0)), furniture=furn, people=peep, world=d.get("world", {}))


def main() -> None:
    logger = get_logger(__name__)
    parser = argparse.ArgumentParser()
    parser.add_argument("--events", required=True)
    parser.add_argument("--out", default="data/exports/summary.json")
    parser.add_argument("--classes", default="configs/classes.example.yaml")
    args = parser.parse_args()

    try:
        from ..core.config import load_yaml
        cfg = load_yaml(args.classes)
    except Exception:
        cfg = {}

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    timeline = []
    for ev in load_events(args.events):
        layout = classify_layout(ev, cfg)
        social = classify_social(ev, cfg)
        timeline.append({
            "timestamp_iso": ev.timestamp_iso,
            "frame_id": ev.frame_id,
            "layout": layout["label"],
            "layout_score": layout["score"],
            "social": social["label"],
            "social_score": social["score"],
        })

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump({"timeline": timeline}, f, indent=2)
    logger.info("Wrote export to %s", args.out)


if __name__ == "__main__":
    main()
