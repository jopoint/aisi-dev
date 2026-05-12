from __future__ import annotations

import math

from aisi.core.models import LayoutProposal, ProposalEvaluation, SceneState, TargetProfile
from aisi.generation.layout_constraints import (
    compute_artificial_shape_penalty,
    compute_configuration_preservation_bonus,
    evaluate_hard_constraints,
)


def evaluate_layout_proposal(
    scene_state: SceneState,
    target_profile: TargetProfile,
    layout_proposal: LayoutProposal,
) -> ProposalEvaluation:
    """Evaluate a layout with transparent, coarse v0 scoring terms."""
    by_table_id = {table.table_id: table for table in scene_state.tables}

    movement_sum = 0.0
    rotation_sum = 0.0
    pair_count = 0

    for target in layout_proposal.table_targets:
        source = by_table_id.get(target.table_id)
        if source is None:
            continue

        movement_sum += math.hypot(target.target_x - source.x, target.target_y - source.y)
        rotation_sum += _angle_delta_deg(source.rot_deg, target.target_rot_deg)
        pair_count += 1

    if pair_count == 0:
        return ProposalEvaluation(
            movement_cost=0.0,
            rotation_cost=0.0,
            fit_score=0.0,
            total_score=0.0,
            details={"matched_tables": 0.0},
        )

    movement_cost = movement_sum / pair_count
    rotation_cost = rotation_sum / pair_count

    roi_diag = max(1.0, math.hypot(scene_state.roi.width, scene_state.roi.height))
    movement_quality = max(0.0, 1.0 - (movement_cost / (roi_diag * 0.55)))
    rotation_quality = max(0.0, 1.0 - (rotation_cost / 180.0))

    hard_stats = evaluate_hard_constraints(
        scene_state,
        layout_proposal.table_targets,
        overlap_gap=0.0,
        clearance_depth_factor=_clearance_depth_factor_for_format(scene_state.learning_format),
        generation_notes=layout_proposal.generation_notes,
    )
    overlap_violations = hard_stats.overlap_violations
    roi_violations = hard_stats.roi_violations
    clearance_violations = hard_stats.clearance_violations

    artificial_shape_penalty = compute_artificial_shape_penalty(scene_state, layout_proposal)
    input_shape_penalty = _compute_input_shape_penalty(scene_state, layout_proposal, movement_cost)
    combined_shape_penalty = _clamp(artificial_shape_penalty + (input_shape_penalty * 0.85), 0.0, 1.0)
    preservation_bonus = compute_configuration_preservation_bonus(scene_state, layout_proposal)
    repair_applied = _extract_generation_flag(layout_proposal, key="repair_applied", fallback=False)

    hard_violation_load = (
        overlap_violations * 1.0
        + roi_violations * 1.0
        + clearance_violations * 0.8
    )
    hard_constraint_quality = max(0.0, 1.0 - (hard_violation_load / max(1.0, float(pair_count))))
    shape_quality = max(0.0, 1.0 - combined_shape_penalty)

    target_weight = max(0.1, target_profile.target_area_orientation_fit.weight)
    fit_score = (
        movement_quality * 0.40
        + (rotation_quality * target_weight) * 0.18
        + hard_constraint_quality * 0.27
        + shape_quality * 0.10
        + preservation_bonus * 0.05
    )
    total_score = (
        (fit_score * 100.0)
        - (movement_cost * 0.04)
        - (rotation_cost * 0.08)
        - (hard_violation_load * 14.0)
        - (combined_shape_penalty * 8.0)
        + (preservation_bonus * 5.0)
    )

    return ProposalEvaluation(
        movement_cost=movement_cost,
        rotation_cost=rotation_cost,
        fit_score=fit_score,
        total_score=total_score,
        details={
            "matched_tables": float(pair_count),
            "movement_quality": movement_quality,
            "rotation_quality": rotation_quality,
            "hard_constraint_quality": hard_constraint_quality,
            "preservation_bonus": preservation_bonus,
            "overlap_violations": float(overlap_violations),
            "roi_violations": float(roi_violations),
            "clearance_violations": float(clearance_violations),
            "artificial_shape_penalty": artificial_shape_penalty,
            "input_shape_penalty": input_shape_penalty,
            "combined_shape_penalty": combined_shape_penalty,
            "repair_applied": repair_applied,
        },
    )


def _angle_delta_deg(source: float, target: float) -> float:
    delta = (target - source + 180.0) % 360.0 - 180.0
    return abs(delta)


def _extract_generation_flag(layout_proposal: LayoutProposal, key: str, fallback: bool) -> bool:
    prefix = f"{key}="
    for note in layout_proposal.generation_notes:
        if not note.startswith(prefix):
            continue
        raw = note[len(prefix) :].strip().lower()
        if raw in {"1", "true", "yes"}:
            return True
        if raw in {"0", "false", "no"}:
            return False
    return fallback


def _clearance_depth_factor_for_format(learning_format: str) -> float:
    if learning_format == "input":
        return 0.65
    if learning_format == "discussion":
        return 0.80
    return 1.0


def _compute_input_shape_penalty(
    scene_state: SceneState,
    layout_proposal: LayoutProposal,
    movement_cost: float,
) -> float:
    if scene_state.learning_format != "input":
        return 0.0

    source_points: list[tuple[float, float]] = []
    target_points: list[tuple[float, float]] = []
    by_id = {table.table_id: table for table in scene_state.tables}

    for target in layout_proposal.table_targets:
        source = by_id.get(target.table_id)
        if source is None:
            continue
        source_points.append((source.x, source.y))
        target_points.append((target.target_x, target.target_y))

    if len(target_points) < 3:
        return 0.0

    source_axis, source_anisotropy = _dominant_axis(source_points)
    target_axis, target_anisotropy = _dominant_axis(target_points)

    source_diag = _axis_diagonal_strength(source_axis) * source_anisotropy
    target_diag = _axis_diagonal_strength(target_axis) * target_anisotropy
    diag_excess = max(0.0, target_diag - source_diag - 0.08)

    row_layout = _extract_input_row_layout(layout_proposal)
    singleton_penalty = 0.12 * sum(1 for size in row_layout if size == 1)
    three_seat_penalty = 0.05 * sum(1 for size in row_layout if size == 3)
    extra_row_penalty = 0.05 * max(0, len(row_layout) - 2)

    rot_spread = _rotation_spread_mod180([target.target_rot_deg for target in layout_proposal.table_targets])

    roi_diag = max(1.0, math.hypot(scene_state.roi.width, scene_state.roi.height))
    movement_pressure = _clamp(movement_cost / (roi_diag * 0.24), 0.0, 1.0)

    return _clamp(
        (diag_excess * (0.30 + 0.70 * movement_pressure))
        + singleton_penalty
        + three_seat_penalty
        + extra_row_penalty
        + (rot_spread * 0.18),
        0.0,
        1.0,
    )


def _extract_input_row_layout(layout_proposal: LayoutProposal) -> list[int]:
    prefix = "input_row_layout="
    for note in layout_proposal.generation_notes:
        if not note.startswith(prefix):
            continue

        raw = note[len(prefix) :].strip()
        if not (raw.startswith("[") and raw.endswith("]")):
            continue

        values = [part.strip() for part in raw[1:-1].split(",") if part.strip()]
        layout: list[int] = []
        for value in values:
            if value.isdigit():
                layout.append(int(value))
        if layout:
            return layout

    return []


def _rotation_spread_mod180(rotations_deg: list[float]) -> float:
    if len(rotations_deg) < 2:
        return 0.0

    max_delta = 0.0
    for idx, first in enumerate(rotations_deg):
        for second in rotations_deg[idx + 1 :]:
            delta = abs(((first - second + 90.0) % 180.0) - 90.0)
            max_delta = max(max_delta, delta)

    return _clamp(max_delta / 40.0, 0.0, 1.0)


def _dominant_axis(points: list[tuple[float, float]]) -> tuple[tuple[float, float], float]:
    if len(points) < 2:
        return (1.0, 0.0), 0.0

    cx = sum(point[0] for point in points) / len(points)
    cy = sum(point[1] for point in points) / len(points)

    sxx = sum((point[0] - cx) ** 2 for point in points) / len(points)
    syy = sum((point[1] - cy) ** 2 for point in points) / len(points)
    sxy = sum((point[0] - cx) * (point[1] - cy) for point in points) / len(points)

    if abs(sxy) < 1e-9 and abs(sxx - syy) < 1e-9:
        return (1.0, 0.0), 0.0

    theta = 0.5 * math.atan2(2.0 * sxy, sxx - syy)
    axis = (math.cos(theta), math.sin(theta))
    anisotropy = _clamp(abs(sxx - syy) / max(1e-9, sxx + syy), 0.0, 1.0)
    return axis, anisotropy


def _axis_diagonal_strength(axis: tuple[float, float]) -> float:
    alignment = max(abs(axis[0]), abs(axis[1]))
    return _clamp((0.90 - alignment) / 0.20, 0.0, 1.0)


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))
