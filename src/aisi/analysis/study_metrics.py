"""Extract reproducible per-trial metrics from Study-controller JSONL logs.

This module is intentionally offline-only: it does not alter tracking, OSC,
TouchDesigner, or the Study controller. Position changes smaller than 1 cm and
Rect-orientation changes smaller than 1 degree are treated as residual tracking
jitter for path calculations. A stop is a >= 1 s stationary interval after
meaningful movement that is followed by resumed movement. A correction is a
transition from >= 5 cm radial progress toward the target to >= 5 cm renewed
movement away from it.
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime
import json
import math
from pathlib import Path
from typing import Any, Iterable


POSITION_STEP_DEADBAND_CM = 1.0
ROTATION_STEP_DEADBAND_DEG = 1.0
STOP_MIN_DURATION_S = 1.0
CORRECTION_RADIAL_DEADBAND_CM = 5.0
SUCCESS_POSITION_TOLERANCE_CM = 8.0
SUCCESS_ROTATION_TOLERANCE_DEG = 5.0

METRIC_COLUMNS = (
    "source_log_filename", "session_id", "task_id", "task", "variant", "condition",
    "trial_start_timestamp", "trial_end_timestamp", "trial_duration_s",
    "translation_path_cm", "rotation_path_deg", "final_position_error_cm",
    "final_rotation_error_deg", "success", "stop_count", "correction_count",
    "valid_pose_sample_count", "missing_pose_sample_count",
)


def rect_angle_delta_deg(first_deg: float, second_deg: float) -> float:
    """Return the smallest orientation change for a 180-degree-symmetric Rect."""

    return abs((float(second_deg) - float(first_deg) + 90.0) % 180.0 - 90.0)


def read_jsonl_events(path: str | Path) -> list[dict[str, Any]]:
    """Read valid JSON-object lines, silently retaining usable neighboring rows."""

    events: list[dict[str, Any]] = []
    try:
        lines = Path(path).read_text(encoding="utf-8").splitlines()
    except OSError:
        return events
    for line in lines:
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(event, dict):
            events.append(event)
    return events


def analyze_log(path: str | Path) -> list[dict[str, Any]]:
    """Return one metric record for every completed trial in a JSONL session."""

    source = Path(path)
    records: list[dict[str, Any]] = []
    active_trial: dict[str, Any] | None = None
    active_samples: list[dict[str, Any]] = []
    for event in read_jsonl_events(source):
        event_type = event.get("event_type")
        if event_type == "trial_started":
            active_trial, active_samples = event, []
        elif event_type == "active_pose_sample" and active_trial is not None:
            active_samples.append(event)
        elif event_type == "trial_completed" and active_trial is not None:
            records.append(_trial_metrics(source, active_trial, event, active_samples))
            active_trial, active_samples = None, []
    return records


def analyze_logs(paths: Iterable[str | Path]) -> list[dict[str, Any]]:
    """Analyze individual JSONL paths or all ``*.jsonl`` files in directories."""

    records: list[dict[str, Any]] = []
    for item in paths:
        path = Path(item)
        files = sorted(path.glob("*.jsonl")) if path.is_dir() else [path]
        for file_path in files:
            records.extend(analyze_log(file_path))
    return records


def _trial_metrics(source: Path, started: dict[str, Any], completed: dict[str, Any], sample_events: list[dict[str, Any]]) -> dict[str, Any]:
    valid_samples: list[tuple[float | None, float, float, float]] = []
    missing_count = 0
    for event in sample_events:
        pose = _pose(event.get("source_pose"))
        if pose is None:
            missing_count += 1
            continue
        valid_samples.append((_event_time(event), *pose))

    target = _target_pose(completed) or _target_pose(started)
    completion_pose = _pose(completed.get("source_pose"))
    final_pose = completion_pose or (valid_samples[-1][1:] if valid_samples else None)
    translation_path, rotation_path, stops, corrections = _trajectory_metrics(valid_samples, target)
    final_position_error = None
    final_rotation_error = None
    if final_pose is not None and target is not None:
        final_position_error = math.hypot(final_pose[0] - target[0], final_pose[1] - target[1])
        final_rotation_error = rect_angle_delta_deg(final_pose[2], target[2])
    success = bool(
        final_position_error is not None and final_rotation_error is not None
        and final_position_error <= SUCCESS_POSITION_TOLERANCE_CM
        and final_rotation_error <= SUCCESS_ROTATION_TOLERANCE_DEG
    )
    return {
        "source_log_filename": source.name,
        "session_id": source.stem,
        "task_id": completed.get("task_id", started.get("task_id")),
        "task": completed.get("task", started.get("task")),
        "variant": completed.get("variant", started.get("variant")),
        "condition": completed.get("condition", started.get("condition")),
        "trial_start_timestamp": started.get("timestamp_iso"),
        "trial_end_timestamp": completed.get("timestamp_iso"),
        "trial_duration_s": _duration_s(started, completed),
        "translation_path_cm": translation_path,
        "rotation_path_deg": rotation_path,
        "final_position_error_cm": final_position_error,
        "final_rotation_error_deg": final_rotation_error,
        "success": success,
        "stop_count": stops,
        "correction_count": corrections,
        "valid_pose_sample_count": len(valid_samples),
        "missing_pose_sample_count": missing_count,
    }


def _trajectory_metrics(samples: list[tuple[float | None, float, float, float]], target: tuple[float, float, float] | None) -> tuple[float, float, int, int]:
    if not samples:
        return 0.0, 0.0, 0, 0
    translation_path = 0.0
    rotation_path = 0.0
    stops = 0
    corrections = 0
    anchor_time, anchor_x, anchor_y, anchor_rot = samples[0]
    movement_seen = False
    stationary_since: float | None = None
    was_stationary = False
    radial_state: str | None = None
    prior_distance = _distance_to_target(anchor_x, anchor_y, target)
    for sample_time, x, y, rotation in samples[1:]:
        step_distance = math.hypot(x - anchor_x, y - anchor_y)
        rotation_step = rect_angle_delta_deg(anchor_rot, rotation)
        meaningful_translation = step_distance >= POSITION_STEP_DEADBAND_CM
        meaningful_rotation = rotation_step >= ROTATION_STEP_DEADBAND_DEG
        if meaningful_translation or meaningful_rotation:
            if was_stationary and movement_seen:
                stops += 1
            stationary_since = None
            was_stationary = False
            movement_seen = True
            if meaningful_translation:
                translation_path += step_distance
                if target is not None and prior_distance is not None:
                    current_distance = _distance_to_target(x, y, target)
                    radial_delta = current_distance - prior_distance
                    if radial_delta <= -CORRECTION_RADIAL_DEADBAND_CM:
                        radial_state = "toward"
                    elif radial_delta >= CORRECTION_RADIAL_DEADBAND_CM:
                        if radial_state == "toward":
                            corrections += 1
                        radial_state = "away"
                    prior_distance = current_distance
                anchor_x, anchor_y = x, y
            if meaningful_rotation:
                rotation_path += rotation_step
                anchor_rot = rotation
            anchor_time = sample_time if sample_time is not None else anchor_time
            continue
        if movement_seen and sample_time is not None and anchor_time is not None:
            if stationary_since is None and sample_time - anchor_time >= STOP_MIN_DURATION_S:
                stationary_since = sample_time
                was_stationary = True
    return translation_path, rotation_path, stops, corrections


def _pose(value: object) -> tuple[float, float, float] | None:
    if not isinstance(value, dict):
        return None
    try:
        pose = (float(value["x_cm"]), float(value["y_cm"]), float(value["rotation_deg"]))
    except (KeyError, TypeError, ValueError):
        return None
    return pose if all(math.isfinite(component) for component in pose) else None


def _target_pose(event: dict[str, Any]) -> tuple[float, float, float] | None:
    try:
        pose = (float(event["target_x_cm"]), float(event["target_y_cm"]), float(event["target_rotation_deg"]))
    except (KeyError, TypeError, ValueError):
        return None
    return pose if all(math.isfinite(component) for component in pose) else None


def _event_time(event: dict[str, Any]) -> float | None:
    for field in ("monotonic_s", "elapsed_s"):
        try:
            value = float(event[field])
        except (KeyError, TypeError, ValueError):
            continue
        if math.isfinite(value):
            return value
    return None


def _duration_s(started: dict[str, Any], completed: dict[str, Any]) -> float | None:
    start_time, end_time = _event_time(started), _event_time(completed)
    if start_time is not None and end_time is not None and end_time >= start_time:
        return end_time - start_time
    try:
        start_wall = datetime.fromisoformat(str(started["timestamp_iso"]).replace("Z", "+00:00"))
        end_wall = datetime.fromisoformat(str(completed["timestamp_iso"]).replace("Z", "+00:00"))
        seconds = (end_wall - start_wall).total_seconds()
        return seconds if seconds >= 0 else None
    except (KeyError, TypeError, ValueError):
        return None


def _distance_to_target(x: float, y: float, target: tuple[float, float, float] | None) -> float | None:
    return None if target is None else math.hypot(x - target[0], y - target[1])


def write_metrics_csv(records: list[dict[str, Any]], path: str | Path) -> Path:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=METRIC_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)
    return destination


def write_metrics_json(records: list[dict[str, Any]], path: str | Path) -> Path:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
    return destination


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("logs", type=Path, nargs="+", help="JSONL files or directories containing them.")
    parser.add_argument("--output-dir", type=Path, default=Path("data/aisi/study/analysis"))
    parser.add_argument("--json", action="store_true", help="Also write study_metrics.json.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    records = analyze_logs(args.logs)
    csv_path = write_metrics_csv(records, args.output_dir / "study_metrics.csv")
    print(f"Wrote {len(records)} completed trial metric row(s) to {csv_path}")
    if args.json:
        print(f"Wrote {write_metrics_json(records, args.output_dir / 'study_metrics.json')}")


if __name__ == "__main__":
    main()
