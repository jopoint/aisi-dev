from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from pathlib import Path
import sys
import time

import matplotlib.pyplot as plt

from ..core.logging import get_logger, read_jsonl, write_jsonl, iter_jsonl
from ..core.types import FrameEvent
from ..inference.layout_classifier import classify as classify_layout
from ..feedback.floorplan_render import draw_floorplan


def load_events_any(path: Path) -> List[FrameEvent]:
    p = path.expanduser().resolve()
    if p.is_dir():
        p = p / "events.jsonl"
    rows = [FrameEvent.from_dict(d) for d in iter_jsonl(p)]
    return rows


def default_labels_out(events_path: Path) -> Path:
    if events_path.is_dir():
        return (events_path / "labels.jsonl").resolve()
    return (events_path.parent / "labels.jsonl").resolve()


def default_summary_out(events_path: Path) -> Path:
    if events_path.is_dir():
        return (events_path / "labels_summary.json").resolve()
    return (events_path.parent / "labels_summary.json").resolve()


@dataclass
class LabelState:
    labels_by_fid: Dict[int, Dict[str, Any]]
    last_label: Optional[str] = None
    show_help: bool = True


def load_existing_labels(path: Path) -> Dict[int, Dict[str, Any]]:
    if path.exists():
        try:
            rows = read_jsonl(path)
            out: Dict[int, Dict[str, Any]] = {}
            for r in rows:
                if "frame_id" in r and "human_layout" in r:
                    out[int(r["frame_id"])] = r
            return out
        except Exception:
            return {}
    return {}


def save_labels(path: Path, labels_by_fid: Dict[int, Dict[str, Any]], total_frames: int, summary_path: Path) -> None:
    # Rewrite labels.jsonl deterministically by frame_id
    ordered = [labels_by_fid[k] for k in sorted(labels_by_fid.keys())]
    write_jsonl(path, ordered)
    # Summary
    counts: Dict[str, int] = {}
    for r in ordered:
        lbl = r.get("human_layout", "unknown")
        counts[lbl] = counts.get(lbl, 0) + 1
    summary = {
        "total_frames": int(total_frames),
        "labeled_frames": int(len(ordered)),
        "unlabeled_frames": int(max(0, total_frames - len(ordered))),
        "counts_per_label": counts,
        "last_updated_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")


def main() -> None:
    logger = get_logger(__name__)
    ap = argparse.ArgumentParser(description="Human-in-the-loop layout labeling for a session.")
    ap.add_argument("--events", required=True, help="Session folder or events.jsonl path")
    ap.add_argument("--classes-config", default="configs/classes.example.yaml", help="Classes config for model prediction")
    ap.add_argument("--out", default=None, help="Output labels.jsonl path (default: <session>/labels.jsonl)")
    ap.add_argument("--max-frames", type=int, default=None)
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--end", type=int, default=None)
    args = ap.parse_args()

    events_path = Path(args.events).expanduser().resolve()
    # Resolve default outputs from session directory
    session_dir = events_path if events_path.is_dir() else events_path.parent
    labels_path = Path(args.out).expanduser().resolve() if args.out else default_labels_out(events_path)
    summary_path = default_summary_out(events_path)

    frames = load_events_any(events_path)
    total_frames = len(frames)
    # Filter by start/end and max-frames on frame_id basis
    start = max(0, int(args.start))
    end = int(args.end) if args.end is not None else None
    fsel = [f for f in frames if (f.frame_id >= start and (end is None or f.frame_id <= end))]
    if args.max_frames is not None:
        fsel = fsel[: int(args.max_frames)]

    logger.info(f"Loaded {len(fsel)} frames for labeling (from total {total_frames}).")

    # Resume labels
    labels_by_fid = load_existing_labels(labels_path)
    state = LabelState(labels_by_fid=labels_by_fid, last_label=None, show_help=True)

    # Interactive figure
    plt.ion()
    fig, ax = plt.subplots(figsize=(7, 5))

    idx = 0  # index into fsel list

    import yaml
    try:
        with open(args.classes_config, 'r', encoding='utf-8') as f:
            cfg = yaml.safe_load(f) or {}
    except Exception:
        cfg = {}

    labels_map = {
        '1': 'presentation_front',
        '2': 'group_islands',
        '3': 'circle',
        '4': 'seminar_rows',
        '0': 'unknown',
    }

    def current_frame() -> FrameEvent:
        return fsel[idx]

    def redraw():
        ax.clear()
        ev = current_frame()
        # Draw floorplan
        draw_floorplan(ax, ev, title=None)
        # Overlays
        model = classify_layout(ev, cfg)
        total = len(fsel)
        info_lines = [
            f"Frame {idx+1}/{total} (id={ev.frame_id})",
            f"MODEL: {model['label']} ({model['score']:.2f})",
        ]
        human = state.labels_by_fid.get(ev.frame_id, {}).get('human_layout')
        if human:
            info_lines.append(f"HUMAN: {human}")
        if state.last_label:
            info_lines.append(f"Last label: {state.last_label} (Enter to reuse)")
        if state.show_help:
            info_lines.append("Keys: 1:present 2:islands 3:circle 4:rows 0:unknown | n/→ next | p/← prev | Enter reuse | c clear | g goto | s save | h help | q quit")
        # Place text
        y0 = 0.98
        for i, line in enumerate(info_lines):
            ax.text(0.01, y0 - i*0.05, line, transform=ax.transAxes, fontsize=9, va='top', ha='left', bbox=dict(facecolor='white', alpha=0.6, edgecolor='none'))
        fig.canvas.draw_idle()
        plt.pause(0.001)

    def move_next():
        nonlocal idx
        if idx < len(fsel) - 1:
            idx += 1

    def move_prev():
        nonlocal idx
        if idx > 0:
            idx -= 1

    def apply_label(lbl: str):
        ev = current_frame()
        state.labels_by_fid[ev.frame_id] = {
            'frame_id': ev.frame_id,
            'human_layout': lbl,
            'timestamp_iso': ev.timestamp_iso,
            'note': None,
        }
        state.last_label = lbl

    def clear_label():
        ev = current_frame()
        if ev.frame_id in state.labels_by_fid:
            del state.labels_by_fid[ev.frame_id]

    def goto_prompt():
        try:
            target = int(input("Go to frame_id: ").strip())
        except Exception:
            return
        # Find index in fsel with matching frame_id
        for i, fr in enumerate(fsel):
            if fr.frame_id == target:
                nonlocal idx
                idx = i
                break

    def do_save():
        save_labels(labels_path, state.labels_by_fid, total_frames=len(frames), summary_path=summary_path)
        logger.info(f"Saved labels to {labels_path}")

    def on_key(event):
        key = event.key
        if key is None:
            return
        if key in labels_map:
            apply_label(labels_map[key])
            move_next()
            redraw()
            return
        if key in ('enter', 'return'):
            if state.last_label:
                apply_label(state.last_label)
                move_next()
            redraw()
            return
        if key in ('right', 'n'):
            move_next(); redraw(); return
        if key in ('left', 'p'):
            move_prev(); redraw(); return
        if key == 'c':
            clear_label(); redraw(); return
        if key == 'g':
            goto_prompt(); redraw(); return
        if key == 's':
            do_save(); return
        if key == 'h':
            state.show_help = not state.show_help; redraw(); return
        if key == 'q':
            do_save();
            plt.close('all')
            sys.exit(0)

    cid = fig.canvas.mpl_connect('key_press_event', on_key)

    try:
        redraw()
        plt.show(block=True)
    except KeyboardInterrupt:
        pass
    finally:
        do_save()
        logger.info("Exiting label_session (saved).")


if __name__ == '__main__':
    main()
