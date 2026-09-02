"""Layout adapter for the AISI simulation pipeline.

This module connects the live simulation scene to the existing AISI layout
pipeline. If the full pipeline fails, it falls back to static presets.
"""

from __future__ import annotations

from typing import Any


GROUPWORK_TARGETS = [
    {"x_cm": 150.0, "y_cm": 160.0, "rotation_deg": 0.0},
    {"x_cm": 350.0, "y_cm": 160.0, "rotation_deg": 0.0},
    {"x_cm": 150.0, "y_cm": 340.0, "rotation_deg": 0.0},
    {"x_cm": 350.0, "y_cm": 340.0, "rotation_deg": 0.0},
]

INPUT_TARGETS = [
    {"x_cm": 140.0, "y_cm": 150.0, "rotation_deg": 0.0},
    {"x_cm": 360.0, "y_cm": 150.0, "rotation_deg": 0.0},
    {"x_cm": 140.0, "y_cm": 260.0, "rotation_deg": 0.0},
    {"x_cm": 360.0, "y_cm": 260.0, "rotation_deg": 0.0},
]

DISCUSSION_TARGETS = [
    {"x_cm": 160.0, "y_cm": 180.0, "rotation_deg": 35.0},
    {"x_cm": 340.0, "y_cm": 180.0, "rotation_deg": -35.0},
    {"x_cm": 160.0, "y_cm": 330.0, "rotation_deg": -35.0},
    {"x_cm": 340.0, "y_cm": 330.0, "rotation_deg": 35.0},
]

LAYOUT_MODES = {
    "input": INPUT_TARGETS,
    "groupwork": GROUPWORK_TARGETS,
    "discussion": DISCUSSION_TARGETS,
}

_DID_WARN_FALLBACK = False


def _static_fallback(learning_format: str) -> list[dict[str, float]]:
    """Return static fallback targets."""

    if learning_format not in LAYOUT_MODES:
        learning_format = "input"

    return LAYOUT_MODES[learning_format]

def _normalize_scene_for_aisi(scene: dict[str, Any]) -> dict[str, Any]:
    """Adapt simulated live_scene.json to the AISI scene format."""

    normalized = dict(scene)

    roi = dict(normalized.get("roi", {}))

    if "x_min" not in roi:
        roi["x_min"] = 0.0
    if "y_min" not in roi:
        roi["y_min"] = 0.0
    if "x_max" not in roi:
        roi["x_max"] = float(roi.get("width_cm", 500.0))
    if "y_max" not in roi:
        roi["y_max"] = float(roi.get("height_cm", 500.0))

    normalized["roi"] = roi

    tables = normalized.get("tables")
    if isinstance(tables, list):
        normalized_tables: list[dict[str, Any]] = []
        for table in tables:
            if not isinstance(table, dict):
                normalized_tables.append(table)
                continue

            normalized_table = dict(table)
            if "x" not in normalized_table and "x_cm" in normalized_table:
                normalized_table["x"] = normalized_table["x_cm"]
            if "y" not in normalized_table and "y_cm" in normalized_table:
                normalized_table["y"] = normalized_table["y_cm"]
            if "width" not in normalized_table and "width_cm" in normalized_table:
                normalized_table["width"] = normalized_table["width_cm"]
            if "height" not in normalized_table and "height_cm" in normalized_table:
                normalized_table["height"] = normalized_table["height_cm"]
            if "rot_deg" not in normalized_table and "rotation_deg" in normalized_table:
                normalized_table["rot_deg"] = normalized_table["rotation_deg"]

            normalized_tables.append(normalized_table)

        normalized["tables"] = normalized_tables

    return normalized


def _get_source_table_center(scene: dict[str, Any]) -> tuple[float, float] | None:
    """Compute average center (x_cm, y_cm) of source tables.

    Returns None if no valid tables with numeric x_cm/y_cm are present.
    """

    tables = scene.get("tables") if isinstance(scene, dict) else None
    if not tables or not isinstance(tables, list):
        return None

    xs: list[float] = []
    ys: list[float] = []
    for t in tables:
        if not isinstance(t, dict):
            continue
        x = t.get("x_cm")
        y = t.get("y_cm")
        if isinstance(x, (int, float)) and isinstance(y, (int, float)):
            xs.append(float(x))
            ys.append(float(y))

    if not xs or not ys:
        return None

    return (sum(xs) / len(xs), sum(ys) / len(ys))


def _clamp(value: float, min_value: float, max_value: float) -> float:
    """Clamp a numeric value between min_value and max_value."""

    try:
        v = float(value)
    except Exception:
        v = 0.0

    if v < min_value:
        return float(min_value)
    if v > max_value:
        return float(max_value)
    return v


def _apply_source_center_offset(scene: dict[str, Any], targets: list[dict[str, float]]) -> list[dict[str, float]]:
    """Apply a small offset to targets based on source tables' center.

    - offset_x = clamp(center_x - 250.0, -80.0, 80.0)
    - offset_y = clamp(center_y - 250.0, -80.0, 80.0)
    - after shift, x_cm is clamped to [66.5, 433.5]
    - after shift, y_cm is clamped to [33.5, 466.5]
    """

    center = _get_source_table_center(scene)
    if center is None:
        return targets

    center_x, center_y = center
    offset_x = _clamp(center_x - 250.0, -80.0, 80.0)
    offset_y = _clamp(center_y - 250.0, -80.0, 80.0)

    out: list[dict[str, float]] = []
    for t in targets:
        if not isinstance(t, dict):
            continue
        x = float(t.get("x_cm", 0.0)) + offset_x
        y = float(t.get("y_cm", 0.0)) + offset_y
        x = _clamp(x, 66.5, 433.5)
        y = _clamp(y, 33.5, 466.5)
        out.append({
            "x_cm": float(x),
            "y_cm": float(y),
            "rotation_deg": float(t.get("rotation_deg", 0.0)),
        })

    return out


def _center_targets_in_roi(targets: list[dict[str, float]]) -> list[dict[str, float]]:
    """Center the group of targets approximately in the ROI around (250,250).

    - If targets is empty, return unchanged.
    - Compute average x/y of targets and shift so the group's center moves
      toward (250.0, 250.0).
    - Limit the center offsets to [-120.0, 120.0].
    - After shifting, clamp x/y to the ROI bounds used elsewhere.
    - rotation_deg is preserved.
    """

    if not targets:
        return targets

    xs: list[float] = []
    ys: list[float] = []
    for t in targets:
        if not isinstance(t, dict):
            continue
        x = t.get("x_cm")
        y = t.get("y_cm")
        try:
            xs.append(float(x))
            ys.append(float(y))
        except Exception:
            continue

    if not xs or not ys:
        return targets

    avg_x = sum(xs) / len(xs)
    avg_y = sum(ys) / len(ys)

    center_offset_x = _clamp(250.0 - avg_x, -120.0, 120.0)
    center_offset_y = _clamp(250.0 - avg_y, -120.0, 120.0)

    out: list[dict[str, float]] = []
    for t in targets:
        if not isinstance(t, dict):
            continue
        x = float(t.get("x_cm", 0.0)) + center_offset_x
        y = float(t.get("y_cm", 0.0)) + center_offset_y
        x = _clamp(x, 66.5, 433.5)
        y = _clamp(y, 33.5, 466.5)
        out.append({
            "x_cm": float(x),
            "y_cm": float(y),
            "rotation_deg": float(t.get("rotation_deg", 0.0)),
        })

    return out

def _compute_with_aisi_pipeline(
    scene: dict[str, Any],
    learning_format: str,
    transformation_strength: float = 0.8,
) -> list[dict[str, float]]:
    """Compute target layout with the existing AISI layout pipeline."""

    from aisi.input.scene_loader import build_scene_state_from_dict
    from aisi.interpretation.scene_interpreter import interpret_scene
    from aisi.schemas.target_schema_engine import get_target_profile
    from aisi.generation.target_structure_generator import generate_target_structure
    from aisi.generation.layout_synthesizer import synthesize_layout

    normalized_scene = _normalize_scene_for_aisi(scene)
    scene_state = build_scene_state_from_dict(normalized_scene, learning_format=learning_format)
    scene_features = interpret_scene(scene_state)
    target_profile = get_target_profile(learning_format)
    target_structure = generate_target_structure(
        scene_state,
        scene_features,
        target_profile,
        transformation_strength=transformation_strength,
    )
    proposal = synthesize_layout(
        scene_state,
        scene_features,
        target_profile,
        target_structure,
        transformation_strength=transformation_strength,
    )

    target_by_id = {target.table_id: target for target in proposal.table_targets}
    targets = []
    for table in scene_state.tables:
        target = target_by_id.get(table.table_id)
        if target is None:
            raise ValueError(f"AISI layout pipeline omitted table_id={table.table_id!r}.")
        targets.append(
            {
                "x_cm": float(target.target_x),
                "y_cm": float(target.target_y),
                "rotation_deg": float(target.target_rot_deg),
            }
        )

    if not targets:
        raise ValueError("AISI layout pipeline returned no table targets.")

    return targets


def _compute_geometry_safe_static_fallback(
    scene: dict[str, Any],
    learning_format: str,
    transformation_strength: float,
) -> list[dict[str, float]]:
    """Bind static slots to scene IDs, then blend, repair, and validate them."""
    from aisi.core.models import TableTarget
    from aisi.core.table_geometry import table_allowed_center_bounds
    from aisi.generation.layout_synthesizer import (
        _apply_hard_constraint_repair,
        _blend_targets_with_source,
        _evaluate_for_learning_format,
        _source_pose_targets,
        _targets_in_scene_order,
    )
    from aisi.input.scene_loader import build_scene_state_from_dict

    normalized_scene = _normalize_scene_for_aisi(scene)
    scene_state = build_scene_state_from_dict(normalized_scene, learning_format=learning_format)
    strength = _clamp(transformation_strength, 0.0, 1.0)
    if strength <= 0.0:
        targets = _source_pose_targets(scene_state)
    else:
        templates = _static_fallback(learning_format)
        targets: list[TableTarget] = []
        for index, table in enumerate(scene_state.tables):
            if index < len(templates):
                template = templates[index]
                rotation = float(template["rotation_deg"])
                x_min, x_max, y_min, y_max = table_allowed_center_bounds(
                    table,
                    rotation,
                    x_min=scene_state.roi.x_min,
                    x_max=scene_state.roi.x_max,
                    y_min=scene_state.roi.y_min,
                    y_max=scene_state.roi.y_max,
                )
                x = _clamp(float(template["x_cm"]), x_min, x_max)
                y = _clamp(float(template["y_cm"]), y_min, y_max)
            else:
                x, y, rotation = table.x, table.y, table.rot_deg
            targets.append(
                TableTarget(
                    table_id=table.table_id,
                    target_x=x,
                    target_y=y,
                    source_rot_deg=table.rot_deg,
                    target_rot_deg=rotation,
                )
            )

        targets = _blend_targets_with_source(scene_state, targets, strength)
        notes = ["fallback=static_geometry_safe", f"transformation_strength={strength:.3f}"]
        targets, repair_notes = _apply_hard_constraint_repair(scene_state, targets, notes)
        notes.extend(repair_notes)
        stats = _evaluate_for_learning_format(scene_state, targets, notes)
        if stats.overlap_violations or stats.roi_violations:
            raise ValueError(
                "Static fallback remains invalid: "
                f"overlap={stats.overlap_violations}, roi={stats.roi_violations}, "
                f"clearance={stats.clearance_violations}"
            )
        if stats.clearance_violations:
            print(
                "[sim_layout_rules] Static fallback has remaining seat-clearance "
                f"violations: {stats.clearance_violations}"
            )

    ordered = _targets_in_scene_order(scene_state, targets)
    return [
        {
            "x_cm": float(target.target_x),
            "y_cm": float(target.target_y),
            "rotation_deg": float(target.target_rot_deg),
        }
        for target in ordered
    ]


def _source_pose_fallback(scene: dict[str, Any]) -> list[dict[str, float]]:
    """Last-resort contract-preserving source poses; validity is not implied."""
    result: list[dict[str, float]] = []
    for table in scene.get("tables", []):
        if not isinstance(table, dict):
            continue
        result.append(
            {
                "x_cm": float(table.get("x_cm", table.get("x", 0.0))),
                "y_cm": float(table.get("y_cm", table.get("y", 0.0))),
                "rotation_deg": float(table.get("rotation_deg", table.get("rot_deg", 0.0))),
            }
        )
    return result


def _blend_generated_targets_with_source(
    scene: dict[str, Any],
    generated_targets: list[dict[str, float]],
    transformation_strength: float,
) -> list[dict[str, float]]:
    """Blend generated targets toward the source scene using the given strength."""

    strength = _clamp(transformation_strength, 0.0, 1.0)
    source_tables = scene.get("tables") if isinstance(scene, dict) else None
    if not isinstance(source_tables, list):
        source_tables = []

    blended_targets: list[dict[str, float]] = []
    for index, generated_target in enumerate(generated_targets):
        if not isinstance(generated_target, dict):
            continue

        if index >= len(source_tables) or not isinstance(source_tables[index], dict):
            blended_targets.append({
                "x_cm": float(generated_target.get("x_cm", 0.0)),
                "y_cm": float(generated_target.get("y_cm", 0.0)),
                "rotation_deg": float(generated_target.get("rotation_deg", 0.0)),
            })
            continue

        source_table = source_tables[index]
        source_x = float(source_table.get("x_cm", 0.0))
        source_y = float(source_table.get("y_cm", 0.0))
        source_rot = float(source_table.get("rotation_deg", 0.0))

        target_x = float(generated_target.get("x_cm", 0.0))
        target_y = float(generated_target.get("y_cm", 0.0))
        target_rot = float(generated_target.get("rotation_deg", 0.0))

        blended_targets.append({
            "x_cm": source_x + strength * (target_x - source_x),
            "y_cm": source_y + strength * (target_y - source_y),
            "rotation_deg": source_rot + strength * (target_rot - source_rot),
        })

    return blended_targets


def compute_target_layout(
    scene: dict,
    learning_format: str,
    transformation_strength: float = 0.5,
) -> list[dict[str, float]]:
    """Return target table layout for the selected learning format."""

    global _DID_WARN_FALLBACK

    if learning_format not in LAYOUT_MODES:
        learning_format = "input"

    try:
        return _compute_with_aisi_pipeline(
            scene,
            learning_format,
            transformation_strength=transformation_strength,
        )
    except Exception as exc:
        if not _DID_WARN_FALLBACK:
            print(f"[sim_layout_rules] Falling back to static targets: {exc}")
            _DID_WARN_FALLBACK = True

        try:
            return _compute_geometry_safe_static_fallback(
                scene,
                learning_format,
                transformation_strength,
            )
        except Exception as fallback_exc:
            print(
                "[sim_layout_rules] Geometry-safe static fallback failed; returning "
                f"source poses without claiming validity: {fallback_exc}"
            )
            return _source_pose_fallback(scene)
