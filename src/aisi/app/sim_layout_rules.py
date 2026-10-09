"""Layout adapter for the AISI simulation pipeline.

This module connects the live simulation scene to the existing AISI layout
pipeline. If the full pipeline fails, it falls back to static presets.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations, permutations
import math
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


@dataclass(frozen=True, slots=True)
class SyntheticLayoutOutput:
    """Table targets plus optional synthetic chair markers for the simulator.

    Chair generation is deliberately opt-in.  The established layout API still
    returns table targets alone, so existing OSC and TouchDesigner consumers
    retain their contract until the simulation preview is enabled explicitly.
    """

    table_targets: list[dict[str, float]]
    chairs: list[dict[str, float | str]]
    active_table_ids: tuple[str, ...] = ()
    parked_table_ids: tuple[str, ...] = ()
    presentation_side: str | None = None


SYNTHETIC_CHAIR_RADIUS_CM = 25.0
INPUT_SEAT_CLEARANCE_DEPTH_CM = 70.0


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
        except ValueError:
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
    *,
    input_presentation_side: str | None = None,
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
        **({"input_presentation_side": input_presentation_side} if input_presentation_side is not None else {}),
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


def _participant_aware_input_preview(
    scene: dict[str, Any],
    transformation_strength: float,
    activity_parameters: dict[str, Any],
) -> SyntheticLayoutOutput:
    """Build a table-only Input preview on top of the accepted generator.

    Only the active subset is passed through the existing AISI synthesizer.
    Thus its accepted Rect Input target semantics remain authoritative instead
    of being replaced by a second, static target grid.  Remaining visible
    tables receive derived edge parking poses. Chairs deliberately remain
    outside this planning step until the table topology is accepted.
    """

    from aisi.core.models import TableTarget
    from aisi.generation.adaptive_layout_v1 import (
        LayoutConstraintError,
        _parking_candidates,
    )
    from aisi.generation.layout_synthesizer import (
        _rect_input_clearance_regions,
        _rect_input_presenter_and_axis,
    )
    from aisi.input.scene_loader import build_scene_state_from_dict

    normalized_scene = _normalize_scene_for_aisi(scene)
    scene_state = build_scene_state_from_dict(normalized_scene, learning_format="input")
    if len(scene_state.tables) > 5:
        raise LayoutConstraintError("Die Input-Vorschau unterstützt höchstens fünf Tische.")
    side = activity_parameters.get("presentation_side")
    if side not in {None, "north", "east", "south", "west"}:
        raise LayoutConstraintError(f"Ungültige Präsentationsseite: {side!r}.")
    participants = int(activity_parameters.get("participants", 4))
    rect_tables = sorted((table for table in scene_state.tables if table.table_type == "rect"), key=lambda table: table.table_id)
    if participants < 1:
        raise LayoutConstraintError("Die Teilnehmerzahl muss mindestens 1 sein.")
    if participants > 3 * len(rect_tables):
        raise LayoutConstraintError(
            f"{participants} Teilnehmende benötigen mehr als drei Personen pro verfügbarem Rect-Tisch."
        )
    required = min(len(rect_tables), math.ceil(participants / 2.0))
    raw_by_id = {
        str(table.get("id")): table
        for table in normalized_scene.get("tables", [])
        if isinstance(table, dict)
    }
    best: tuple[tuple[float, float, tuple[str, ...]], list[TableTarget], tuple[str, ...]] | None = None
    for active in combinations(rect_tables, required):
        active_ids = {table.table_id for table in active}
        active_scene = dict(normalized_scene)
        active_scene["tables"] = [raw_by_id[table.table_id] for table in active]
        try:
            generated = _compute_with_aisi_pipeline(active_scene, "input", transformation_strength, input_presentation_side=side)
            active_targets = [
                TableTarget(table.table_id, float(target["x_cm"]), float(target["y_cm"]), table.rot_deg, float(target["rotation_deg"]))
                for table, target in zip(active, generated)
            ]
            presenter, presentation_axis = _rect_input_presenter_and_axis(list(active), side)
            active_clearance_regions = _rect_input_clearance_regions(
                active_targets,
                list(active),
                presenter.table_id,
                presentation_axis,
            )
            parked = sorted((table for table in scene_state.tables if table.table_id not in active_ids), key=lambda table: table.table_id)
            # Zero strength preserves all source poses, including parked
            # tables. Joint seating validity is claimed only at full strength.
            parked_targets = [
                TableTarget(table.table_id, table.x, table.y, table.rot_deg, table.rot_deg)
                for table in parked
            ] if transformation_strength <= 0.0 else _compact_park_targets(
                scene_state,
                parked,
                active_targets,
                _parking_candidates(activity_parameters.get("presentation_side")),
                exclusion_regions=active_clearance_regions,
            )
            all_targets = [*active_targets, *parked_targets]
        except ValueError:
            continue
        by_id = {target.table_id: target for target in all_targets}
        distances = [math.dist((table.x, table.y), (by_id[table.table_id].target_x, by_id[table.table_id].target_y)) for table in scene_state.tables]
        score = (max(distances, default=0.0), math.fsum(distances), tuple(sorted(active_ids)))
        if best is None or score < best[0]:
            best = (score, all_targets, tuple(sorted(active_ids)))
    if best is None:
        raise LayoutConstraintError("Keine footprint-sichere aktive/parkende Input-Tischplanung gefunden.")
    all_targets = best[1]
    selected_active_ids = best[2]

    target_by_id = {target.table_id: target for target in all_targets}
    ordered = [
        {
            "x_cm": float(target_by_id[table.table_id].target_x),
            "y_cm": float(target_by_id[table.table_id].target_y),
            "rotation_deg": float(target_by_id[table.table_id].target_rot_deg),
        }
        for table in scene_state.tables
    ]
    return SyntheticLayoutOutput(
        table_targets=ordered,
        chairs=[],
        active_table_ids=selected_active_ids,
        parked_table_ids=tuple(table.table_id for table in scene_state.tables if table.table_id not in selected_active_ids),
        presentation_side=side,
    )


def _compact_park_targets(
    scene_state: Any,
    parked: list[Any],
    active_targets: list[Any],
    candidates: tuple[tuple[float, float, float], ...],
    *,
    exclusion_regions: list[tuple[tuple[float, float], ...]],
    edge_aligned: bool = False,
    min_active_gap_cm: float = 0.0,
    prefer_short_movement: bool = False,
) -> list[Any]:
    """Choose compact edge bays outside active tables and their seat zones."""
    from aisi.core.models import TableTarget
    from aisi.core.table_geometry import convex_polygons_intersect, polygon_inside_roi, table_world_footprint, table_allowed_center_bounds

    if not parked:
        return []
    active_by_id = {table.table_id: table for table in scene_state.tables}
    occupied = [table_world_footprint(active_by_id[target.table_id], (target.target_x, target.target_y), target.target_rot_deg) for target in active_targets]
    gap_cache = {}

    def active_gap_ok(table_id, x, y, rotation, footprint):
        if min_active_gap_cm <= 0.:
            return True
        from aisi.analysis.rect_groupwork_adaptive_prototype import _polygon_distance
        key = (table_id,x,y,rotation)
        if key not in gap_cache:
            gap_cache[key] = all(_polygon_distance(footprint,other) >= min_active_gap_cm-1e-7
                                 for other in occupied)
        return gap_cache[key]

    best: tuple[tuple[float, float], list[TableTarget]] | None = None
    for slots in permutations(candidates, len(parked)):
        proposed: list[TableTarget] = []
        footprints = list(occupied)
        valid = True
        for table, (x, y, rotation) in zip(parked, slots):
            if edge_aligned:
                x0,y0,x1,y1 = table_allowed_center_bounds(table,rotation,
                    x_min=scene_state.roi.x_min,y_min=scene_state.roi.y_min,
                    x_max=scene_state.roi.x_max,y_max=scene_state.roi.y_max)
                if abs(rotation % 180.) < 1e-8:
                    y = y0 if y < (scene_state.roi.y_min+scene_state.roi.y_max)/2 else y1
                    x = min(max(x,x0),x1)
                else:
                    x = x0 if x < (scene_state.roi.x_min+scene_state.roi.x_max)/2 else x1
                    y = min(max(y,y0),y1)
            footprint = table_world_footprint(table, (x, y), rotation)
            if (
                not polygon_inside_roi(footprint, x_min=scene_state.roi.x_min, y_min=scene_state.roi.y_min, x_max=scene_state.roi.x_max, y_max=scene_state.roi.y_max)
                or any(convex_polygons_intersect(footprint, other) for other in footprints)
                or any(convex_polygons_intersect(footprint, region) for region in exclusion_regions)
                or not active_gap_ok(table.table_id,x,y,rotation,footprint)
            ):
                valid = False
                break
            proposed.append(TableTarget(table.table_id, x, y, table.rot_deg, rotation))
            footprints.append(footprint)
        if not valid:
            continue
        xs, ys = zip(*((target.target_x, target.target_y) for target in proposed))
        compactness = (max(xs) - min(xs)) + (max(ys) - min(ys))
        movement = sum(math.dist((table.x, table.y), (target.target_x, target.target_y)) for table, target in zip(parked, proposed))
        score = (movement, compactness) if prefer_short_movement else (compactness, movement)
        if best is None or score < best[0]:
            best = (score, proposed)
    if best is None:
        raise ValueError("Keine kompakte, footprint-sichere Parkbuchtenkombination gefunden.")
    return best[1]


def plan_synthetic_input_chairs(
    scene: dict[str, Any],
    layout: SyntheticLayoutOutput,
    participants: int,
) -> list[dict[str, float | str]]:
    """Derive review-only Input chair markers from accepted active table roles.

    This helper deliberately has no OSC side effect.  It is used first by the
    offline plot so chair geometry can be reviewed before the live sender is
    allowed to publish it.
    """
    from aisi.core.models import TableTarget, long_axis_unit_vector
    from aisi.core.table_geometry import table_support_distance
    from aisi.generation.layout_synthesizer import _rect_input_presenter_and_axis
    from aisi.input.scene_loader import build_scene_state_from_dict

    normalized_scene = _normalize_scene_for_aisi(scene)
    state = build_scene_state_from_dict(normalized_scene, learning_format="input")
    active_tables = sorted((table for table in state.tables if table.table_id in layout.active_table_ids), key=lambda table: table.table_id)
    if participants < 1 or not active_tables:
        return []
    if participants > len(active_tables) * 3:
        raise ValueError("Die angeforderte Chair-Kapazität überschreitet drei Personen pro aktivem Tisch.")

    target_by_id = {
        table.table_id: TableTarget(
            table_id=table.table_id,
            target_x=item["x_cm"],
            target_y=item["y_cm"],
            source_rot_deg=table.rot_deg,
            target_rot_deg=item["rotation_deg"],
        )
        for table, item in zip(state.tables, layout.table_targets)
    }
    presenter, presentation_axis = _rect_input_presenter_and_axis(active_tables, layout.presentation_side)
    base, extra = divmod(participants, len(active_tables))
    counts = [base + (1 if index < extra else 0) for index in range(len(active_tables))]
    if max(counts, default=0) > 3:
        raise ValueError("Die Chair-Verteilung überschreitet die Input-Kapazität pro Tisch.")

    markers: list[dict[str, float | str]] = []
    for table, count in zip(active_tables, counts):
        target = target_by_id[table.table_id]
        seat_direction = (
            presentation_axis
            if table.table_id == presenter.table_id
            else (-presentation_axis[0], -presentation_axis[1])
        )
        long_axis = long_axis_unit_vector(target.target_rot_deg)
        # Room-fit may rotate the generated formation away from the source
        # axis. Use the same directed target normal as canonical seat regions.
        normal = (-long_axis[1], long_axis[0])
        if normal[0] * seat_direction[0] + normal[1] * seat_direction[1] < 0.0:
            normal = (-normal[0], -normal[1])
        seat_direction = normal
        offsets = {1: (0.0,), 2: (-40.0, 40.0), 3: (-52.0, 0.0, 52.0)}[count]
        seat_distance = table_support_distance(table, target.target_rot_deg, seat_direction) + INPUT_SEAT_CLEARANCE_DEPTH_CM * 0.5
        for offset in offsets:
            markers.append({
                "x_cm": target.target_x + long_axis[0] * offset + seat_direction[0] * seat_distance,
                "y_cm": target.target_y + long_axis[1] * offset + seat_direction[1] * seat_distance,
                "radius_cm": SYNTHETIC_CHAIR_RADIUS_CM,
                "table_id": table.table_id,
            })
    return markers


def compute_synthetic_layout(
    scene: dict[str, Any],
    learning_format: str,
    transformation_strength: float = 0.5,
    activity_parameters: dict[str, Any] | None = None,
) -> SyntheticLayoutOutput:
    """Return simulation-only tables and chairs without changing normal modes."""

    parameters = activity_parameters or {}
    preview_enabled = parameters.get("adaptive_layout_preview") is True
    if preview_enabled and learning_format == "groupwork":
        from aisi.generation.groupwork_participants import plan_participant_groupwork, transform_groupwork_plan
        from aisi.generation.adaptive_layout_v1 import LayoutConstraintError
        from aisi.input.scene_loader import build_scene_state_from_dict
        participants = parameters.get("participants", 4)
        groups = parameters.get("number_of_groups", 1)
        if type(participants) is not int or type(groups) is not int or not 1 <= groups <= participants:
            raise LayoutConstraintError("Groupwork benötigt gültige ganzzahlige Teilnehmer-/Gruppenzahlen.")
        if participants > 15:
            raise LayoutConstraintError("Groupwork-Ausgabe überschreitet die technischen 15 TD-Chair-Slots; keine Kürzung.")
        state = build_scene_state_from_dict(_normalize_scene_for_aisi(scene), learning_format="groupwork")
        strength = float(transformation_strength)
        if not math.isfinite(strength):
            raise LayoutConstraintError("Ungültige Transformationsstärke.")
        strength = max(0.0, min(1.0, strength))
        if strength == 0.0:
            return SyntheticLayoutOutput(
                table_targets=[{"x_cm": t.x, "y_cm": t.y, "rotation_deg": t.rot_deg} for t in state.tables],
                chairs=[],
            )
        plan = plan_participant_groupwork(state, participants, groups)
        if strength < 1.0:
            plan = transform_groupwork_plan(state, plan, strength)
        active = {tid for cluster in plan.clusters for tid in cluster.table_ids}
        return SyntheticLayoutOutput(
            table_targets=[{"x_cm": t.target_x, "y_cm": t.target_y, "rotation_deg": t.target_rot_deg} for t in plan.targets],
            chairs=plan.chairs,
            active_table_ids=tuple(t.table_id for t in state.tables if t.table_id in active),
            parked_table_ids=plan.parked_table_ids,
        )
    if preview_enabled and learning_format == "discussion":
        from aisi.generation.discussion_chairs import plan_discussion_chairs
        from aisi.generation.adaptive_layout_v1 import LayoutConstraintError
        from aisi.input.scene_loader import build_scene_state_from_dict
        from aisi.core.models import TableTarget
        participants=parameters.get("participants",4)
        if type(participants) is not int or participants<1:
            raise LayoutConstraintError("Discussion benötigt eine positive ganzzahlige Teilnehmerzahl.")
        if participants>15:
            raise LayoutConstraintError("Discussion-Ausgabe überschreitet die technischen 15 TD-Chair-Slots; keine Kürzung.")
        strength=float(transformation_strength)
        if not math.isfinite(strength):
            raise LayoutConstraintError("Ungültige Transformationsstärke.")
        strength=max(0.,min(1.,strength))
        state=build_scene_state_from_dict(_normalize_scene_for_aisi(scene),learning_format="discussion")
        if strength==0.:
            return SyntheticLayoutOutput(table_targets=[dict(x_cm=t.x,y_cm=t.y,rotation_deg=t.rot_deg) for t in state.tables],chairs=[])
        if strength<1.:
            # Retain the existing blend-before-repair path; reject clearly if
            # its partial poses cannot accommodate the requested outside chairs.
            poses=_compute_with_aisi_pipeline(scene,"discussion",strength)
            targets=[TableTarget(t.table_id,p["x_cm"],p["y_cm"],source_rot_deg=t.rot_deg,target_rot_deg=p["rotation_deg"])
                     for t,p in zip(state.tables,poses)]
            plan=plan_discussion_chairs(state,participants,targets)
        else:
            plan=plan_discussion_chairs(state,participants)
        return SyntheticLayoutOutput(table_targets=[dict(x_cm=t.target_x,y_cm=t.target_y,rotation_deg=t.target_rot_deg)
            for t in plan.targets],chairs=plan.chairs,active_table_ids=tuple(t.table_id for t in state.tables),parked_table_ids=())
    if preview_enabled and learning_format == "input":
        table_plan = _participant_aware_input_preview(scene, transformation_strength, parameters)
        chairs = plan_synthetic_input_chairs(scene, table_plan, int(parameters.get("participants", 4)))
        result = SyntheticLayoutOutput(
            table_targets=table_plan.table_targets,
            chairs=chairs,
            active_table_ids=table_plan.active_table_ids,
            parked_table_ids=table_plan.parked_table_ids,
            presentation_side=table_plan.presentation_side,
        )
        if transformation_strength >= 1.0 - 1e-9:
            validate_synthetic_input_geometry(scene, result)
        return result
    return SyntheticLayoutOutput(
        table_targets=compute_target_layout(
            scene,
            learning_format,
            transformation_strength,
            activity_parameters=activity_parameters,
        ),
        chairs=[],
    )


def compute_target_layout(
    scene: dict,
    learning_format: str,
    transformation_strength: float = 0.5,
    activity_parameters: dict[str, Any] | None = None,
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


def validate_synthetic_input_geometry(scene: dict[str, Any], layout: SyntheticLayoutOutput) -> None:
    """Reject invalid combined Input targets using the canonical geometry."""
    from aisi.core.models import TableTarget
    from aisi.core.table_geometry import (
        circle_inside_convex_polygon, circle_intersects_convex_polygon,
        convex_polygons_intersect, polygon_inside_roi, table_world_footprint,
    )
    from aisi.generation.adaptive_layout_v1 import LayoutConstraintError
    from aisi.generation.layout_synthesizer import _rect_input_clearance_regions, _rect_input_presenter_and_axis
    from aisi.input.scene_loader import build_scene_state_from_dict

    state = build_scene_state_from_dict(_normalize_scene_for_aisi(scene), learning_format="input")
    if len(layout.table_targets) != len(state.tables):
        raise LayoutConstraintError("Input-Ziele müssen alle Source-Tische in Scene Order enthalten.")
    targets = [TableTarget(table.table_id, item["x_cm"], item["y_cm"], table.rot_deg, item["rotation_deg"])
               for table, item in zip(state.tables, layout.table_targets)]
    active = [table for table in state.tables if table.table_id in layout.active_table_ids]
    presenter, axis = _rect_input_presenter_and_axis(active, layout.presentation_side)
    active_targets = [target for target in targets if target.table_id in layout.active_table_ids]
    regions = dict(zip((target.table_id for target in active_targets),
                       _rect_input_clearance_regions(active_targets, active, presenter.table_id, axis)))
    footprints = {target.table_id: table_world_footprint(table, (target.target_x, target.target_y), target.target_rot_deg)
                  for table, target in zip(state.tables, targets)}
    roi = state.roi
    for polygon in [*footprints.values(), *regions.values()]:
        if not polygon_inside_roi(polygon, x_min=roi.x_min, y_min=roi.y_min, x_max=roi.x_max, y_max=roi.y_max):
            raise LayoutConstraintError("Input-Footprint oder Sitzfläche liegt außerhalb der ROI.")
    for index, polygon in enumerate(footprints.values()):
        if any(convex_polygons_intersect(polygon, other) for other in list(footprints.values())[index + 1:]):
            raise LayoutConstraintError("Input-Tischziele kollidieren.")
    for table_id, region in regions.items():
        if any(convex_polygons_intersect(region, polygon) for other_id, polygon in footprints.items() if other_id != table_id):
            raise LayoutConstraintError("Ein Tisch blockiert eine aktive Input-Sitz-/Bewegungsfläche.")
    for index, region in enumerate(regions.values()):
        if any(convex_polygons_intersect(region, other) for other in list(regions.values())[index + 1:]):
            raise LayoutConstraintError("Aktive Input-Sitz-/Bewegungsflächen überschneiden sich.")
    for index, chair in enumerate(layout.chairs):
        center = (float(chair["x_cm"]), float(chair["y_cm"]))
        radius = float(chair["radius_cm"])
        region = regions.get(str(chair["table_id"]))
        if region is None or not circle_inside_convex_polygon(center, radius, region):
            raise LayoutConstraintError("Ein Chair liegt nicht vollständig in seiner aktiven Sitzfläche.")
        if any(circle_intersects_convex_polygon(center, radius, polygon) for polygon in footprints.values()):
            raise LayoutConstraintError("Ein Chair kollidiert mit einem Input-Tisch.")
        if any(math.dist(center, (float(other["x_cm"]), float(other["y_cm"]))) <= radius + float(other["radius_cm"]) + 1e-9
               for other in layout.chairs[index + 1:]):
            raise LayoutConstraintError("Input-Chairs kollidieren.")
