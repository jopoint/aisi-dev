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
from ..core.logging import iter_jsonl, read_jsonl

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
                "layout_debug": {k: layout["debug"].get(k) for k in ("rule", "chosen_before_gate", "gated_to_unknown")},
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
    # If session folder and labels present and no-gui: print accuracy report
    events_path = Path(args.events)
    if args.no_gui and events_path.is_dir():
        labels_path = events_path / "labels.jsonl"
        if labels_path.exists():
            labels = read_jsonl(labels_path)
            human = {int(r.get("frame_id")): r.get("human_layout", "unknown") for r in labels}
            preds = {int(r["frame_id"]): r["layout"] for r in results}
            common = sorted(set(human) & set(preds))
            total_labeled = len(common)
            correct = sum(1 for fid in common if preds[fid] == human[fid])
            unknown_rate = sum(1 for fid in common if human[fid] == "unknown") / max(1, total_labeled)
            # per-class accuracy when human==class
            from collections import defaultdict
            per_class_tot = defaultdict(int)
            per_class_ok = defaultdict(int)
            for fid in common:
                hl = human[fid]
                per_class_tot[hl] += 1
                if preds[fid] == hl:
                    per_class_ok[hl] += 1
            logger.info("Labels found: %d | Overall acc: %.2f | Unknown rate: %.2f",
                        total_labeled, (correct / max(1, total_labeled)), unknown_rate)
            for lbl in sorted(per_class_tot.keys()):
                acc = per_class_ok[lbl] / max(1, per_class_tot[lbl])
                logger.info("Class %s: acc=%.2f (%d/%d)", lbl, acc, per_class_ok[lbl], per_class_tot[lbl])

    # Export summary if requested
    if args.export:
        from collections import Counter
        def compute_transitions(labels):
            transitions = Counter()
            for prev, curr in zip(labels, labels[1:]):
                transitions[f"{prev}->{curr}"] += 1
            return dict(transitions)

        layouts = [r["layout"] for r in results]
        socials = [r["social"] for r in results]
        summary = {
            "frames": results,
            "label_counts": {
                "layout": dict(Counter(layouts)),
                "social": dict(Counter(socials)),
            },
            "transitions": {
                "layout": compute_transitions(layouts),
                "social": compute_transitions(socials),
            },
        }
        # If events path is a session folder, add session_id
        if events_path.is_dir():
            summary["session_id"] = events_path.name
        with open(args.export, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
        logger.info(f"Exported summary to {args.export}")


if __name__ == "__main__":
    main()
