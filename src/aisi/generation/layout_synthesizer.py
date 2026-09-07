from __future__ import annotations

import math
from statistics import mean, median

from aisi.core.models import (
    LayoutProposal,
    Point2D,
    SceneFeatures,
    SceneState,
    TableState,
    TableTarget,
    TargetProfile,
    TargetStructure,
    long_axis_rotation_from_facing_vector,
)
from aisi.core.table_geometry import (
    required_table_center_separation,
    resolve_table_state_geometry,
    table_allowed_center_bounds,
    table_support_distance,
    table_world_footprint,
)
from aisi.generation.assignment_utils import score_format_bound_targets
from aisi.generation.layout_constraints import evaluate_hard_constraints, repair_layout_hard_constraints
from aisi.generation.target_structure_generator import pair_tables_for_groupwork


GROUPWORK_PAIR_SEAM_GAP_CM = 4.0
INPUT_TABLE_GAP_CM = 8.0
RECT_TEMPLATE_MAX_TABLES = 6
RECT_INPUT_TWO_COLUMN_SPACING_CM = 220.0
RECT_INPUT_ROW_SPACING_CM = 190.0


def synthesize_layout(
    scene_state: SceneState,
    scene_features: SceneFeatures,
    target_profile: TargetProfile,
    target_structure: TargetStructure,
    transformation_strength: float = 0.5,
) -> LayoutProposal:
    """Synthesize adaptive table-only layouts from target structure + current scene."""
    tables = sorted(scene_state.tables, key=lambda table: table.table_id)
    strength = _clamp(transformation_strength, 0.0, 1.0)

    if strength <= 0.0:
        return LayoutProposal(
            table_targets=_source_pose_targets(scene_state),
            chair_targets=[],
            generation_notes=[
                "transformation_strength=0.000",
                "transformation_strength_zero=exact_source_no_repair",
                "assignment_strategy=format_bound",
            ],
        )

    if _uses_rect_template_layout(tables):
        targets, notes = _layout_rect_templates(scene_state, tables)
    elif scene_state.learning_format == "input":
        targets, notes = _layout_input_adaptive(
            scene_state,
            tables,
            target_structure,
            transformation_strength=transformation_strength,
        )
    elif scene_state.learning_format == "groupwork":
        targets, notes = _layout_groupwork_adaptive(
            scene_state,
            tables,
            target_structure,
            transformation_strength=transformation_strength,
        )
    else:
        targets, notes = _layout_discussion_adaptive(
            scene_state,
            tables,
            target_structure,
            transformation_strength=transformation_strength,
        )

    assignment_result = score_format_bound_targets(scene_state, targets)
    targets = assignment_result.table_targets
    notes = [*notes, *assignment_result.notes]

    targets = _blend_targets_with_source(scene_state, targets, strength)
    notes.append(f"transformation_strength={strength:.3f}")

    repaired_targets, repair_notes = _apply_hard_constraint_repair(scene_state, targets, notes)
    notes = [*notes, *repair_notes]

    final_stats = _evaluate_for_learning_format(scene_state, repaired_targets, notes)
    if final_stats.overlap_violations or final_stats.roi_violations:
        raise ValueError(
            "Final layout violates hard table geometry: "
            f"overlap={final_stats.overlap_violations}, roi={final_stats.roi_violations}"
        )
    if final_stats.clearance_violations:
        notes.append(f"final_clearance_violations={final_stats.clearance_violations}")

    return LayoutProposal(
        table_targets=_targets_in_scene_order(scene_state, repaired_targets),
        chair_targets=[],
        generation_notes=notes,
    )


def _uses_rect_template_layout(tables: list[TableState]) -> bool:
    """Return whether a small all-rect scene uses the restored template path."""
    return 1 <= len(tables) <= RECT_TEMPLATE_MAX_TABLES and all(
        table.table_type == "rect" for table in tables
    )


def _layout_rect_templates(
    scene_state: SceneState,
    tables: list[TableState],
) -> tuple[list[TableTarget], list[str]]:
    """Build deterministic, ID-bound layouts for the historical rect workflow."""
    if scene_state.learning_format == "input":
        return _layout_rect_input_templates(scene_state, tables)
    if scene_state.learning_format == "groupwork":
        return _layout_rect_groupwork_templates(scene_state, tables)
    return _layout_rect_discussion_templates(scene_state, tables)


def _layout_rect_input_templates(
    scene_state: SceneState,
    tables: list[TableState],
) -> tuple[list[TableTarget], list[str]]:
    """Restore frontal rect rows with spacing that satisfies current clearance."""
    occupancy_by_count = {
        1: (1,),
        2: (2,),
        3: (2, 1),
        4: (2, 2),
        5: (3, 2),
        6: (3, 3),
    }
    occupancy = occupancy_by_count[len(tables)]
    row_y = (250.0,) if len(occupancy) == 1 else (155.0, 345.0)
    rotation_deg = long_axis_rotation_from_facing_vector((0.0, -1.0), reference_rot_deg=0.0)

    slots: list[tuple[float, float]] = []
    for row_size, y in zip(occupancy, row_y):
        slots.extend((x, y) for x in _rect_input_row_x_positions(tables[0], row_size))

    targets = [
        TableTarget(
            table_id=table.table_id,
            target_x=slot[0],
            target_y=slot[1],
            source_rot_deg=table.rot_deg,
            target_rot_deg=rotation_deg,
            facing_target_x=slot[0],
            facing_target_y=slot[1] - 100.0,
        )
        for table, slot in zip(tables, slots)
    ]
    return targets, [
        "rect_template=input",
        f"rect_input_occupancy={list(occupancy)}",
        f"rect_input_two_column_spacing_cm={RECT_INPUT_TWO_COLUMN_SPACING_CM:.1f}",
        f"rect_input_row_spacing_cm={RECT_INPUT_ROW_SPACING_CM:.1f}",
    ]


def _rect_input_row_x_positions(table: TableState, row_size: int) -> tuple[float, ...]:
    if row_size == 1:
        return (250.0,)
    if row_size == 2:
        half_spacing = RECT_INPUT_TWO_COLUMN_SPACING_CM * 0.5
        return (250.0 - half_spacing, 250.0 + half_spacing)

    lateral_spacing = required_table_center_separation(
        table,
        0.0,
        table,
        0.0,
        (1.0, 0.0),
        gap=INPUT_TABLE_GAP_CM,
    )
    return tuple(250.0 + (index - 1) * lateral_spacing for index in range(row_size))


def _layout_rect_groupwork_templates(
    scene_state: SceneState,
    tables: list[TableState],
) -> tuple[list[TableTarget], list[str]]:
    """Arrange rect tables as compact, centered pair islands and singletons."""
    groups = [tables[index : index + 2] for index in range(0, len(tables), 2)]
    centers = _rect_groupwork_group_centers(len(tables))
    targets: list[TableTarget] = []
    assignment_notes: list[str] = []
    geometry_notes: list[str] = []
    rotation_deg = 0.0

    for group_index, (group, center) in enumerate(zip(groups, centers)):
        group_id = f"pair{group_index}"
        if len(group) == 2:
            separation = required_table_center_separation(
                group[0],
                rotation_deg,
                group[1],
                rotation_deg,
                (0.0, 1.0),
                gap=GROUPWORK_PAIR_SEAM_GAP_CM,
            )
            half_separation = separation * 0.5
            slots = ((center[0], center[1] - half_separation), (center[0], center[1] + half_separation))
            seat_directions = ((0.0, -1.0), (0.0, 1.0))
            geometry_notes.append(
                f"{group_id}|center={center[0]:.3f},{center[1]:.3f}|normal=0.000000,1.000000|gap_cm={separation:.3f}"
            )
        else:
            slots = (center,)
            seat_directions = ((0.0, -1.0),)

        for table, slot, seat_direction in zip(group, slots, seat_directions):
            targets.append(
                TableTarget(
                    table_id=table.table_id,
                    target_x=slot[0],
                    target_y=slot[1],
                    source_rot_deg=table.rot_deg,
                    target_rot_deg=rotation_deg,
                    facing_target_x=slot[0] + seat_direction[0] * 100.0,
                    facing_target_y=slot[1] + seat_direction[1] * 100.0,
                )
            )
            assignment_notes.append(f"{table.table_id}->{group_id}")

    return targets, [
        "rect_template=groupwork",
        f"groupwork_pair_count={len(groups)}",
        f"groupwork_assignments={', '.join(assignment_notes)}",
        f"groupwork_pair_geometry={'; '.join(geometry_notes)}",
        f"groupwork_pair_seam_gap_cm={GROUPWORK_PAIR_SEAM_GAP_CM:.1f}",
    ]


def _rect_groupwork_group_centers(table_count: int) -> tuple[tuple[float, float], ...]:
    """Return deliberate centered compositions for one to three islands."""
    by_count = {
        1: ((250.0, 250.0),),
        2: ((250.0, 250.0),),
        3: ((150.0, 250.0), (350.0, 250.0)),
        4: ((150.0, 250.0), (350.0, 250.0)),
        5: ((120.0, 160.0), (380.0, 160.0), (250.0, 360.0)),
        6: ((120.0, 180.0), (380.0, 180.0), (250.0, 350.0)),
    }
    return by_count[table_count]


def _layout_rect_discussion_templates(
    scene_state: SceneState,
    tables: list[TableState],
) -> tuple[list[TableTarget], list[str]]:
    """Arrange rect tables on a regular inward-facing polygon around the ROI center."""
    center = scene_state.roi.center
    if len(tables) == 1:
        table = tables[0]
        return [
            TableTarget(
                table_id=table.table_id,
                target_x=center[0],
                target_y=center[1],
                source_rot_deg=table.rot_deg,
                target_rot_deg=0.0,
            )
        ], ["rect_template=discussion", "rect_discussion_centered_singleton=true"]

    # Bind the regular ring in source angular order. This remains a
    # format-specific ID binding (not a slot-permutation optimization), while
    # avoiding avoidable crossing paths during strength blending.
    ordered_tables = _tables_in_source_angular_order(tables, center)
    start_angle = _source_angle_or_default(ordered_tables[0], center, len(tables))
    angles = tuple(start_angle + (2.0 * math.pi * index) / len(ordered_tables) for index in range(len(ordered_tables)))
    rotations = tuple(
        long_axis_rotation_from_facing_vector((-math.cos(angle), -math.sin(angle)), reference_rot_deg=0.0)
        for angle in angles
    )
    radius = _rect_discussion_radius(scene_state, ordered_tables, angles, rotations)

    targets = []
    for table, angle, rotation_deg in zip(ordered_tables, angles, rotations):
        x = center[0] + math.cos(angle) * radius
        y = center[1] + math.sin(angle) * radius
        targets.append(
            TableTarget(
                table_id=table.table_id,
                target_x=x,
                target_y=y,
                source_rot_deg=table.rot_deg,
                target_rot_deg=rotation_deg,
                facing_target_x=center[0],
                facing_target_y=center[1],
            )
        )

    return targets, [
        "rect_template=discussion",
        f"rect_discussion_center=({center[0]:.1f},{center[1]:.1f})",
        f"rect_discussion_radius_cm={radius:.3f}",
    ]


def _tables_in_source_angular_order(
    tables: list[TableState],
    center: tuple[float, float],
) -> list[TableState]:
    return sorted(
        tables,
        key=lambda table: (
            _source_angle_or_default(table, center, len(tables)),
            table.table_id,
        ),
    )


def _source_angle_or_default(
    table: TableState,
    center: tuple[float, float],
    table_count: int,
) -> float:
    dx = table.x - center[0]
    dy = table.y - center[1]
    if math.hypot(dx, dy) <= 1e-6:
        return -math.pi * 0.5 + math.pi / max(1, table_count)
    return math.atan2(dy, dx)


def _rect_discussion_radius(
    scene_state: SceneState,
    tables: list[TableState],
    angles: tuple[float, ...],
    rotations: tuple[float, ...],
) -> float:
    """Derive an ROI-safe ring radius from rect support and the common gap."""
    count = len(tables)
    radius = 0.0
    for index in range(count):
        next_index = (index + 1) % count
        point = (math.cos(angles[index]), math.sin(angles[index]))
        next_point = (math.cos(angles[next_index]), math.sin(angles[next_index]))
        separation_axis = _normalize_vector((next_point[0] - point[0], next_point[1] - point[1]))
        required = required_table_center_separation(
            tables[index],
            rotations[index],
            tables[next_index],
            rotations[next_index],
            separation_axis,
            gap=INPUT_TABLE_GAP_CM,
        )
        chord_factor = 2.0 * math.sin(math.pi / count)
        radius = max(radius, required / max(1e-6, chord_factor))

    radius += INPUT_TABLE_GAP_CM
    max_radius = math.inf
    for table, angle, rotation_deg in zip(tables, angles, rotations):
        x_min, y_min, x_max, y_max = table_allowed_center_bounds(
            table,
            rotation_deg,
            x_min=scene_state.roi.x_min,
            x_max=scene_state.roi.x_max,
            y_min=scene_state.roi.y_min,
            y_max=scene_state.roi.y_max,
        )
        direction = (math.cos(angle), math.sin(angle))
        for coordinate, center_value, lower, upper in (
            (direction[0], scene_state.roi.center[0], x_min, x_max),
            (direction[1], scene_state.roi.center[1], y_min, y_max),
        ):
            if coordinate > 1e-9:
                max_radius = min(max_radius, (upper - center_value) / coordinate)
            elif coordinate < -1e-9:
                max_radius = min(max_radius, (lower - center_value) / coordinate)

    if radius > max_radius:
        raise ValueError(
            f"rect discussion ring cannot fit {count} tables: required_radius={radius:.3f}, max_radius={max_radius:.3f}"
        )
    return radius


def _source_pose_targets(scene_state: SceneState) -> list[TableTarget]:
    return [
        TableTarget(
            table_id=table.table_id,
            target_x=table.x,
            target_y=table.y,
            source_rot_deg=table.rot_deg,
            target_rot_deg=table.rot_deg,
        )
        for table in scene_state.tables
    ]


def _targets_in_scene_order(scene_state: SceneState, targets: list[TableTarget]) -> list[TableTarget]:
    by_id = {target.table_id: target for target in targets}
    return [by_id[table.table_id] for table in scene_state.tables if table.table_id in by_id]


def _blend_targets_with_source(
    scene_state: SceneState,
    targets: list[TableTarget],
    strength: float,
) -> list[TableTarget]:
    source_by_id = {table.table_id: table for table in scene_state.tables}
    blended: list[TableTarget] = []
    for target in targets:
        source = source_by_id[target.table_id]
        x = _lerp(source.x, target.target_x, strength)
        y = _lerp(source.y, target.target_y, strength)
        rot = _normalize_angle_deg(
            source.rot_deg + _normalize_angle_deg(target.target_rot_deg - source.rot_deg) * strength
        )
        facing_x = target.facing_target_x
        facing_y = target.facing_target_y
        if facing_x is not None and facing_y is not None:
            facing_x += x - target.target_x
            facing_y += y - target.target_y
        blended.append(
            TableTarget(
                table_id=target.table_id,
                target_x=x,
                target_y=y,
                source_rot_deg=source.rot_deg,
                target_rot_deg=rot,
                facing_target_x=facing_x,
                facing_target_y=facing_y,
            )
        )
    return blended


def _evaluate_for_learning_format(
    scene_state: SceneState,
    targets: list[TableTarget],
    notes: list[str],
):
    depth_factor = 0.65 if scene_state.learning_format == "input" else 0.80 if scene_state.learning_format == "discussion" else 1.0
    return evaluate_hard_constraints(
        scene_state,
        targets,
        # Groupwork pairs intentionally use their own 4 cm seam.  Final
        # validity therefore means real-footprint non-intersection; the repair
        # still applies its existing 8 cm spacing to non-paired tables.
        overlap_gap=0.0,
        clearance_depth_factor=depth_factor,
        generation_notes=notes,
    )


def _apply_hard_constraint_repair(
    scene_state: SceneState,
    table_targets: list[TableTarget],
    generation_notes: list[str],
) -> tuple[list[TableTarget], list[str]]:
    if scene_state.learning_format == "input":
        clearance_depth_factor = 0.65
    elif scene_state.learning_format == "discussion":
        clearance_depth_factor = 0.80
    else:
        clearance_depth_factor = 1.0

    outcome = repair_layout_hard_constraints(
        scene_state,
        table_targets,
        max_iterations=80,
        overlap_gap=8.0,
        clearance_depth_factor=clearance_depth_factor,
        generation_notes=generation_notes,
    )

    return outcome.table_targets, [
        f"repair_applied={str(outcome.repair_applied).lower()}",
        f"repair_iterations={outcome.iterations}",
        (
            "repair_violations_before="
            f"o{outcome.before.overlap_violations}/"
            f"r{outcome.before.roi_violations}/"
            f"c{outcome.before.clearance_violations}"
        ),
        (
            "repair_violations_after="
            f"o{outcome.after.overlap_violations}/"
            f"r{outcome.after.roi_violations}/"
            f"c{outcome.after.clearance_violations}"
        ),
    ]


def _layout_input_adaptive(
    scene_state: SceneState,
    tables: list[TableState],
    target_structure: TargetStructure,
    transformation_strength: float = 0.5,
) -> tuple[list[TableTarget], list[str]]:
    if not tables:
        return [], ["input: no tables available"]

    roi = scene_state.roi
    roi_diag = max(1.0, math.hypot(roi.width, roi.height))
    front_direction, row_axis, axis_note = _resolve_input_front_axes(scene_state, tables, target_structure)
    common_rot_deg = long_axis_rotation_from_facing_vector(
        facing_vector=front_direction,
        reference_rot_deg=_mean_group_rot_deg(tables),
    )

    row_layout_candidates = _input_row_layout_candidates(len(tables))
    preferred_layout = list(target_structure.row_layout)
    if preferred_layout and sum(preferred_layout) == len(tables):
        if preferred_layout in row_layout_candidates:
            row_layout_candidates = [preferred_layout] + [layout for layout in row_layout_candidates if layout != preferred_layout]
        else:
            row_layout_candidates = [preferred_layout, *row_layout_candidates]

    best_plan: dict | None = None
    best_score = math.inf
    for row_layout in row_layout_candidates:
        row_centers = _resolve_input_row_centers(scene_state, tables, target_structure, row_layout, front_direction)
        plan = _build_input_row_plan(
            scene_state, tables, row_layout, row_centers, row_axis, common_rot_deg
        )
        plan_score = _score_input_row_plan(scene_state, tables, plan, row_layout, row_axis)
        if plan_score < best_score:
            best_score = plan_score
            best_plan = plan

    if best_plan is None:
        return [], ["input: failed to synthesize frontal row plan"]

    targets: list[TableTarget] = []
    assignment_notes: list[str] = []
    row_index_notes: list[str] = []

    for entry in best_plan["assignments"]:
        table = entry["table"]
        row_index = int(entry["row_index"])
        slot_center = entry["slot_center"]

        pull = _clamp(0.78 + (_distance((table.x, table.y), slot_center) / max(1.0, roi_diag)) * 0.30, 0.78, 0.94)
        blended = (
            _lerp(table.x, slot_center[0], pull),
            _lerp(table.y, slot_center[1], pull),
        )
        target_rot_deg = _blend_rotation_toward(
            target_rot_deg=common_rot_deg,
            source_rot_deg=table.rot_deg,
            preserve_ratio=0.10,
        )
        target_center = _clip_table_center_to_roi(blended, table, target_rot_deg, scene_state)

        geometry = resolve_table_state_geometry(table)
        seat_probe = table_support_distance(table, target_rot_deg, front_direction) + geometry.nominal_depth * 0.85
        seat_target = (
            target_center[0] + front_direction[0] * seat_probe,
            target_center[1] + front_direction[1] * seat_probe,
        )

        targets.append(
            TableTarget(
                table_id=table.table_id,
                target_x=target_center[0],
                target_y=target_center[1],
                source_rot_deg=table.rot_deg,
                target_rot_deg=target_rot_deg,
                facing_target_x=seat_target[0],
                facing_target_y=seat_target[1],
            )
        )
        assignment_notes.append(f"{table.table_id}->row{row_index}")
        row_index_notes.append(f"{table.table_id}:row_index={row_index}")

    row_layout = best_plan["row_layout"]
    row_centers = best_plan["row_centers"]
    notes = [
        "input: frontal row synthesis",
        f"input_front_direction=({front_direction[0]:.3f},{front_direction[1]:.3f})",
        f"input_row_layout={row_layout}",
        f"input_row_centers={'; '.join(f'row{idx}=({center[0]:.1f},{center[1]:.1f})' for idx, center in enumerate(row_centers))}",
        axis_note,
        f"input_row_assignments={', '.join(sorted(assignment_notes))}",
        f"input_row_index={'; '.join(sorted(row_index_notes))}",
    ]
    return targets, notes


def _resolve_input_front_axes(
    scene_state: SceneState,
    tables: list[TableState],
    target_structure: TargetStructure,
) -> tuple[tuple[float, float], tuple[float, float], str]:
    if target_structure.front_direction is not None:
        front_direction = _normalize_vector((target_structure.front_direction.x, target_structure.front_direction.y))
    elif target_structure.focus_direction is not None:
        front_direction = _normalize_vector((target_structure.focus_direction.x, target_structure.focus_direction.y))
    else:
        front_direction = (0.0, -1.0)

    if abs(front_direction[0]) <= 1e-6 and abs(front_direction[1]) <= 1e-6:
        front_direction = (0.0, -1.0)

    row_axis = _perpendicular(front_direction)
    row_axis, axis_note = _regularize_input_axis_from_source(row_axis, tables)
    front_direction = _normalize_vector(_perpendicular(row_axis))
    if front_direction[1] > 0.0:
        front_direction = (-front_direction[0], -front_direction[1])

    return front_direction, _normalize_vector(row_axis), axis_note


def _input_row_layout_candidates(table_count: int) -> list[list[int]]:
    if table_count <= 0:
        return [[1]]
    if table_count == 1:
        return [[1]]
    if table_count == 2:
        return [[2]]
    if table_count == 3:
        return [[3], [2, 1]]
    if table_count == 4:
        return [[2, 2]]
    if table_count == 5:
        return [[2, 3], [2, 2, 1]]
    if table_count == 6:
        return [[2, 2, 2], [3, 3]]

    twos = [2 for _ in range(table_count // 2)]
    if table_count % 2:
        twos.append(1)
    return [twos]


def _resolve_input_row_centers(
    scene_state: SceneState,
    tables: list[TableState],
    target_structure: TargetStructure,
    row_layout: list[int],
    front_direction: tuple[float, float],
) -> list[tuple[float, float]]:
    row_count = len(row_layout)
    roi = scene_state.roi

    if target_structure.row_centers and len(target_structure.row_centers) == row_count:
        roi_min = max(1.0, min(roi.width, roi.height))
        margin = max(roi_min * 0.10, _input_row_spacing(scene_state, tables) * 0.60)
        return [
            _clip_point(
                (row_center.x, row_center.y),
                x_min=roi.x_min + margin,
                x_max=roi.x_max - margin,
                y_min=roi.y_min + margin,
                y_max=roi.y_max - margin,
            )
            for row_center in target_structure.row_centers
        ]

    centroid = compute_table_centroid(tables)
    base_center = (centroid.x, centroid.y)
    back_axis = (-front_direction[0], -front_direction[1])
    row_spacing = _input_row_spacing(scene_state, tables)
    roi_min = max(1.0, min(roi.width, roi.height))
    margin = max(roi_min * 0.10, row_spacing * 0.60)

    centers: list[tuple[float, float]] = []
    for row_idx in range(row_count):
        depth_offset = (row_idx - (row_count - 1) * 0.5) * row_spacing
        raw = (
            base_center[0] + back_axis[0] * depth_offset,
            base_center[1] + back_axis[1] * depth_offset,
        )
        centers.append(
            _clip_point(
                raw,
                x_min=roi.x_min + margin,
                x_max=roi.x_max - margin,
                y_min=roi.y_min + margin,
                y_max=roi.y_max - margin,
            )
        )

    return centers


def _build_input_row_plan(
    scene_state: SceneState,
    tables: list[TableState],
    row_layout: list[int],
    row_centers: list[tuple[float, float]],
    row_axis: tuple[float, float],
    target_rot_deg: float,
) -> dict:
    back_axis = (-_perpendicular(row_axis)[0], -_perpendicular(row_axis)[1])

    sorted_by_depth = sorted(tables, key=lambda table: _dot((table.x, table.y), back_axis))

    assignments: list[dict] = []
    start = 0
    for row_idx, row_size in enumerate(row_layout):
        row_tables = sorted_by_depth[start : start + row_size]
        start += row_size
        if not row_tables:
            continue

        row_tables_sorted = sorted(row_tables, key=lambda table: _dot((table.x, table.y), row_axis))
        row_center = row_centers[min(row_idx, len(row_centers) - 1)]
        lateral_positions = [0.0]
        for previous, current in zip(row_tables_sorted, row_tables_sorted[1:]):
            lateral_positions.append(
                lateral_positions[-1]
                + required_table_center_separation(
                    previous,
                    target_rot_deg,
                    current,
                    target_rot_deg,
                    row_axis,
                    gap=INPUT_TABLE_GAP_CM,
                )
            )
        lateral_center = (lateral_positions[0] + lateral_positions[-1]) * 0.5
        slots = [
            (
                row_center[0] + row_axis[0] * (lateral - lateral_center),
                row_center[1] + row_axis[1] * (lateral - lateral_center),
            )
            for lateral in lateral_positions
        ]

        for slot_idx, (table, slot_center) in enumerate(zip(row_tables_sorted, slots)):
            assignments.append(
                {
                    "table": table,
                    "row_index": row_idx,
                    "slot_index": slot_idx,
                    "slot_center": slot_center,
                }
            )

    return {
        "row_layout": list(row_layout),
        "row_centers": list(row_centers),
        "assignments": assignments,
    }


def _score_input_row_plan(
    scene_state: SceneState,
    tables: list[TableState],
    plan: dict,
    row_layout: list[int],
    row_axis: tuple[float, float],
) -> float:
    if not plan["assignments"]:
        return math.inf

    roi_diag = max(1.0, math.hypot(scene_state.roi.width, scene_state.roi.height))
    movement_cost = mean(
        _distance((entry["table"].x, entry["table"].y), entry["slot_center"])
        for entry in plan["assignments"]
    )

    source_axis, source_anisotropy = _dominant_axis_and_anisotropy(tables)
    source_diag = _axis_diagonal_strength(source_axis) * source_anisotropy
    target_diag = _axis_diagonal_strength(row_axis)
    diag_excess = max(0.0, target_diag - source_diag - 0.10)
    movement_pressure = _clamp(movement_cost / (roi_diag * 0.24), 0.0, 1.0)
    diagonal_penalty = diag_excess * (0.35 + 0.65 * movement_pressure)

    singleton_penalty = 0.18 * sum(1 for size in row_layout if size == 1)
    triple_penalty = 0.05 * sum(1 for size in row_layout if size == 3)
    row_count_penalty = 0.05 * max(0, len(row_layout) - 2)

    row_centers = plan["row_centers"]
    back_axis = (-_perpendicular(row_axis)[0], -_perpendicular(row_axis)[1])
    row_depths = sorted(_dot(center, back_axis) for center in row_centers)
    min_row_sep = min(
        (abs(row_depths[idx + 1] - row_depths[idx]) for idx in range(len(row_depths) - 1)),
        default=math.inf,
    )
    required_sep = _input_row_spacing(scene_state, tables) * 0.95
    if math.isinf(min_row_sep):
        separation_penalty = 0.0
    else:
        separation_penalty = _clamp((required_sep - min_row_sep) / max(1.0, required_sep), 0.0, 1.0) * 0.26

    return (
        (movement_cost / (roi_diag * 0.42))
        + diagonal_penalty
        + singleton_penalty
        + triple_penalty
        + row_count_penalty
        + separation_penalty
    )


def _input_row_spacing(scene_state: SceneState, tables: list[TableState]) -> float:
    if not tables:
        return max(60.0, scene_state.roi.height * 0.16)

    geometries = [resolve_table_state_geometry(table) for table in tables]
    median_height = median(max(1.0, geometry.nominal_depth) for geometry in geometries)
    median_width = median(max(1.0, geometry.nominal_width) for geometry in geometries)
    roi_min = max(1.0, min(scene_state.roi.width, scene_state.roi.height))
    return max(median_height * 1.35, median_width * 0.95, roi_min * 0.16)


def _input_col_spacing(scene_state: SceneState, tables: list[TableState]) -> float:
    if not tables:
        return max(70.0, scene_state.roi.width * 0.18)

    median_width = median(max(1.0, resolve_table_state_geometry(table).nominal_width) for table in tables)
    roi_min = max(1.0, min(scene_state.roi.width, scene_state.roi.height))
    return max(median_width * 0.90, roi_min * 0.11)


def _blend_rotation_toward(target_rot_deg: float, source_rot_deg: float, preserve_ratio: float) -> float:
    delta = _normalize_angle_deg(source_rot_deg - target_rot_deg)
    return _normalize_angle_deg(target_rot_deg + delta * preserve_ratio)


def _layout_groupwork_adaptive(
    scene_state: SceneState,
    tables: list[TableState],
    target_structure: TargetStructure,
    transformation_strength: float = 0.5,
) -> tuple[list[TableTarget], list[str]]:
    if not tables:
        return [], ["groupwork: no tables available"]

    zones = target_structure.cluster_zones or []
    roi = scene_state.roi
    roi_diag = max(1.0, math.hypot(roi.width, roi.height))

    pairs = pair_tables_for_groupwork(tables)
    if not pairs:
        return [], ["groupwork: no pair islands could be formed"]

    pair_zone_map = _assign_pairs_to_cluster_zones(pairs, zones) if zones else {idx: idx for idx in range(len(pairs))}

    median_height = median(
        max(1.0, resolve_table_state_geometry(table).nominal_depth) for table in tables
    )

    island_specs: list[dict] = []
    initial_centers: list[tuple[float, float]] = []
    island_radii: list[float] = []
    island_anchors: list[tuple[float, float]] = []

    for pair_idx, pair in enumerate(pairs):
        pair_centroid = compute_table_centroid(pair)
        zone_idx = pair_zone_map.get(pair_idx, pair_idx)
        zone_center = (
            (zones[zone_idx].center.x, zones[zone_idx].center.y)
            if zones and 0 <= zone_idx < len(zones)
            else (pair_centroid.x, pair_centroid.y)
        )

        pair_quality = _groupwork_pair_cohesion(pair)
        zone_distance = _distance((pair_centroid.x, pair_centroid.y), zone_center)
        center_pull = _adaptive_pull(zone_distance, roi_diag, min_pull=0.22, max_pull=0.62)
        center_pull *= (1.0 - (pair_quality * 0.45))
        initial_center = (
            _lerp(pair_centroid.x, zone_center[0], center_pull),
            _lerp(pair_centroid.y, zone_center[1], center_pull),
        )

        if len(pair) == 2:
            source_link_axis = _unit_vector_between(pair[0], pair[1], fallback=(1.0, 0.0))
            source_pair_rot = _mean_group_rot_deg(pair)
            source_long_axis = _long_axis_vector_from_rot(source_pair_rot)
            structural_long_axis = _perpendicular(source_link_axis)
            if _dot(structural_long_axis, source_long_axis) < 0.0:
                structural_long_axis = (-structural_long_axis[0], -structural_long_axis[1])

            source_blend = _clamp(0.50 + pair_quality * 0.38, 0.35, 0.90)
            long_axis = _normalize_vector(
                (
                    _lerp(structural_long_axis[0], source_long_axis[0], source_blend),
                    _lerp(structural_long_axis[1], source_long_axis[1], source_blend),
                )
            )
            short_axis = _perpendicular(long_axis)
            if _dot((pair[1].x - pair[0].x, pair[1].y - pair[0].y), short_axis) < 0.0:
                short_axis = (-short_axis[0], -short_axis[1])

            pair_rot_deg = _rotation_from_long_axis(long_axis, reference_rot_deg=source_pair_rot)
            desired_sep = required_table_center_separation(
                pair[0],
                pair_rot_deg,
                pair[1],
                pair_rot_deg,
                short_axis,
                gap=GROUPWORK_PAIR_SEAM_GAP_CM,
            )
        else:
            desired_sep = 0.0
            pair_rot_deg = pair[0].rot_deg
            long_axis = _long_axis_vector_from_rot(pair_rot_deg)
            short_axis = _perpendicular(long_axis)

        island_specs.append(
            {
                "pair_idx": pair_idx,
                "tables": pair,
                "zone_idx": zone_idx,
                "zone_center": zone_center,
                "pair_quality": pair_quality,
                "desired_sep": desired_sep,
                "long_axis": long_axis,
                "short_axis": short_axis,
                "pair_rot_deg": pair_rot_deg,
            }
        )
        initial_centers.append(initial_center)
        island_anchors.append(zone_center)
        island_radii.append(
            _estimate_groupwork_island_radius(pair, desired_sep, short_axis, pair_rot_deg)
        )

    distributed_centers = _spread_groupwork_island_centers(
        scene_state=scene_state,
        centers=initial_centers,
        radii=island_radii,
        anchors=island_anchors,
        spacing=max(18.0, median_height * 0.30),
    )

    targets: list[TableTarget] = []
    assignment_notes: list[str] = []
    pair_members_notes: list[str] = []
    pair_center_notes: list[str] = []
    pair_rotation_notes: list[str] = []
    pair_geometry_notes: list[str] = []
    table_role_notes: list[str] = []

    for spec, island_center in zip(island_specs, distributed_centers):
        pair_idx = int(spec["pair_idx"])
        pair = list(spec["tables"])
        pair_normal = _normalize_vector(spec["short_axis"])
        pair_rot_deg = float(spec["pair_rot_deg"])
        desired_sep = float(spec["desired_sep"])

        pair_label = f"pair{pair_idx}"
        pair_members_notes.append(f"{pair_label}:{'+'.join(sorted(table.table_id for table in pair))}")
        pair_center_notes.append(f"{pair_label}=({island_center[0]:.1f},{island_center[1]:.1f})")
        pair_rotation_notes.append(f"{pair_label}:{pair_rot_deg:.1f}")
        if len(pair) == 2:
            pair_geometry_notes.append(
                f"{pair_label}|center={island_center[0]:.3f},{island_center[1]:.3f}|"
                f"normal={pair_normal[0]:.6f},{pair_normal[1]:.6f}|gap_cm={desired_sep:.3f}"
            )

        if len(pair) == 2:
            pair_centroid = compute_table_centroid(pair)
            ordered_pair = sort_tables_along_axis(pair, pair_normal, origin=(pair_centroid.x, pair_centroid.y))
            half_sep = desired_sep * 0.5
            ideal_positions = [
                (island_center[0] - pair_normal[0] * half_sep, island_center[1] - pair_normal[1] * half_sep),
                (island_center[0] + pair_normal[0] * half_sep, island_center[1] + pair_normal[1] * half_sep),
            ]
            seat_signs = [-1.0, 1.0]

            for table, ideal, seat_sign in zip(ordered_pair, ideal_positions, seat_signs):
                target_center = _clip_table_center_to_roi(ideal, table, pair_rot_deg, scene_state)
                seat_direction = (pair_normal[0] * seat_sign, pair_normal[1] * seat_sign)
                geometry = resolve_table_state_geometry(table)
                seat_probe = (
                    table_support_distance(table, pair_rot_deg, seat_direction)
                    + geometry.nominal_depth * 0.85
                )
                seat_target = (
                    target_center[0] + seat_direction[0] * seat_probe,
                    target_center[1] + seat_direction[1] * seat_probe,
                )
                seat_side = _long_side_label_from_direction(pair_rot_deg, seat_direction)
                pair_contact_side = _long_side_label_from_direction(pair_rot_deg, (-seat_direction[0], -seat_direction[1]))

                targets.append(
                    TableTarget(
                        table_id=table.table_id,
                        target_x=target_center[0],
                        target_y=target_center[1],
                        source_rot_deg=table.rot_deg,
                        target_rot_deg=pair_rot_deg,
                        facing_target_x=seat_target[0],
                        facing_target_y=seat_target[1],
                    )
                )
                assignment_notes.append(f"{table.table_id}->{pair_label}")
                table_role_notes.append(
                    f"{table.table_id}:{pair_label}:seat_side={seat_side}:pair_contact_side={pair_contact_side}:pair_id={pair_label}"
                )
        else:
            table = pair[0]
            blended = _blend_position_preserving_motion(
                current=(table.x, table.y),
                ideal=island_center,
                roi_diag=roi_diag,
                min_pull=0.40,
                max_pull=0.72,
            )
            target_rot_deg = _target_rot_deg_from_facing_target(
                table=table,
                table_center=blended,
                facing_target=island_center,
            )
            target_center = _clip_table_center_to_roi(blended, table, target_rot_deg, scene_state)
            target_rot_deg = _target_rot_deg_from_facing_target(
                table=table,
                table_center=target_center,
                facing_target=island_center,
            )
            target_center = _clip_table_center_to_roi(target_center, table, target_rot_deg, scene_state)
            targets.append(
                TableTarget(
                    table_id=table.table_id,
                    target_x=target_center[0],
                    target_y=target_center[1],
                    source_rot_deg=table.rot_deg,
                    target_rot_deg=target_rot_deg,
                    facing_target_x=island_center[0],
                    facing_target_y=island_center[1],
                )
            )
            assignment_notes.append(f"{table.table_id}->{pair_label}")
            table_role_notes.append(
                f"{table.table_id}:{pair_label}:seat_side=from_facing:pair_contact_side=none:pair_id={pair_label}"
            )

    notes = [
        "groupwork: pair-first compact island synthesis",
        f"groupwork_pair_count={len(pairs)} zones={len(zones)}",
        f"groupwork_pairs={'; '.join(pair_members_notes)}",
        f"groupwork_island_centers={'; '.join(pair_center_notes)}",
        f"groupwork_pair_seam_gap_cm={GROUPWORK_PAIR_SEAM_GAP_CM:.1f}",
        f"groupwork_pair_geometry={'; '.join(pair_geometry_notes)}",
        f"groupwork_pair_rotations={'; '.join(pair_rotation_notes)}",
        f"groupwork_table_roles={'; '.join(sorted(table_role_notes))}",
        f"groupwork_assignments={', '.join(sorted(assignment_notes))}",
    ]
    return targets, notes


def _layout_discussion_adaptive(
    scene_state: SceneState,
    tables: list[TableState],
    target_structure: TargetStructure,
    transformation_strength: float = 0.5,
) -> tuple[list[TableTarget], list[str]]:
    if not tables:
        return [], ["discussion: no tables available"]

    roi = scene_state.roi
    roi_diag = max(1.0, math.hypot(roi.width, roi.height))
    roi_min = max(1.0, min(roi.width, roi.height))

    center = target_structure.shared_field_center or compute_table_centroid(tables)
    center_tuple = _clip_point(
        (center.x, center.y),
        x_min=roi.x_min + roi_min * 0.08,
        x_max=roi.x_max - roi_min * 0.08,
        y_min=roi.y_min + roi_min * 0.08,
        y_max=roi.y_max - roi_min * 0.08,
    )

    # Keep the existing angular ordering, but lightly regularize for readability.
    polar_entries: list[tuple[TableState, float, float]] = []
    for idx, table in enumerate(tables):
        dx = table.x - center_tuple[0]
        dy = table.y - center_tuple[1]
        radius = math.hypot(dx, dy)
        if radius <= 1e-6:
            angle = (2.0 * math.pi * idx) / len(tables)
            radius = roi_min * 0.18
        else:
            angle = math.atan2(dy, dx)
        polar_entries.append((table, angle, radius))

    polar_entries.sort(key=lambda item: item[1])
    base_radius = median(entry[2] for entry in polar_entries)
    typical_diagonal = median(
        resolve_table_state_geometry(table).characteristic_diagonal for table in tables
    )
    min_radius = max(roi_min * 0.14, typical_diagonal * 0.55)
    max_radius = roi_min * 0.42
    start_angle = polar_entries[0][1]

    targets: list[TableTarget] = []
    for idx, (table, current_angle, current_radius) in enumerate(polar_entries):
        regular_angle = start_angle + (2.0 * math.pi * idx) / len(polar_entries)
        blended_angle = _blend_angle(current_angle, regular_angle, blend=0.35)
        target_radius = _clamp(_lerp(current_radius, base_radius, 0.45), min_radius, max_radius)

        ideal = (
            center_tuple[0] + math.cos(blended_angle) * target_radius,
            center_tuple[1] + math.sin(blended_angle) * target_radius,
        )
        blended = _blend_position_preserving_motion(
            current=(table.x, table.y),
            ideal=ideal,
            roi_diag=roi_diag,
            min_pull=0.40,
            max_pull=0.78,
        )
        target_rot_deg = _target_rot_deg_from_facing_target(
            table=table,
            table_center=blended,
            facing_target=center_tuple,
        )
        target_center = _clip_table_center_to_roi(blended, table, target_rot_deg, scene_state)
        target_rot_deg = _target_rot_deg_from_facing_target(
            table=table,
            table_center=target_center,
            facing_target=center_tuple,
        )
        target_center = _clip_table_center_to_roi(target_center, table, target_rot_deg, scene_state)

        targets.append(
            TableTarget(
                table_id=table.table_id,
                target_x=target_center[0],
                target_y=target_center[1],
                source_rot_deg=table.rot_deg,
                target_rot_deg=target_rot_deg,
                facing_target_x=center_tuple[0],
                facing_target_y=center_tuple[1],
            )
        )

    notes = [
        "discussion: adaptive field-like ring with continuous angles",
        f"discussion_center=({center_tuple[0]:.1f},{center_tuple[1]:.1f}) base_radius={base_radius:.1f}",
    ]
    return targets, notes


def _input_focus_line_or_fallback(
    scene_state: SceneState,
    target_structure: TargetStructure,
) -> tuple[tuple[float, float], tuple[float, float], tuple[float, float]]:
    roi = scene_state.roi
    if target_structure.focus_line_start and target_structure.focus_line_end:
        start = (target_structure.focus_line_start.x, target_structure.focus_line_start.y)
        end = (target_structure.focus_line_end.x, target_structure.focus_line_end.y)
        center = ((start[0] + end[0]) * 0.5, (start[1] + end[1]) * 0.5)
        return start, end, center

    # Backward-compatible fallback if older structures are present.
    center = target_structure.focus_point or Point2D(x=roi.center[0], y=roi.y_min + roi.height * 0.20)
    start = (center.x - roi.width * 0.25, center.y)
    end = (center.x + roi.width * 0.25, center.y)
    return start, end, (center.x, center.y)


def _regularize_input_axis_from_source(
    suggested_axis: tuple[float, float],
    tables: list[TableState],
) -> tuple[tuple[float, float], str]:
    """Avoid unnecessarily diagonal input fronts unless source geometry supports it."""
    if len(tables) < 3:
        return suggested_axis, "input_axis_regularization=kept_small_set"

    source_axis, source_anisotropy = _dominant_axis_and_anisotropy(tables)
    source_diag = _axis_diagonal_strength(source_axis)
    suggested_diag = _axis_diagonal_strength(suggested_axis)

    diagonal_is_plausible = source_diag > 0.55 and source_anisotropy > 0.42
    if diagonal_is_plausible or suggested_diag < 0.18:
        return suggested_axis, "input_axis_regularization=kept"

    horizontal = (1.0, 0.0)
    vertical = (0.0, 1.0)
    horizontal_score = abs(_dot(suggested_axis, horizontal))
    vertical_score = abs(_dot(suggested_axis, vertical))
    snapped = horizontal if horizontal_score >= vertical_score else vertical
    if _dot(suggested_axis, snapped) < 0.0:
        snapped = (-snapped[0], -snapped[1])

    blended = _normalize_vector(
        (
            _lerp(suggested_axis[0], snapped[0], 0.72),
            _lerp(suggested_axis[1], snapped[1], 0.72),
        )
    )
    return blended, "input_axis_regularization=soft_snap"


def _rebuild_focus_line_with_direction(
    center: tuple[float, float],
    direction: tuple[float, float],
    half_length: float,
    scene_state: SceneState,
) -> tuple[tuple[float, float], tuple[float, float]]:
    roi = scene_state.roi
    roi_margin = max(8.0, min(roi.width, roi.height) * 0.08)
    start = _clip_point(
        (center[0] - direction[0] * half_length, center[1] - direction[1] * half_length),
        x_min=roi.x_min + roi_margin,
        x_max=roi.x_max - roi_margin,
        y_min=roi.y_min + roi_margin,
        y_max=roi.y_max - roi_margin,
    )
    end = _clip_point(
        (center[0] + direction[0] * half_length, center[1] + direction[1] * half_length),
        x_min=roi.x_min + roi_margin,
        x_max=roi.x_max - roi_margin,
        y_min=roi.y_min + roi_margin,
        y_max=roi.y_max - roi_margin,
    )
    return start, end


def compute_table_centroid(tables: list[TableState]) -> Point2D:
    return Point2D(
        x=mean(table.x for table in tables),
        y=mean(table.y for table in tables),
    )


def sort_tables_along_axis(
    tables: list[TableState],
    axis: tuple[float, float],
    origin: tuple[float, float],
) -> list[TableState]:
    """Sort tables by projection along axis for stable geometric ordering."""
    return sorted(
        tables,
        key=lambda table: _dot((table.x - origin[0], table.y - origin[1]), axis),
    )


def pair_tables_by_proximity(tables: list[TableState]) -> list[list[TableState]]:
    """Greedy nearest-neighbor pairing with optional single-table remainder."""
    remaining = list(tables)
    pairs: list[list[TableState]] = []

    while len(remaining) >= 2:
        best_i = 0
        best_j = 1
        best_dist = math.inf
        for i in range(len(remaining)):
            for j in range(i + 1, len(remaining)):
                dist = _distance((remaining[i].x, remaining[i].y), (remaining[j].x, remaining[j].y))
                if dist < best_dist:
                    best_dist = dist
                    best_i = i
                    best_j = j

        second = remaining.pop(best_j)
        first = remaining.pop(best_i)
        pairs.append([first, second])

    if remaining:
        pairs.append([remaining[0]])

    return pairs


def assign_tables_to_cluster_zones(
    tables: list[TableState],
    zones: list,
) -> dict[str, int]:
    """Assign each table to the nearest cluster zone index."""
    assignments: dict[str, int] = {}
    if not zones:
        return assignments

    for table in tables:
        zone_idx = min(
            range(len(zones)),
            key=lambda idx: _distance((table.x, table.y), (zones[idx].center.x, zones[idx].center.y)),
        )
        assignments[table.table_id] = zone_idx

    return assignments


def compute_target_long_axis_from_facing_vector(
    table: TableState,
    facing_vector: tuple[float, float],
) -> float:
    """Derive long-axis rotation from desired facing direction."""
    return long_axis_rotation_from_facing_vector(
        facing_vector=facing_vector,
        reference_rot_deg=table.rot_deg,
    )


def _target_rot_deg_from_facing_target(
    table: TableState,
    table_center: tuple[float, float],
    facing_target: tuple[float, float],
) -> float:
    facing_vector = _unit_vector_toward(table_center, facing_target)
    return compute_target_long_axis_from_facing_vector(table, facing_vector)


def _project_point_to_line_segment(
    point: tuple[float, float],
    line_start: tuple[float, float],
    line_end: tuple[float, float],
) -> tuple[float, float]:
    """Project a point onto the line segment used as a shared focus edge."""
    line_vec = (line_end[0] - line_start[0], line_end[1] - line_start[1])
    line_len_sq = max(1e-9, line_vec[0] * line_vec[0] + line_vec[1] * line_vec[1])
    rel = (point[0] - line_start[0], point[1] - line_start[1])
    t = _clamp(_dot(rel, line_vec) / line_len_sq, 0.0, 1.0)
    return (
        line_start[0] + line_vec[0] * t,
        line_start[1] + line_vec[1] * t,
    )


def _assign_pairs_to_cluster_zones(pairs: list[list[TableState]], zones: list) -> dict[int, int]:
    """Greedy pair-to-zone assignment that prefers unique zones if available."""
    available = set(range(len(zones)))
    mapping: dict[int, int] = {}

    for pair_idx, pair in enumerate(pairs):
        pair_center = compute_table_centroid(pair)
        ranked = sorted(
            range(len(zones)),
            key=lambda zone_idx: _distance(
                (pair_center.x, pair_center.y),
                (zones[zone_idx].center.x, zones[zone_idx].center.y),
            ),
        )

        chosen = None
        for zone_idx in ranked:
            if zone_idx in available:
                chosen = zone_idx
                break
        if chosen is None:
            chosen = ranked[0]
        else:
            available.discard(chosen)

        mapping[pair_idx] = chosen

    return mapping


def _groupwork_pair_cohesion(pair: list[TableState]) -> float:
    if len(pair) < 2:
        return 0.0

    separation = _distance((pair[0].x, pair[0].y), (pair[1].x, pair[1].y))
    pair_axis = _unit_vector_between(pair[0], pair[1], fallback=(1.0, 0.0))
    preferred = required_table_center_separation(
        pair[0], pair[0].rot_deg, pair[1], pair[1].rot_deg, pair_axis, gap=GROUPWORK_PAIR_SEAM_GAP_CM
    )

    separation_quality = max(0.0, 1.0 - (abs(separation - preferred) / max(1.0, preferred * 0.90)))
    orientation_delta = _angle_delta_mod180(pair[0].rot_deg, pair[1].rot_deg)
    orientation_quality = max(0.0, 1.0 - (orientation_delta / 52.0))

    return _clamp((separation_quality * 0.65) + (orientation_quality * 0.35), 0.0, 1.0)


def _mean_group_rot_deg(group: list[TableState]) -> float:
    if not group:
        return 0.0

    sum_x = 0.0
    sum_y = 0.0
    for table in group:
        theta = math.radians(table.rot_deg * 2.0)
        sum_x += math.cos(theta)
        sum_y += math.sin(theta)

    if abs(sum_x) <= 1e-9 and abs(sum_y) <= 1e-9:
        return group[0].rot_deg

    mean_theta = 0.5 * math.atan2(sum_y, sum_x)
    return _normalize_angle_deg(math.degrees(mean_theta))


def _long_axis_vector_from_rot(rot_deg: float) -> tuple[float, float]:
    theta = math.radians(rot_deg)
    return (math.cos(theta), math.sin(theta))


def _rotation_from_long_axis(axis: tuple[float, float], reference_rot_deg: float) -> float:
    base = _normalize_angle_deg(math.degrees(math.atan2(axis[1], axis[0])))
    candidate_a = base
    candidate_b = _normalize_angle_deg(base + 180.0)
    ref = _normalize_angle_deg(reference_rot_deg)
    delta_a = abs(_normalize_angle_deg(candidate_a - ref))
    delta_b = abs(_normalize_angle_deg(candidate_b - ref))
    return candidate_a if delta_a <= delta_b else candidate_b


def _long_side_label_from_direction(rot_deg: float, direction: tuple[float, float]) -> str:
    long_axis = _long_axis_vector_from_rot(rot_deg)
    short_axis = _perpendicular(long_axis)
    side_sign = 1.0 if _dot(direction, short_axis) >= 0.0 else -1.0
    return "long_side_pos_normal" if side_sign >= 0.0 else "long_side_neg_normal"


def _estimate_groupwork_island_radius(
    pair: list[TableState],
    separation: float,
    separation_normal: tuple[float, float],
    target_rot_deg: float,
) -> float:
    if not pair:
        return 0.0
    if len(pair) == 1:
        polygons = [table_world_footprint(pair[0], (0.0, 0.0), target_rot_deg)]
    else:
        normal = _normalize_vector(separation_normal)
        half = separation * 0.5
        centers = [(-normal[0] * half, -normal[1] * half), (normal[0] * half, normal[1] * half)]
        polygons = [
            table_world_footprint(table, center, target_rot_deg)
            for table, center in zip(pair, centers)
        ]
    radius = max(math.hypot(x, y) for polygon in polygons for x, y in polygon)
    padding = mean(resolve_table_state_geometry(table).nominal_depth for table in pair) * 0.20
    return radius + padding


def _spread_groupwork_island_centers(
    scene_state: SceneState,
    centers: list[tuple[float, float]],
    radii: list[float],
    anchors: list[tuple[float, float]],
    spacing: float,
) -> list[tuple[float, float]]:
    if not centers:
        return []

    adjusted = list(centers)
    roi = scene_state.roi

    for _ in range(18):
        changed = False

        for i in range(len(adjusted)):
            for j in range(i + 1, len(adjusted)):
                delta = (
                    adjusted[j][0] - adjusted[i][0],
                    adjusted[j][1] - adjusted[i][1],
                )
                distance = math.hypot(delta[0], delta[1])
                minimum = radii[i] + radii[j] + spacing
                if distance >= minimum:
                    continue

                axis = _normalize_vector(delta) if distance > 1e-6 else _deterministic_axis(i, j)
                push = (minimum - distance) * 0.52 + 0.5

                adjusted[i] = (
                    adjusted[i][0] - axis[0] * push,
                    adjusted[i][1] - axis[1] * push,
                )
                adjusted[j] = (
                    adjusted[j][0] + axis[0] * push,
                    adjusted[j][1] + axis[1] * push,
                )
                changed = True

        for idx in range(len(adjusted)):
            adjusted[idx] = (
                _lerp(adjusted[idx][0], anchors[idx][0], 0.10),
                _lerp(adjusted[idx][1], anchors[idx][1], 0.10),
            )

            radius_margin = max(8.0, radii[idx] * 0.62)
            adjusted[idx] = _clip_point(
                adjusted[idx],
                x_min=roi.x_min + radius_margin,
                x_max=roi.x_max - radius_margin,
                y_min=roi.y_min + radius_margin,
                y_max=roi.y_max - radius_margin,
            )

        if not changed:
            break

    return adjusted


def _blend_position_preserving_motion(
    current: tuple[float, float],
    ideal: tuple[float, float],
    roi_diag: float,
    min_pull: float,
    max_pull: float,
) -> tuple[float, float]:
    """Keep minimal movement secondary while preserving structural readability.

    Close tables move less, far-off tables move more.
    """
    delta = _distance(current, ideal)
    pull = _adaptive_pull(delta, roi_diag, min_pull=min_pull, max_pull=max_pull)
    return (
        _lerp(current[0], ideal[0], pull),
        _lerp(current[1], ideal[1], pull),
    )


def _adaptive_pull(delta: float, roi_diag: float, min_pull: float, max_pull: float) -> float:
    normalized = _clamp(delta / max(1.0, roi_diag * 0.22), 0.0, 1.0)
    return _lerp(min_pull, max_pull, normalized)


def _clip_table_center_to_roi(
    center: tuple[float, float],
    table: TableState,
    rotation_deg: float,
    scene_state: SceneState,
) -> tuple[float, float]:
    """Clamp a rotated real footprint into the ROI."""
    roi = scene_state.roi
    x_min, x_max, y_min, y_max = table_allowed_center_bounds(
        table,
        rotation_deg,
        x_min=roi.x_min,
        x_max=roi.x_max,
        y_min=roi.y_min,
        y_max=roi.y_max,
    )
    return _clip_point(
        center,
        x_min=x_min,
        x_max=x_max,
        y_min=y_min,
        y_max=y_max,
    )


def _unit_vector_between(
    table_a: TableState,
    table_b: TableState,
    fallback: tuple[float, float],
) -> tuple[float, float]:
    return _unit_vector_toward((table_a.x, table_a.y), (table_b.x, table_b.y), fallback=fallback)


def _unit_vector_toward(
    origin: tuple[float, float],
    target: tuple[float, float],
    fallback: tuple[float, float] = (0.0, -1.0),
) -> tuple[float, float]:
    dx = target[0] - origin[0]
    dy = target[1] - origin[1]
    length = math.hypot(dx, dy)
    if length <= 1e-9:
        return fallback

    return (dx / length, dy / length)


def _normalize_vector(vector: tuple[float, float]) -> tuple[float, float]:
    length = math.hypot(vector[0], vector[1])
    if length <= 1e-9:
        return (1.0, 0.0)
    return (vector[0] / length, vector[1] / length)


def _dominant_axis_and_anisotropy(tables: list[TableState]) -> tuple[tuple[float, float], float]:
    if len(tables) < 2:
        return (1.0, 0.0), 0.0

    centroid = compute_table_centroid(tables)
    sxx = mean((table.x - centroid.x) ** 2 for table in tables)
    syy = mean((table.y - centroid.y) ** 2 for table in tables)
    sxy = mean((table.x - centroid.x) * (table.y - centroid.y) for table in tables)

    if abs(sxy) < 1e-9 and abs(sxx - syy) < 1e-9:
        return (1.0, 0.0), 0.0

    theta = 0.5 * math.atan2(2.0 * sxy, sxx - syy)
    axis = (math.cos(theta), math.sin(theta))

    trace = max(1e-9, sxx + syy)
    anisotropy = _clamp(abs(sxx - syy) / trace, 0.0, 1.0)
    return axis, anisotropy


def _axis_diagonal_strength(axis: tuple[float, float]) -> float:
    alignment = max(abs(axis[0]), abs(axis[1]))
    return _clamp((0.90 - alignment) / 0.20, 0.0, 1.0)


def _perpendicular(vector: tuple[float, float]) -> tuple[float, float]:
    return (-vector[1], vector[0])


def _blend_angle(current_angle: float, target_angle: float, blend: float) -> float:
    delta = math.atan2(math.sin(target_angle - current_angle), math.cos(target_angle - current_angle))
    return current_angle + delta * blend


def _clip_point(
    point: tuple[float, float],
    x_min: float,
    x_max: float,
    y_min: float,
    y_max: float,
) -> tuple[float, float]:
    return (
        _clamp(point[0], x_min, x_max),
        _clamp(point[1], y_min, y_max),
    )


def _lerp(start: float, end: float, t: float) -> float:
    return start + (end - start) * t


def _dot(a: tuple[float, float], b: tuple[float, float]) -> float:
    return a[0] * b[0] + a[1] * b[1]


def _distance(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _angle_delta_mod180(a_deg: float, b_deg: float) -> float:
    return abs(((a_deg - b_deg + 90.0) % 180.0) - 90.0)


def _normalize_angle_deg(value: float) -> float:
    return ((value + 180.0) % 360.0) - 180.0


def _deterministic_axis(first_idx: int, second_idx: int) -> tuple[float, float]:
    phase = (first_idx * 19 + second_idx * 37 + 1) * 0.6180339887498949
    return (math.cos(phase), math.sin(phase))


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))
