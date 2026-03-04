from __future__ import annotations

"""Record FrameEvent stream to data/sessions/<session_id>/events.jsonl (skeleton)."""


import argparse
import json
import os
import sys
import platform
import subprocess
from pathlib import Path
from datetime import datetime
from ..core.logging import get_logger, write_jsonl
from ..core.timebase import now_iso
from ..core.types import FrameEvent, DetectedEntity, Pose2D



def main() -> None:
    logger = get_logger(__name__)
    parser = argparse.ArgumentParser(description="Record a FrameEvent stream to a session folder.")
    parser.add_argument("--session-id", type=str, default=None, help="Session id (default: timestamp)")
    parser.add_argument("--out-dir", type=str, default="data/sessions", help="Output base directory")
    parser.add_argument("--source", choices=["dummy", "video", "camera"], default="dummy", help="Input source")
    parser.add_argument("--num-frames", type=int, default=200, help="Number of frames to record")
    parser.add_argument("--fps", type=int, default=10, help="Frames per second")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for dummy mode")
    parser.add_argument("--lab-config", type=str, default="configs/lab.example.yaml", help="Lab config path")
    parser.add_argument("--classes-config", type=str, default="configs/classes.example.yaml", help="Classes config path")
    args = parser.parse_args()

    # Determine session id
    if args.session_id:
        session_id = args.session_id
    else:
        session_id = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    out_dir = Path(args.out_dir) / session_id
    out_dir.mkdir(parents=True, exist_ok=True)
    events_path = out_dir / "events.jsonl"
    meta_path = out_dir / "meta.json"


    # --- Config snapshotting ---
    import shutil
    import yaml
    lab_src = Path(args.lab_config)
    classes_src = Path(args.classes_config)
    lab_dst = out_dir / "lab.yaml"
    classes_dst = out_dir / "classes.yaml"
    meta = {
        "timestamp": datetime.now().isoformat(),
        "session_id": session_id,
        "args": vars(args),
        "python_version": sys.version,
        "platform": platform.platform(),
        "schema_version": "1.0",
        "lab_config_snapshot_path": str(lab_dst),
        "classes_config_snapshot_path": str(classes_dst),
    }
    # Try to get git info
    try:
        git_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=Path(__file__).parent.parent.parent, stderr=subprocess.DEVNULL).decode().strip()
        meta["git_commit"] = git_commit
    except Exception:
        meta["git_commit"] = None

    # Copy and parse configs
    def copy_and_parse(src, dst, meta_key):
        try:
            shutil.copy2(src, dst)
            with open(dst, "r", encoding="utf-8") as f:
                parsed = yaml.safe_load(f)
            meta[meta_key] = parsed
            logger.info(f"Snapshot config: {src} -> {dst}")
        except Exception as e:
            logger.warning(f"Could not snapshot config {src}: {e}")
            meta[meta_key] = None

    copy_and_parse(lab_src, lab_dst, "lab_config_snapshot")
    copy_and_parse(classes_src, classes_dst, "classes_config_snapshot")

    with meta_path.open("w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    logger.info(f"Wrote meta.json to {meta_path}")

    # Dummy mode: generate N frames with realistic jitter/noise and 4 phases
    import random
    import yaml
    random.seed(args.seed)

    # Load lab bounds from lab config
    bounds = [0.0, 0.0, 6.0, 4.0]
    try:
        with open(args.lab_config, 'r', encoding='utf-8') as f:
            lab_cfg = yaml.safe_load(f) or {}
            lb = (((lab_cfg or {}).get('lab') or {}).get('bounds'))
            if isinstance(lb, list) and len(lb) == 4:
                bounds = [float(x) for x in lb]
    except Exception as e:
        logger.warning(f"Could not read lab config {args.lab_config}: {e}")

    # Load dummy noise params from classes config
    jitter_sigma = 0.08
    walk_sigma = 0.02
    try:
        with open(args.classes_config, 'r', encoding='utf-8') as f:
            cls_cfg = yaml.safe_load(f) or {}
            feats = (cls_cfg or {}).get('features') or {}
            jitter_sigma = float(feats.get('dummy_jitter_sigma_m', jitter_sigma))
            walk_sigma = float(feats.get('dummy_random_walk_sigma_m', walk_sigma))
    except Exception as e:
        logger.warning(f"Could not read classes config {args.classes_config}: {e}")

    def clamp(v, lo, hi):
        return max(lo, min(hi, v))

    min_x, min_y, max_x, max_y = bounds
    cx, cy = (min_x + max_x) / 2.0, (min_y + max_y) / 2.0
    width, height = (max_x - min_x), (max_y - min_y)

    # Stable counts and IDs
    n_tables = random.randint(4, 6)
    n_chairs = random.randint(8, 12)
    n_people = random.randint(6, 10)
    table_ids = [f"TABLE-{i:02d}" for i in range(1, n_tables + 1)]
    chair_ids = [f"CHAIR-{i:02d}" for i in range(1, n_chairs + 1)]
    person_ids = [f"P-{i:02d}" for i in range(1, n_people + 1)]

    # Per-entity small random-walk drift state
    drift = {eid: (0.0, 0.0) for eid in (table_ids + chair_ids + person_ids)}

    # Phase generator helpers
    def add_noise(x, y, eid):
        dx, dy = drift[eid]
        dx += random.gauss(0.0, walk_sigma)
        dy += random.gauss(0.0, walk_sigma)
        # Bound the drift to avoid runaway
        dx = clamp(dx, -0.3, 0.3)
        dy = clamp(dy, -0.3, 0.3)
        drift[eid] = (dx, dy)
        x = clamp(x + dx + random.gauss(0.0, jitter_sigma), min_x, max_x)
        y = clamp(y + dy + random.gauss(0.0, jitter_sigma), min_y, max_y)
        return x, y

    def phase_presentation_front():
        front_margin = 0.5
        rows = random.randint(2, 3)
        row_ys = [max_y - front_margin - i * 0.5 for i in range(rows)]
        xs = [min_x + (i + 1) * (width / (n_tables + 1)) for i in range(n_tables)]
        tbl_positions = [(xs[i % len(xs)], row_ys[i % rows]) for i in range(n_tables)]
        # Chairs behind tables (lower y)
        ch_positions = []
        for i in range(n_chairs):
            t = tbl_positions[i % n_tables]
            ch_positions.append((t[0] + random.uniform(-0.2, 0.2), t[1] - 0.3))
        # People behind front rows
        ppl_positions = [(min_x + (i + 1) * (width / (n_people + 1)), max_y - front_margin - 0.6 - 0.3 * (i % rows)) for i in range(n_people)]
        return tbl_positions, ch_positions, ppl_positions

    def phase_group_islands():
        # Choose 2-3 island centroids in a triangle-like arrangement (non-collinear)
        k = random.randint(2, 3)
        centers = []
        if k == 2:
            r = min(width, height) * 0.25
            centers = [
                (clamp(cx - r, min_x + 0.5, max_x - 0.5), clamp(cy - r/2, min_y + 0.5, max_y - 0.5)),
                (clamp(cx + r, min_x + 0.5, max_x - 0.5), clamp(cy + r/3, min_y + 0.5, max_y - 0.5)),
            ]
        else:
            r = min(width, height) * 0.30
            angs = [0.0, 2.094, 4.188]  # ~0, 120, 240 deg
            centers = [
                (clamp(cx + r * cos(a), min_x + 0.5, max_x - 0.5), clamp(cy + r * sin(a), min_y + 0.5, max_y - 0.5))
                for a in angs
            ]
        tbl_positions = []
        for i in range(n_tables):
            cx_i, cy_i = centers[i % k]
            ang = random.uniform(0, 6.283)
            r = 0.4 + 0.15 * random.random()
            tbl_positions.append((cx_i + r * cos(ang), cy_i + r * sin(ang)))
        ch_positions = []
        for i in range(n_chairs):
            cx_i, cy_i = centers[i % k]
            ang = random.uniform(0, 6.283)
            r = 0.6 + 0.2 * random.random()
            ch_positions.append((cx_i + r * cos(ang), cy_i + r * sin(ang)))
        ppl_positions = []
        for i in range(n_people):
            cx_i, cy_i = centers[i % k]
            ang = random.uniform(0, 6.283)
            r = 0.7 + 0.3 * random.random()
            ppl_positions.append((cx_i + r * cos(ang), cy_i + r * sin(ang)))
        return tbl_positions, ch_positions, ppl_positions

    def phase_circle():
        R = min(width, height) * 0.35
        tbl_positions = [(cx + R * cos(2 * 3.14159 * i / n_tables), cy + R * sin(2 * 3.14159 * i / n_tables)) for i in range(n_tables)]
        ch_positions = [(cx + (R + 0.2) * cos(2 * 3.14159 * i / n_chairs), cy + (R + 0.2) * sin(2 * 3.14159 * i / n_chairs)) for i in range(n_chairs)]
        ppl_positions = [(cx + (R - 0.2) * cos(2 * 3.14159 * i / n_people), cy + (R - 0.2) * sin(2 * 3.14159 * i / n_people)) for i in range(n_people)]
        return tbl_positions, ch_positions, ppl_positions

    def phase_seminar_rows():
        rows = random.randint(3, 4)
        spacing = height / (rows + 2)
        row_ys = [min_y + spacing * (i + 2) for i in range(rows)]
        xs = [min_x + (i + 1) * (width / (max(n_tables, n_chairs) + 1)) for i in range(max(n_tables, n_chairs))]
        tbl_positions = [(xs[i % len(xs)], row_ys[i % rows]) for i in range(n_tables)]
        ch_positions = [(xs[i % len(xs)], row_ys[(i + 1) % rows]) for i in range(n_chairs)]
        ppl_positions = [(xs[i % len(xs)], row_ys[i % rows] + (0.25 if i % 2 == 0 else -0.25)) for i in range(n_people)]
        return tbl_positions, ch_positions, ppl_positions

    from math import sin, cos
    phase_funcs = [phase_presentation_front, phase_group_islands, phase_circle, phase_seminar_rows]
    phase_labels = ["presentation_front", "group_islands", "circle", "seminar_rows"]
    phase_len = max(1, args.num_frames // 4)

    frames = []
    for i in range(args.num_frames):
        phase = (i // phase_len) % 4
        label = phase_labels[phase]
        tbl_pos, ch_pos, ppl_pos = phase_funcs[phase]()
        # Build entities with noise
        furniture = []
        for idx, eid in enumerate(table_ids):
            x, y = add_noise(*tbl_pos[idx % len(tbl_pos)], eid)
            furniture.append(DetectedEntity(id=eid, kind="table", pose=Pose2D(x, y), confidence=1.0))
        for idx, eid in enumerate(chair_ids):
            x, y = add_noise(*ch_pos[idx % len(ch_pos)], eid)
            furniture.append(DetectedEntity(id=eid, kind="chair", pose=Pose2D(x, y), confidence=1.0))
        people = []
        for idx, eid in enumerate(person_ids):
            x, y = add_noise(*ppl_pos[idx % len(ppl_pos)], eid)
            people.append(DetectedEntity(id=eid, kind="person", pose=Pose2D(x, y), confidence=1.0))

        frame = FrameEvent(
            timestamp_iso=(datetime.now().isoformat()),
            frame_id=i,
            furniture=furniture,
            people=people,
            world={"layout": label, "bounds": bounds},
        )
        frames.append(frame)

    write_jsonl(events_path, (f.to_dict() for f in frames))
    logger.info(f"Wrote {len(frames)} events to {events_path}")

    print(f"Session recorded: {out_dir}")


if __name__ == "__main__":
    main()
