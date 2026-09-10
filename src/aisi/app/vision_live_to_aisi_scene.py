"""Adapt calibrated live vision FrameEvents to the existing AISI scene contract.

This is intentionally a tables-only producer.  It owns its output scene file;
do not point it at the Room Editor's ``live_scene.json`` while that editor is
running.  ``sim_scene_to_osc --scene`` can consume this scene unchanged.
"""

from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import tempfile
import time
from typing import Any

from aisi.core.table_geometry import get_table_geometry
from aisi_sensing.core.types import FrameEvent


ROI_WIDTH_CM = 500.0
ROI_HEIGHT_CM = 500.0
RECT_TABLE_TYPE = "rect"
DEFAULT_POLL_SECONDS = 0.05
DEFAULT_MISSING_FRAMES = 15
DEFAULT_STREAM_STALE_SECONDS = 2.0
SCENE_FILE_RETRY_DELAYS_SECONDS = (0.005, 0.010, 0.020)


def default_input_path() -> Path:
    return Path(__file__).resolve().parents[3] / "data" / "vision" / "live" / "current_room_rect.jsonl"


def default_output_path() -> Path:
    return Path(__file__).resolve().parents[3] / "data" / "aisi" / "scenes" / "live" / "vision_live_scene.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Adapt calibrated Rect-table vision FrameEvents into an AISI scene JSON."
    )
    parser.add_argument("--input", default=str(default_input_path()), help="Vision FrameEvent JSONL input.")
    parser.add_argument("--output", default=str(default_output_path()), help="Dedicated AISI scene JSON output.")
    parser.add_argument("--missing-frames", type=int, default=DEFAULT_MISSING_FRAMES,
                        help="Consecutive valid frames before an absent table is removed (default: 15).")
    parser.add_argument("--stream-stale-seconds", type=float, default=DEFAULT_STREAM_STALE_SECONDS,
                        help="Clear tables after this long without a new FrameEvent (default: 2.0).")
    parser.add_argument("--poll-seconds", type=float, default=DEFAULT_POLL_SECONDS,
                        help="JSONL polling interval in seconds (default: 0.05).")
    parser.add_argument("--once", action="store_true",
                        help="Convert the last complete input FrameEvent once, then exit (offline use).")
    return parser.parse_args()


def _finite_number(value: object, field: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{field} must be numeric")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be numeric") from exc
    if not math.isfinite(number):
        raise ValueError(f"{field} must be finite")
    return number


def _require_tabletop_world(frame: FrameEvent) -> None:
    """Reject uncalibrated/pixel FrameEvents rather than silently remapping them."""
    world = frame.world
    if world.get("homography_applied") is not True:
        raise ValueError("FrameEvent does not declare homography_applied=true")
    if world.get("calibration_plane") != "rect_tabletop":
        raise ValueError("FrameEvent is not calibrated for the rect_tabletop plane")


def _tables_from_frame(frame: FrameEvent) -> dict[str, dict[str, Any]]:
    """Return valid Rect table records keyed by stable vision track ID."""
    _require_tabletop_world(frame)
    geometry = get_table_geometry(RECT_TABLE_TYPE)
    result: dict[str, dict[str, Any]] = {}
    for entity in frame.furniture:
        if entity.kind != "table":
            continue
        table_id = str(entity.id).strip()
        if not table_id:
            raise ValueError("Table FrameEvent entity has an empty id")
        if table_id in result:
            raise ValueError(f"Duplicate table id in FrameEvent: {table_id!r}")
        x_cm = _finite_number(entity.pose.x, f"table {table_id!r} pose.x")
        y_cm = _finite_number(entity.pose.y, f"table {table_id!r} pose.y")
        theta_rad = _finite_number(entity.pose.theta, f"table {table_id!r} pose.theta")
        result[table_id] = {
            "id": table_id,
            # Vision already emits calibrated AISI world cm.  Do not transform it.
            "x_cm": x_cm,
            "y_cm": y_cm,
            # The scene/OSC contract uses degrees; this is only a unit conversion.
            "rotation_deg": math.degrees(theta_rad),
            "width_cm": geometry.nominal_width,
            "height_cm": geometry.nominal_depth,
            "type": RECT_TABLE_TYPE,
            "confidence": entity.confidence,
        }
    return result


def build_scene(tables: list[dict[str, Any]], frame: FrameEvent | None) -> dict[str, Any]:
    """Build the existing scene shape, explicitly owned by the live adapter."""
    vision_metadata: dict[str, Any] = {"mode": "tables_only"}
    if frame is not None:
        vision_metadata.update({
            "frame_id": frame.frame_id,
            "timestamp_iso": frame.timestamp_iso,
            "calibration_id": frame.world.get("calibration_id"),
            "calibration_plane": frame.world.get("calibration_plane"),
            "plane_height_cm": frame.world.get("plane_height_cm"),
        })
    return {
        "scene_id": "vision_live_scene",
        "source": "vision_live_to_aisi_scene",
        "roi": {"width_cm": ROI_WIDTH_CM, "height_cm": ROI_HEIGHT_CM},
        "tables": tables,
        # Do not project chair/person detections through this tables-only path.
        "chairs": [],
        "persons": [],
        "vision_live": vision_metadata,
    }


def _is_transient_windows_file_lock(error: OSError) -> bool:
    """Return whether Windows reported a replace/open sharing race."""

    return isinstance(error, PermissionError) or getattr(error, "winerror", None) in {5, 32}


def _replace_with_retry(temp_path: str, destination: Path) -> None:
    """Replace a scene file with bounded retries for transient Windows locks."""

    for delay in (*SCENE_FILE_RETRY_DELAYS_SECONDS, None):
        try:
            os.replace(temp_path, destination)
            return
        except OSError as error:
            if not _is_transient_windows_file_lock(error) or delay is None:
                raise
            time.sleep(delay)


def atomic_write_scene(path: str | Path, scene: dict[str, Any]) -> None:
    """Atomically replace the scene file, so OSC never reads partial JSON."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=destination.parent,
            prefix=f".{destination.name}.", suffix=".tmp", delete=False,
        ) as handle:
            temp_name = handle.name
            json.dump(scene, handle, indent=2)
            handle.flush()
            os.fsync(handle.fileno())
        _replace_with_retry(temp_name, destination)
    except Exception:
        if temp_name is not None:
            Path(temp_name).unlink(missing_ok=True)
        raise


class VisionSceneAdapter:
    """Keep table order stable across FrameEvents and handle missing/stale input."""

    def __init__(self, missing_frames: int = DEFAULT_MISSING_FRAMES) -> None:
        if missing_frames < 0:
            raise ValueError("missing_frames must be >= 0")
        self.missing_frames = missing_frames
        self._known_order: list[str] = []
        self._active: dict[str, dict[str, Any]] = {}
        self._missing_counts: dict[str, int] = {}
        self.last_frame: FrameEvent | None = None

    def apply_frame(self, frame: FrameEvent) -> bool:
        """Apply one frame. Returns True when the published scene changed."""
        observed = _tables_from_frame(frame)
        for table_id in sorted(set(observed) - set(self._known_order)):
            self._known_order.append(table_id)

        changed = False
        for table_id, table in observed.items():
            if self._active.get(table_id) != table:
                changed = True
            self._active[table_id] = table
            self._missing_counts[table_id] = 0

        for table_id in list(self._active):
            if table_id in observed:
                continue
            missing = self._missing_counts.get(table_id, 0) + 1
            self._missing_counts[table_id] = missing
            if missing >= self.missing_frames:
                del self._active[table_id]
                changed = True

        self.last_frame = frame
        return changed

    def clear_stale(self) -> bool:
        """Remove every active table after a stopped/stale input stream."""
        if not self._active:
            return False
        self._active.clear()
        self._missing_counts.clear()
        return True

    def scene(self) -> dict[str, Any]:
        ordered_tables = [self._active[table_id] for table_id in self._known_order if table_id in self._active]
        return build_scene(ordered_tables, self.last_frame)


def _frame_from_json_line(raw_line: bytes) -> FrameEvent:
    try:
        payload = json.loads(raw_line.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"Invalid FrameEvent JSONL line: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("FrameEvent JSONL record must be an object")
    return FrameEvent.from_dict(payload)


def load_last_frame(path: str | Path) -> FrameEvent:
    source = Path(path)
    last_line: bytes | None = None
    with source.open("rb") as handle:
        for raw_line in handle:
            if raw_line.strip():
                last_line = raw_line
    if last_line is None:
        raise ValueError(f"No complete FrameEvent found in {source}")
    return _frame_from_json_line(last_line)


def run_live(input_path: str | Path, output_path: str | Path, adapter: VisionSceneAdapter,
             poll_seconds: float, stream_stale_seconds: float) -> None:
    """Tail appended JSONL records; reset safely when the vision writer truncates it."""
    source = Path(input_path)
    offset = 0
    pending = b""
    accepted_any_frame = False
    last_accepted_at = 0.0
    stale_published = False
    print(f"Vision input: {source}")
    print(f"AISI scene output: {output_path}")
    print("Vision adapter owns this output. Do not run the Room Editor against it.")

    while True:
        try:
            size = source.stat().st_size
            if size < offset:
                offset = 0
                pending = b""
            if size > offset:
                with source.open("rb") as handle:
                    handle.seek(offset)
                    data = handle.read()
                offset += len(data)
                pending += data
                complete_lines = pending.split(b"\n")
                pending = complete_lines.pop()
                for raw_line in complete_lines:
                    if not raw_line.strip():
                        continue
                    try:
                        frame = _frame_from_json_line(raw_line)
                        adapter.apply_frame(frame)
                    except ValueError as exc:
                        print(f"Skipping invalid FrameEvent: {exc}")
                        continue
                    atomic_write_scene(output_path, adapter.scene())
                    accepted_any_frame = True
                    last_accepted_at = time.monotonic()
                    stale_published = False
        except FileNotFoundError:
            pass
        except OSError as exc:
            print(f"Unable to read vision input: {exc}")

        if (
            accepted_any_frame
            and not stale_published
            and time.monotonic() - last_accepted_at >= stream_stale_seconds
        ):
            if adapter.clear_stale():
                atomic_write_scene(output_path, adapter.scene())
                print("Vision stream stale; published an empty tables scene.")
            stale_published = True
        time.sleep(poll_seconds)


def main() -> None:
    args = parse_args()
    if args.poll_seconds <= 0:
        raise SystemExit("--poll-seconds must be > 0")
    if args.stream_stale_seconds < 0:
        raise SystemExit("--stream-stale-seconds must be >= 0")
    adapter = VisionSceneAdapter(missing_frames=args.missing_frames)
    if args.once:
        frame = load_last_frame(args.input)
        adapter.apply_frame(frame)
        atomic_write_scene(args.output, adapter.scene())
        print(f"Wrote {len(adapter.scene()['tables'])} Rect table(s) to {Path(args.output).resolve()}")
        return
    try:
        run_live(args.input, args.output, adapter, args.poll_seconds, args.stream_stale_seconds)
    except KeyboardInterrupt:
        print("Vision adapter stopped.")


if __name__ == "__main__":
    main()
