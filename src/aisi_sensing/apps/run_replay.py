from __future__ import annotations

"""Replay recorded FrameEvents and show overlays/classifications.

This path is runnable end-to-end using the provided example JSON.
"""

import argparse
import json
from typing import Iterable, Iterator, Dict, Any

from ..core.logging import get_logger
from ..core.types import FrameEvent, DetectedEntity, Pose2D
from ..inference.layout_classifier import classify as classify_layout
from ..inference.social_classifier import classify as classify_social
from ..feedback.floorplan_render import render_topdown


from pathlib import Path
from ..core.logging import iter_jsonl

def load_events(path: str) -> Iterator[FrameEvent]:
    p = Path(path).expanduser().resolve()
    if p.is_dir():
        jsonl_path = p / "events.jsonl"
        if not jsonl_path.exists():
            raise FileNotFoundError(f"No events.jsonl in {p}")
        for d in iter_jsonl(jsonl_path):
            yield FrameEvent.from_dict(d)
    elif p.suffix == ".jsonl":
        for d in iter_jsonl(p):
            yield FrameEvent.from_dict(d)
    elif p.suffix == ".json":
        with p.open("r", encoding="utf-8") as f:
            d = json.load(f)
            yield FrameEvent.from_dict(d)
    else:
        raise FileNotFoundError(f"Input path not found or not a valid session, JSONL, or JSON file: {p}")


def _dict_to_frame(d: Dict[str, Any]) -> FrameEvent:
    furn = [DetectedEntity(id=e["id"], kind=e["kind"], pose=Pose2D(**e["pose"]), confidence=e.get("confidence")) for e in d.get("furniture", [])]
    peep = [DetectedEntity(id=e["id"], kind=e["kind"], pose=Pose2D(**e["pose"]), confidence=e.get("confidence")) for e in d.get("people", [])]
    return FrameEvent(timestamp_iso=d.get("timestamp_iso", ""), frame_id=int(d.get("frame_id", 0)), furniture=furn, people=peep, world=d.get("world", {}))


def main() -> None:
    logger = get_logger(__name__)
    parser = argparse.ArgumentParser(description="Replay FrameEvents from JSON/JSONL/session.")
    parser.add_argument("--events", default="src/aisi_sensing/contracts/examples/frame_event.example.json", help="Input: JSON, JSONL, or session folder")
    parser.add_argument("--max-frames", type=int, default=500, help="Max frames to replay")
    parser.add_argument("--fps", type=int, default=10, help="Playback FPS")
    parser.add_argument("--no-gui", action="store_true", help="Disable GUI (matplotlib)")
    parser.add_argument("--export", type=str, default=None, help="Export summary JSON")
    parser.add_argument("--classes", default="configs/classes.example.yaml")
    parser.add_argument("--log-interval", type=int, default=10, help="Log every N frames")
    args = parser.parse_args()

    # Load configs lazily; keep optional to allow minimal run
    try:
        from ..core.config import load_yaml
        cfg = load_yaml(args.classes)
    except Exception:
        cfg = {}

    results = []
    gui_mode = not args.no_gui
    if gui_mode:
        import matplotlib.pyplot as plt
        from ..feedback.floorplan_render import draw_floorplan
        plt.ion()
        fig, ax = plt.subplots(figsize=(6, 4))
        print("Close the figure window or press CTRL+C to exit.")
    try:
        for idx, ev in enumerate(load_events(args.events)):
            if idx >= args.max_frames:
                break
            layout = classify_layout(ev, cfg)
            social = classify_social(ev, cfg)
            if idx % args.log_interval == 0 or idx == 0:
                logger.info("Frame %d | Layout: %s (%.2f) | Social: %s (%.2f)",
                            ev.frame_id, layout["label"], layout["score"], social["label"], social["score"])
            results.append({
                "frame_id": ev.frame_id,
                "layout": layout["label"],
                "layout_score": layout["score"],
                "social": social["label"],
                "social_score": social["score"],
            })
            if gui_mode:
                title = f"Frame {ev.frame_id} | Layout: {layout['label']} | Social: {social['label']}"
                draw_floorplan(ax, ev, title)
                plt.pause(1.0 / max(1, args.fps))
            else:
                print(f"Frame {ev.frame_id}: Layout={layout['label']} Social={social['label']}")
        if gui_mode:
            plt.ioff()
            plt.show()
    except KeyboardInterrupt:
        if gui_mode:
            import matplotlib.pyplot as plt
            plt.close('all')
        print("Stopped by user.")
    # Export summary if requested
    if args.export:
        from collections import Counter
        summary = {
            "frames": results,
            "layout_counts": dict(Counter(r["layout"] for r in results)),
            "social_counts": dict(Counter(r["social"] for r in results)),
        }
        with open(args.export, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
        logger.info(f"Exported summary to {args.export}")


if __name__ == "__main__":
    main()
