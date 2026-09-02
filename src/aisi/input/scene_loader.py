from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from aisi.core.models import ChairState, ROI, SceneState, TableState
from aisi.core.table_geometry import TABLE_GEOMETRIES, normalize_table_type


LEGACY_DEFAULT_TABLE_WIDTH = 110.0
LEGACY_DEFAULT_TABLE_HEIGHT = 70.0


def load_scene_json(path: str | Path) -> dict[str, Any]:
    """Load a scene dict from JSON or first line of JSONL."""
    source = Path(path)
    with source.open("r", encoding="utf-8") as handle:
        if source.suffix.lower() == ".jsonl":
            for line in handle:
                stripped = line.strip()
                if stripped:
                    return json.loads(stripped)
            raise ValueError(f"No JSON object found in JSONL file: {source}")
        return json.load(handle)


def build_scene_state_from_dict(scene_dict: dict[str, Any], learning_format: str) -> SceneState:
    """Build a typed SceneState from a plain dictionary payload."""
    roi = _build_roi(scene_dict)
    tables = _build_tables(scene_dict)
    chairs = _build_chairs(scene_dict)

    return SceneState(
        roi=roi,
        tables=tables,
        chairs=chairs,
        people=[],
        learning_format=learning_format,  # caller controls explicit test format
    )


def build_scene_state_from_json(path: str | Path, learning_format: str) -> SceneState:
    """Load a scene from disk and convert to SceneState."""
    return build_scene_state_from_dict(load_scene_json(path), learning_format)


def _build_roi(scene_dict: dict[str, Any]) -> ROI:
    roi_dict = scene_dict.get("roi")
    if not isinstance(roi_dict, dict):
        raise ValueError("Scene must contain roi with x_min, y_min, x_max, y_max")

    return ROI(
        x_min=float(roi_dict["x_min"]),
        y_min=float(roi_dict["y_min"]),
        x_max=float(roi_dict["x_max"]),
        y_max=float(roi_dict["y_max"]),
    )


def _build_tables(scene_dict: dict[str, Any]) -> list[TableState]:
    raw_tables = _extract_objects(scene_dict, target_kind="table", explicit_key="tables")
    tables: list[TableState] = []
    for index, item in enumerate(raw_tables):
        pose = item.get("pose", item)
        table_type = normalize_table_type(item.get("type"))
        rot_deg = _safe_float(item.get("rot_deg"))
        if rot_deg is None:
            rot_deg = _safe_float(pose.get("rot_deg"))
        if rot_deg is None:
            rot_deg = 0.0
        if table_type in TABLE_GEOMETRIES:
            geometry = TABLE_GEOMETRIES[table_type]
            width = geometry.nominal_width
            height = geometry.nominal_depth
        else:
            width = _read_dimension(
                item,
                pose,
                primary_keys=("width",),
                fallback_keys=(),
                default=LEGACY_DEFAULT_TABLE_WIDTH,
            )
            height = _read_dimension(
                item,
                pose,
                primary_keys=("height", "depth"),
                fallback_keys=("depth",),
                default=LEGACY_DEFAULT_TABLE_HEIGHT,
            )
        tables.append(
            TableState(
                table_id=str(item.get("id") or f"table_{index:02d}"),
                x=float(pose.get("x", 0.0)),
                y=float(pose.get("y", 0.0)),
                rot_deg=float(rot_deg),
                width=width,
                height=height,
                confidence=_safe_float(item.get("confidence")),
                table_type=table_type,
            )
        )
    return tables


def _build_chairs(scene_dict: dict[str, Any]) -> list[ChairState]:
    raw_chairs = _extract_objects(scene_dict, target_kind="chair", explicit_key="chairs")
    chairs: list[ChairState] = []
    for index, item in enumerate(raw_chairs):
        pose = item.get("pose", item)
        chairs.append(
            ChairState(
                chair_id=str(item.get("id") or f"chair_{index:02d}"),
                x=float(pose.get("x", 0.0)),
                y=float(pose.get("y", 0.0)),
                width=float(item.get("width", 45.0)),
                height=float(item.get("height", 45.0)),
                confidence=_safe_float(item.get("confidence")),
            )
        )
    return chairs


def _extract_objects(
    scene_dict: dict[str, Any], target_kind: str, explicit_key: str
) -> list[dict[str, Any]]:
    if explicit_key in scene_dict and isinstance(scene_dict[explicit_key], list):
        return [item for item in scene_dict[explicit_key] if isinstance(item, dict)]

    furniture = scene_dict.get("furniture")
    if isinstance(furniture, list):
        return [
            item
            for item in furniture
            if isinstance(item, dict) and str(item.get("kind", "")).lower() == target_kind
        ]

    return []


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _read_dimension(
    item: dict[str, Any],
    pose: dict[str, Any],
    primary_keys: tuple[str, ...],
    fallback_keys: tuple[str, ...],
    default: float,
) -> float:
    for key in primary_keys:
        value = _safe_float(item.get(key))
        if value is not None:
            return value
        value = _safe_float(pose.get(key))
        if value is not None:
            return value

    for key in fallback_keys:
        value = _safe_float(item.get(key))
        if value is not None:
            return value
        value = _safe_float(pose.get(key))
        if value is not None:
            return value

    return default
