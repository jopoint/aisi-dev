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

    # Write meta.json
    meta = {
        "timestamp": datetime.now().isoformat(),
        "session_id": session_id,
        "args": vars(args),
        "python_version": sys.version,
        "platform": platform.platform(),
        "schema_version": "1.0",
    }
    # Try to get git info
    try:
        git_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=Path(__file__).parent.parent.parent, stderr=subprocess.DEVNULL).decode().strip()
        meta["git_commit"] = git_commit
    except Exception:
        meta["git_commit"] = None
    with meta_path.open("w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    logger.info(f"Wrote meta.json to {meta_path}")

    # Dummy mode: generate N frames with evolving layout and people positions
    import random
    random.seed(args.seed)
    layouts = ["presentation_front", "group_islands", "circle", "seminar_rows"]
    num_people = 3
    num_tables = 2
    frames = []
    for i in range(args.num_frames):
        layout = layouts[i % len(layouts)]
        # Move people in a circle
        people = [
            DetectedEntity(
                id=f"p{j+1}",
                kind="person",
                pose=Pose2D(
                    x=2.0 + 1.0 * random.uniform(-1, 1) + 1.5 * random.uniform(-1, 1) * (j+1) * (i/args.num_frames),
                    y=2.0 + 1.0 * random.uniform(-1, 1) + 1.5 * random.uniform(-1, 1) * (j+1) * (i/args.num_frames),
                    theta=None,
                ),
                confidence=1.0,
            ) for j in range(num_people)
        ]
        # Move tables in a line
        furniture = [
            DetectedEntity(
                id=f"t{j+1}",
                kind="table",
                pose=Pose2D(
                    x=1.0 + j*2.0 + 0.1*i,
                    y=1.0 + 0.2*j,
                    theta=None,
                ),
                confidence=1.0,
            ) for j in range(num_tables)
        ]
        frame = FrameEvent(
            timestamp_iso=(datetime.now().isoformat()),
            frame_id=i,
            furniture=furniture,
            people=people,
            world={"layout": layout, "bounds": [0.0, 0.0, 6.0, 4.0]},
        )
        frames.append(frame)
    write_jsonl(events_path, (f.to_dict() for f in frames))
    logger.info(f"Wrote {len(frames)} events to {events_path}")

    print(f"Session recorded: {out_dir}")


if __name__ == "__main__":
    main()
