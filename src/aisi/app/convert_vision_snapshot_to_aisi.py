from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


JsonValue = dict[str, Any] | list[Any] | str | int | float | bool | None


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Convert a vision JSON/JSONL snapshot to AISI scene JSON format."
    )
    parser.add_argument("--input", required=True, help="Path to input JSON or JSONL file.")
    parser.add_argument("--output", required=True, help="Path to output AISI scene JSON.")
    parser.add_argument(
        "--frame-index",
        type=int,
        default=None,
        help="Frame index for JSONL/array inputs (default: last frame).",
    )
    parser.add_argument("--roi-width", type=float, default=500.0, help="ROI width in cm.")
    parser.add_argument("--roi-depth", type=float, default=500.0, help="ROI depth in cm.")
    parser.add_argument("--roi-height", type=float, default=None, help="Optional ROI height in cm for coordinate mapping/output.")
    parser.add_argument("--source-width", type=float, default=None, help="Optional source width for furniture_pose coordinate mapping.")
    parser.add_argument("--source-height", type=float, default=None, help="Optional source height for furniture_pose coordinate mapping.")
    parser.add_argument("--table-width", type=float, default=140.0, help="Table width in cm.")
    parser.add_argument("--table-depth", type=float, default=70.0, help="Table depth in cm.")
    return parser.parse_args()


def _load_records(input_path: Path) -> list[JsonValue]:
    """Load input as a list of records/frames."""
    if not input_path.exists():
        raise ValueError(f"Input file does not exist: {input_path}")

    suffix = input_path.suffix.lower()
    if suffix == ".jsonl":
        records: list[JsonValue] = []
        with input_path.open("r", encoding="utf-8") as handle:
            for line_no, raw in enumerate(handle, start=1):
                line = raw.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    raise ValueError(f"Invalid JSON in JSONL at line {line_no}: {exc}") from exc
        if not records:
            raise ValueError(f"Input JSONL is empty: {input_path}")
        return records

    if suffix == ".json":
        try:
            with input_path.open("r", encoding="utf-8") as handle:
                payload: JsonValue = json.load(handle)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in input file: {input_path} ({exc})") from exc

        if isinstance(payload, list):
            if not payload:
                raise ValueError(f"Input JSON array is empty: {input_path}")
            return payload
        return [payload]

    raise ValueError("Unsupported input type. Use .json or .jsonl")


def _resolve_frame_index(frame_index: int | None, num_frames: int) -> int:
    """Resolve optional frame index with robust bounds handling."""
    if num_frames <= 0:
        raise ValueError("No frames available in input.")

    if frame_index is None:
        return num_frames - 1

    resolved = frame_index
    if frame_index < 0:
        resolved = num_frames + frame_index

    if resolved < 0 or resolved >= num_frames:
        raise ValueError(
            f"--frame-index {frame_index} out of range for {num_frames} frame(s)."
        )
    return resolved


def _find_values_by_key_recursive(node: JsonValue, key_name: str) -> list[JsonValue]:
    """Collect all values for a key in a nested JSON-like structure."""
    found: list[JsonValue] = []
    if isinstance(node, dict):
        for key, value in node.items():
            if key.lower() == key_name:
                found.append(value)
            found.extend(_find_values_by_key_recursive(value, key_name))
    elif isinstance(node, list):
        for item in node:
            found.extend(_find_values_by_key_recursive(item, key_name))
    return found


def _coerce_float(value: Any) -> float | None:
    """Convert unknown value to float if possible."""
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            return float(text)
        except ValueError:
            return None
    return None


def _first_number(record: dict[str, Any], keys: list[str]) -> float | None:
    """Return first parseable number from a list of candidate keys."""
    for key in keys:
        if key in record:
            number = _coerce_float(record[key])
            if number is not None:
                return number
    return None


def _first_string(record: dict[str, Any], keys: list[str]) -> str | None:
    """Return first non-empty string value from candidate keys."""
    for key in keys:
        if key not in record:
            continue
        value = record[key]
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return None


def _looks_like_kind(record: dict[str, Any], kind: str) -> bool:
    """Heuristic filter for furniture-like entries by object kind."""
    type_keys = ["type", "category", "object_type", "class", "label", "name", "kind"]
    for key in type_keys:
        value = record.get(key)
        if value is None:
            continue
        if kind in str(value).strip().lower():
            return True
    return False


def _iter_records(container: JsonValue) -> list[dict[str, Any]]:
    """Yield dict records from list/dict containers."""
    records: list[dict[str, Any]] = []
    if isinstance(container, dict):
        records.append(container)
    elif isinstance(container, list):
        for item in container:
            if isinstance(item, dict):
                records.append(item)
    return records


def _extract_objects(frame: JsonValue, kind: str) -> list[dict[str, Any]]:
    """Extract objects of the requested kind from common fields and nested structures."""
    candidates: list[dict[str, Any]] = []
    seen: set[int] = set()

    if not isinstance(frame, dict):
        return candidates

    # Preferred top-level fields.
    for item in _iter_records(frame.get(f"{kind}s")):
        obj_id = id(item)
        if obj_id not in seen:
            candidates.append(item)
            seen.add(obj_id)

    # Generic furniture field filtered by kind.
    for item in _iter_records(frame.get("furniture")):
        if not _looks_like_kind(item, kind):
            continue
        obj_id = id(item)
        if obj_id not in seen:
            candidates.append(item)
            seen.add(obj_id)

    # Nested structures with same key names.
    for key_name in (f"{kind}s", "furniture"):
        nested_values = _find_values_by_key_recursive(frame, key_name)
        for value in nested_values:
            for item in _iter_records(value):
                if key_name == "furniture" and not _looks_like_kind(item, kind):
                    continue
                obj_id = id(item)
                if obj_id not in seen:
                    candidates.append(item)
                    seen.add(obj_id)

    return candidates


def _detect_input_schema(frame: JsonValue) -> str:
    """Detect the input schema used in the frame."""
    if not isinstance(frame, dict):
        return "unknown"

    if "furniture" in frame:
        furniture = frame["furniture"]
        if isinstance(furniture, list):
            for item in furniture:
                if isinstance(item, dict) and item.get("kind") == "table":
                    if "pose" in item:
                        return "furniture_pose"

    if "tables" in frame or "table" in frame:
        return "standard"

    return "unknown"


def _map_xy_to_roi(
    x: float,
    y: float,
    source_width: float | None,
    source_height: float | None,
    roi_width: float,
    roi_height: float,
) -> tuple[float, float]:
    """Map source coordinates to ROI coordinates (or pass through if mapping is disabled)."""
    if source_width is None or source_height is None:
        return x, y

    if source_width <= 0 or source_height <= 0:
        raise ValueError("--source-width and --source-height must be > 0")

    return (x / source_width) * roi_width, (y / source_height) * roi_height


def _table_from_record(
    record: dict[str, Any],
    fallback_index: int,
    table_width: float,
    table_depth: float,
    source_width: float | None,
    source_height: float | None,
    roi_width: float,
    roi_height: float,
) -> dict[str, Any] | None:
    """Convert a raw object record to AISI table record."""
    x = _first_number(record, ["x", "cx", "center_x"])
    y = _first_number(record, ["y", "cy", "center_y"])

    for key in ("center", "position", "source", "target"):
        nested = record.get(key)
        if not isinstance(nested, dict):
            continue
        if x is None:
            x = _coerce_float(nested.get("x"))
        if y is None:
            y = _coerce_float(nested.get("y"))
        if x is not None and y is not None:
            break

    # Check pose structure (furniture schema)
    if x is None or y is None:
        pose = record.get("pose")
        if isinstance(pose, dict):
            if x is None:
                x = _coerce_float(pose.get("x"))
            if y is None:
                y = _coerce_float(pose.get("y"))

    if x is None or y is None:
        return None

    rot_deg = _first_number(record, ["rot_deg", "angle_deg", "yaw_deg", "rotation"])

    # Check pose.theta (in radians, convert to degrees)
    if rot_deg is None:
        pose = record.get("pose")
        if isinstance(pose, dict):
            theta_rad = _coerce_float(pose.get("theta"))
            if theta_rad is not None:
                rot_deg = theta_rad * 180.0 / math.pi

    if rot_deg is None:
        rot_deg = 0.0

    table_id = _first_string(record, ["id", "track_id", "object_id"])
    if table_id is None:
        table_id = f"table_{fallback_index}"

    mapped_x, mapped_y = _map_xy_to_roi(
        x,
        y,
        source_width=source_width,
        source_height=source_height,
        roi_width=roi_width,
        roi_height=roi_height,
    )

    return {
        "id": table_id,
        "x": mapped_x,
        "y": mapped_y,
        "rot_deg": float(rot_deg),
        "width": float(table_width),
        "depth": float(table_depth),
    }


def convert_snapshot_to_aisi(
    input_path: str | Path,
    output_path: str | Path,
    frame_index: int | None,
    roi_width: float,
    roi_depth: float,
    roi_height: float | None,
    source_width: float | None,
    source_height: float | None,
    table_width: float,
    table_depth: float,
) -> tuple[int, int, str]:
    """Convert source snapshot to AISI scene and write output. Returns (selected_index, table_count, schema)."""
    input_file = Path(input_path)
    output_file = Path(output_path)

    records = _load_records(input_file)
    selected_index = _resolve_frame_index(frame_index, len(records))
    frame = records[selected_index]

    detected_schema = _detect_input_schema(frame)
    coordinate_mapping_enabled = detected_schema == "furniture_pose" and all(
        value is not None for value in (source_width, source_height, roi_width, roi_height)
    )

    if roi_height is None:
        roi_height = roi_depth

    raw_tables = _extract_objects(frame, kind="table")
    tables: list[dict[str, Any]] = []
    for idx, record in enumerate(raw_tables):
        table = _table_from_record(
            record,
            idx,
            table_width=table_width,
            table_depth=table_depth,
            source_width=source_width if coordinate_mapping_enabled else None,
            source_height=source_height if coordinate_mapping_enabled else None,
            roi_width=roi_width,
            roi_height=roi_height,
        )
        if table is not None:
            tables.append(table)

    if not tables:
        raise ValueError(
            "No extractable tables found. Ensure the snapshot contains table objects with x/y fields."
        )

    scene = {
        "roi": {
            "x_min": 0.0,
            "x_max": float(roi_width),
            "y_min": 0.0,
            "y_max": float(roi_height),
        },
        "tables": tables,
    }

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w", encoding="utf-8") as handle:
        json.dump(scene, handle, indent=2)

    return selected_index, len(tables), detected_schema, coordinate_mapping_enabled


def main() -> None:
    args = parse_args()
    selected_frame, table_count, detected_schema, coordinate_mapping_enabled = convert_snapshot_to_aisi(
        input_path=args.input,
        output_path=args.output,
        frame_index=args.frame_index,
        roi_width=args.roi_width,
        roi_depth=args.roi_depth,
        roi_height=args.roi_height,
        source_width=args.source_width,
        source_height=args.source_height,
        table_width=args.table_width,
        table_depth=args.table_depth,
    )

    print(f"Input file: {Path(args.input).resolve()}")
    print(f"Selected frame: {selected_frame}")
    print(f"Extracted tables: {table_count}")
    print(f"Output file: {Path(args.output).resolve()}")
    print(f"schema={detected_schema}")
    print(f"coordinate_mapping={'enabled' if coordinate_mapping_enabled else 'disabled'}")


if __name__ == "__main__":
    main()
