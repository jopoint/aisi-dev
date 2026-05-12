from __future__ import annotations

from dataclasses import dataclass
import math
from statistics import mean

from aisi.core.models import (
    LayoutProposal,
    ROI,
    SceneState,
    TableState,
    TableTarget,
    candidate_facing_normals,
    choose_facing_normal_toward_target,
)


@dataclass(slots=True)
class HardConstraintStats:
    overlap_violations: int = 0
    roi_violations: int = 0
    clearance_violations: int = 0

    @property
    def total_violations(self) -> int:
        return self.overlap_violations + self.roi_violations + self.clearance_violations


@dataclass(slots=True)
class RepairOutcome:
    table_targets: list[TableTarget]
    before: HardConstraintStats
    after: HardConstraintStats
    repair_applied: bool
    iterations: int


@dataclass(slots=True)
class PairContext:
    table_to_pair: dict[str, str]
    pair_to_tables: dict[str, list[str]]
    pair_geometry: dict[str, "PairGeometry"]


@dataclass(slots=True)
class PairGeometry:
    pair_id: str
    center: tuple[float, float]
    normal: tuple[float, float]
    gap_cm: float


@dataclass(slots=True)
class SeatSideInfo:
    seat_side: str
    opposite_side: str
    seat_direction: tuple[float, float]


DEFAULT_GROUPWORK_PAIR_GAP_CM = 74.0


def evaluate_hard_constraints(
    scene_state: SceneState,
    table_targets: list[TableTarget],
    *,
    overlap_gap: float = 0.0,
    clearance_depth_factor: float = 1.0,
    generation_notes: list[str] | None = None,
) -> HardConstraintStats:
    """Count hard-constraint violations for a table-only proposal.

    Notes:
    - Overlap uses OBB intersection (SAT) against rotated table rectangles.
    - Clearance is modeled as a directed OBB on the primary seat side only.
    """
    by_id = _table_state_by_id(scene_state)
    pair_context = _build_pair_context(generation_notes)
    targets = [target for target in table_targets if target.table_id in by_id]

    overlap_violations = 0
    for idx, target_a in enumerate(targets):
        state_a = by_id[target_a.table_id]
        for jdx in range(idx + 1, len(targets)):
            target_b = targets[jdx]
            state_b = by_id[target_b.table_id]
            if _obb_intersects(
                center_a=(target_a.target_x, target_a.target_y),
                width_a=state_a.width,
                height_a=state_a.height,
                rot_deg_a=target_a.target_rot_deg,
                center_b=(target_b.target_x, target_b.target_y),
                width_b=state_b.width,
                height_b=state_b.height,
                rot_deg_b=target_b.target_rot_deg,
                gap=overlap_gap,
            ):
                overlap_violations += 1

    roi_violations = 0
    for target in targets:
        state = by_id[target.table_id]
        if not _table_inside_roi(
            center=(target.target_x, target.target_y),
            width=state.width,
            height=state.height,
            rot_deg=target.target_rot_deg,
            roi=scene_state.roi,
        ):
            roi_violations += 1

    clearance_violations = 0
    for idx, target in enumerate(targets):
        state = by_id[target.table_id]
        zone = _primary_seat_clearance_zone(
            target=target,
            table_state=state,
            depth_factor=clearance_depth_factor,
        )

        blocked = False
        for jdx, other_target in enumerate(targets):
            if idx == jdx:
                continue
            if _is_groupwork_pair_contact(
                scene_state=scene_state,
                pair_context=pair_context,
                table_id=target.table_id,
                other_table_id=other_target.table_id,
            ):
                continue
            other_state = by_id[other_target.table_id]
            if _obb_intersects(
                center_a=(zone.cx, zone.cy),
                width_a=zone.width,
                height_a=zone.height,
                rot_deg_a=zone.rot_deg,
                center_b=(other_target.target_x, other_target.target_y),
                width_b=other_state.width,
                height_b=other_state.height,
                rot_deg_b=other_target.target_rot_deg,
                gap=0.0,
            ):
                blocked = True
                break

        if blocked:
            clearance_violations += 1

    return HardConstraintStats(
        overlap_violations=overlap_violations,
        roi_violations=roi_violations,
        clearance_violations=clearance_violations,
    )


def repair_layout_hard_constraints(
    scene_state: SceneState,
    table_targets: list[TableTarget],
    *,
    max_iterations: int = 28,
    overlap_gap: float = 6.0,
    clearance_depth_factor: float = 1.0,
    generation_notes: list[str] | None = None,
) -> RepairOutcome:
    """Iteratively repair hard constraints with local geometric nudges.

    This is not a global optimizer. It performs conservative local corrections:
    - clamp OBBs into ROI,
    - push apart overlapping tables,
    - push blockers out of seat-side clearance zones,
    - compact groupwork pair members when they drift too far apart.
    """
    by_id = _table_state_by_id(scene_state)
    pair_context = _build_pair_context(generation_notes)
    targets = [
        _copy_target(target)
        for target in table_targets
        if target.table_id in by_id
    ]

    before = evaluate_hard_constraints(
        scene_state,
        targets,
        overlap_gap=0.0,
        clearance_depth_factor=clearance_depth_factor,
        generation_notes=generation_notes,
    )

    compacted = _compact_groupwork_pair_targets(scene_state, targets, by_id, pair_context)
    if compacted:
        before = evaluate_hard_constraints(
            scene_state,
            targets,
            overlap_gap=0.0,
            clearance_depth_factor=clearance_depth_factor,
            generation_notes=generation_notes,
        )

    if before.total_violations == 0:
        return RepairOutcome(
            table_targets=targets,
            before=before,
            after=before,
            repair_applied=compacted,
            iterations=0,
        )

    repair_applied = False
    iterations_run = 0

    for iteration in range(max_iterations):
        iterations_run = iteration + 1
        changed = False

        for target in targets:
            table_state = by_id[target.table_id]
            clamped = _clamp_table_center_to_roi(
                center=(target.target_x, target.target_y),
                width=table_state.width,
                height=table_state.height,
                rot_deg=target.target_rot_deg,
                roi=scene_state.roi,
            )
            if _distance((target.target_x, target.target_y), clamped) > 1e-6:
                target.target_x, target.target_y = clamped
                changed = True

        changed = _compact_groupwork_pair_targets(scene_state, targets, by_id, pair_context) or changed

        for idx, target_a in enumerate(targets):
            state_a = by_id[target_a.table_id]
            for jdx in range(idx + 1, len(targets)):
                target_b = targets[jdx]
                state_b = by_id[target_b.table_id]

                is_pair_contact = _is_groupwork_pair_contact(
                    scene_state=scene_state,
                    pair_context=pair_context,
                    table_id=target_a.table_id,
                    other_table_id=target_b.table_id,
                )

                if is_pair_contact:
                    pair_fixed = _repair_groupwork_pair_overlap_if_needed(
                        scene_state=scene_state,
                        target_a=target_a,
                        target_b=target_b,
                        state_a=state_a,
                        state_b=state_b,
                        pair_context=pair_context,
                    )
                    changed = changed or pair_fixed
                    continue

                if not _obb_intersects(
                    center_a=(target_a.target_x, target_a.target_y),
                    width_a=state_a.width,
                    height_a=state_a.height,
                    rot_deg_a=target_a.target_rot_deg,
                    center_b=(target_b.target_x, target_b.target_y),
                    width_b=state_b.width,
                    height_b=state_b.height,
                    rot_deg_b=target_b.target_rot_deg,
                    gap=overlap_gap,
                ):
                    continue

                push_axis = _unit_vector(
                    (
                        target_b.target_x - target_a.target_x,
                        target_b.target_y - target_a.target_y,
                    ),
                    fallback=_deterministic_pair_axis(idx, jdx),
                )
                required = _required_separation_along_axis(
                    width_a=state_a.width,
                    height_a=state_a.height,
                    rot_deg_a=target_a.target_rot_deg,
                    width_b=state_b.width,
                    height_b=state_b.height,
                    rot_deg_b=target_b.target_rot_deg,
                    axis=push_axis,
                    gap=overlap_gap,
                )
                current = abs(
                    _dot(
                        (
                            target_b.target_x - target_a.target_x,
                            target_b.target_y - target_a.target_y,
                        ),
                        push_axis,
                    )
                )
                if current >= required:
                    continue

                delta = (required - current) * 0.52 + 1.0
                move_a = (-push_axis[0] * delta, -push_axis[1] * delta)
                move_b = (push_axis[0] * delta, push_axis[1] * delta)

                target_a.target_x += move_a[0]
                target_a.target_y += move_a[1]
                target_b.target_x += move_b[0]
                target_b.target_y += move_b[1]

                target_a.target_x, target_a.target_y = _clamp_table_center_to_roi(
                    center=(target_a.target_x, target_a.target_y),
                    width=state_a.width,
                    height=state_a.height,
                    rot_deg=target_a.target_rot_deg,
                    roi=scene_state.roi,
                )
                target_b.target_x, target_b.target_y = _clamp_table_center_to_roi(
                    center=(target_b.target_x, target_b.target_y),
                    width=state_b.width,
                    height=state_b.height,
                    rot_deg=target_b.target_rot_deg,
                    roi=scene_state.roi,
                )
                changed = True

        for idx, target in enumerate(targets):
            state = by_id[target.table_id]
            zone = _primary_seat_clearance_zone(
                target=target,
                table_state=state,
                depth_factor=clearance_depth_factor,
            )

            for jdx, other_target in enumerate(targets):
                if idx == jdx:
                    continue
                if _is_groupwork_pair_contact(
                    scene_state=scene_state,
                    pair_context=pair_context,
                    table_id=target.table_id,
                    other_table_id=other_target.table_id,
                ):
                    continue
                other_state = by_id[other_target.table_id]
                intersects = _obb_intersects(
                    center_a=(zone.cx, zone.cy),
                    width_a=zone.width,
                    height_a=zone.height,
                    rot_deg_a=zone.rot_deg,
                    center_b=(other_target.target_x, other_target.target_y),
                    width_b=other_state.width,
                    height_b=other_state.height,
                    rot_deg_b=other_target.target_rot_deg,
                    gap=0.0,
                )
                if not intersects:
                    continue

                push_axis = _unit_vector(
                    (
                        other_target.target_x - zone.cx,
                        other_target.target_y - zone.cy,
                    ),
                    fallback=zone.seat_direction,
                )
                required = _required_separation_along_axis(
                    width_a=zone.width,
                    height_a=zone.height,
                    rot_deg_a=zone.rot_deg,
                    width_b=other_state.width,
                    height_b=other_state.height,
                    rot_deg_b=other_target.target_rot_deg,
                    axis=push_axis,
                    gap=4.0,
                )
                current = abs(
                    _dot(
                        (
                            other_target.target_x - zone.cx,
                            other_target.target_y - zone.cy,
                        ),
                        push_axis,
                    )
                )
                step = max(3.0, (required - current) * 0.72 + 1.0)
                other_target.target_x += push_axis[0] * step
                other_target.target_y += push_axis[1] * step
                other_target.target_x, other_target.target_y = _clamp_table_center_to_roi(
                    center=(other_target.target_x, other_target.target_y),
                    width=other_state.width,
                    height=other_state.height,
                    rot_deg=other_target.target_rot_deg,
                    roi=scene_state.roi,
                )
                changed = True

            changed = _compact_groupwork_pair_targets(scene_state, targets, by_id, pair_context) or changed

        if changed:
            repair_applied = True

        current_stats = evaluate_hard_constraints(
            scene_state,
            targets,
            overlap_gap=0.0,
            clearance_depth_factor=clearance_depth_factor,
            generation_notes=generation_notes,
        )

        if current_stats.total_violations == 0:
            return RepairOutcome(
                table_targets=targets,
                before=before,
                after=current_stats,
                repair_applied=repair_applied,
                iterations=iterations_run,
            )

        if not changed:
            break

    after = evaluate_hard_constraints(
        scene_state,
        targets,
        overlap_gap=0.0,
        clearance_depth_factor=clearance_depth_factor,
        generation_notes=generation_notes,
    )
    return RepairOutcome(
        table_targets=targets,
        before=before,
        after=after,
        repair_applied=repair_applied,
        iterations=iterations_run,
    )


def compute_artificial_shape_penalty(
    scene_state: SceneState,
    layout_proposal: LayoutProposal,
) -> float:
    """Soft penalty for unusually artificial global figures.

    Strongly diagonal/sheared target figures are only penalized when they are
    more unusual than the source arrangement and do not save much movement.
    """
    pairs = _source_target_pairs(scene_state, layout_proposal.table_targets)
    if len(pairs) < 3:
        return 0.0

    source_points = [source for source, _ in pairs]
    target_points = [target for _, target in pairs]

    source_axis, source_anisotropy = _dominant_axis(source_points)
    target_axis, target_anisotropy = _dominant_axis(target_points)

    source_diag = _axis_diagonal_strength(source_axis) * source_anisotropy
    target_diag = _axis_diagonal_strength(target_axis) * target_anisotropy

    source_shear = _shear_strength(source_points, source_axis)
    target_shear = _shear_strength(target_points, target_axis)

    avg_movement = mean(_distance(source, target) for source, target in pairs)
    roi_diag = max(1.0, math.hypot(scene_state.roi.width, scene_state.roi.height))
    movement_pressure = _clamp(avg_movement / (roi_diag * 0.24), 0.0, 1.0)

    diag_excess = max(0.0, target_diag - source_diag - 0.10)
    if scene_state.learning_format == "input":
        shear_excess = max(0.0, target_shear - source_shear - 0.12)
        shear_weight = 0.55
    else:
        shear_excess = max(0.0, target_shear - source_shear - 0.18)
        shear_weight = 0.25

    raw_penalty = (diag_excess * 0.82) + (shear_excess * shear_weight)
    weighted_penalty = raw_penalty * (0.35 + 0.65 * movement_pressure)
    return _clamp(weighted_penalty, 0.0, 1.0)


def compute_configuration_preservation_bonus(
    scene_state: SceneState,
    layout_proposal: LayoutProposal,
) -> float:
    """Bonus when pairwise source spacing is preserved plausibly."""
    pairs = _source_target_pairs(scene_state, layout_proposal.table_targets)
    if len(pairs) < 2:
        return 0.0

    source_points = [source for source, _ in pairs]
    target_points = [target for _, target in pairs]

    source_distances = _pairwise_distances(source_points)
    target_distances = _pairwise_distances(target_points)
    if not source_distances:
        return 0.0

    mean_source = max(1.0, mean(source_distances))
    rmse = math.sqrt(
        mean((target_distances[idx] - source_distances[idx]) ** 2 for idx in range(len(source_distances)))
    )
    normalized_rmse = rmse / mean_source

    return _clamp(1.0 - (normalized_rmse / 0.60), 0.0, 1.0)


@dataclass(slots=True)
class _SeatClearanceZone:
    cx: float
    cy: float
    width: float
    height: float
    rot_deg: float
    seat_direction: tuple[float, float]
    seat_side: str
    opposite_side: str


def _primary_seat_clearance_zone(
    target: TableTarget,
    table_state: TableState,
    depth_factor: float,
) -> _SeatClearanceZone:
    seat_info = _seat_side_info(target)
    depth = max(table_state.width * depth_factor, table_state.height * 0.72)
    center_offset = (table_state.height * 0.5) + (depth * 0.5)

    cx = target.target_x + seat_info.seat_direction[0] * center_offset
    cy = target.target_y + seat_info.seat_direction[1] * center_offset

    return _SeatClearanceZone(
        cx=cx,
        cy=cy,
        width=max(18.0, table_state.width * 0.58),
        height=max(16.0, depth),
        rot_deg=target.target_rot_deg,
        seat_direction=seat_info.seat_direction,
        seat_side=seat_info.seat_side,
        opposite_side=seat_info.opposite_side,
    )


def _facing_vector(target: TableTarget) -> tuple[float, float]:
    center = (target.target_x, target.target_y)
    if target.facing_target_x is not None and target.facing_target_y is not None:
        return choose_facing_normal_toward_target(
            table_center=center,
            target_point=(target.facing_target_x, target.facing_target_y),
            rot_deg=target.target_rot_deg,
        )

    normal_a, normal_b = candidate_facing_normals(target.target_rot_deg)
    return normal_a if normal_a[1] <= normal_b[1] else normal_b


def _seat_side_info(target: TableTarget) -> SeatSideInfo:
    facing = _facing_vector(target)
    _, short_axis = _axes_from_rotation(target.target_rot_deg)
    side_sign = 1.0 if _dot(facing, short_axis) >= 0.0 else -1.0

    seat_direction = _unit_vector(
        (short_axis[0] * side_sign, short_axis[1] * side_sign),
        fallback=(short_axis[0], short_axis[1]),
    )
    if side_sign >= 0.0:
        seat_side = "long_side_pos_normal"
        opposite_side = "long_side_neg_normal"
    else:
        seat_side = "long_side_neg_normal"
        opposite_side = "long_side_pos_normal"

    return SeatSideInfo(
        seat_side=seat_side,
        opposite_side=opposite_side,
        seat_direction=seat_direction,
    )


def _build_pair_context(generation_notes: list[str] | None) -> PairContext:
    table_to_pair: dict[str, str] = {}
    pair_to_tables: dict[str, list[str]] = {}
    pair_geometry: dict[str, PairGeometry] = {}
    if not generation_notes:
        return PairContext(
            table_to_pair=table_to_pair,
            pair_to_tables=pair_to_tables,
            pair_geometry=pair_geometry,
        )

    prefix = "groupwork_assignments="
    for note in generation_notes:
        if not note.startswith(prefix):
            continue

        payload = note[len(prefix) :]
        for entry in payload.split(","):
            mapping = entry.strip()
            if "->" not in mapping:
                continue

            table_id, pair_id = [item.strip() for item in mapping.split("->", 1)]
            if not table_id or not pair_id:
                continue

            table_to_pair[table_id] = pair_id
            pair_to_tables.setdefault(pair_id, []).append(table_id)

    for pair_id in list(pair_to_tables):
        pair_to_tables[pair_id] = sorted(set(pair_to_tables[pair_id]))

    geometry_prefix = "groupwork_pair_geometry="
    for note in generation_notes:
        if not note.startswith(geometry_prefix):
            continue

        payload = note[len(geometry_prefix) :].strip()
        if not payload:
            continue

        for entry in payload.split(";"):
            packed = entry.strip()
            if not packed:
                continue

            tokens = [token.strip() for token in packed.split("|") if token.strip()]
            if not tokens:
                continue

            pair_id = tokens[0]
            center = None
            normal = None
            gap_cm = None
            for token in tokens[1:]:
                if token.startswith("center="):
                    center = _parse_pair_geometry_vector(token[len("center=") :])
                elif token.startswith("normal="):
                    normal = _parse_pair_geometry_vector(token[len("normal=") :])
                elif token.startswith("gap_cm="):
                    gap_cm = _parse_float(token[len("gap_cm=") :])

            if center is None or normal is None:
                continue

            normal_unit = _unit_vector(normal, fallback=(1.0, 0.0))
            pair_geometry[pair_id] = PairGeometry(
                pair_id=pair_id,
                center=center,
                normal=normal_unit,
                gap_cm=gap_cm if gap_cm is not None else DEFAULT_GROUPWORK_PAIR_GAP_CM,
            )

    return PairContext(
        table_to_pair=table_to_pair,
        pair_to_tables=pair_to_tables,
        pair_geometry=pair_geometry,
    )


def _is_groupwork_pair_contact(
    scene_state: SceneState,
    pair_context: PairContext,
    table_id: str,
    other_table_id: str,
) -> bool:
    if scene_state.learning_format != "groupwork":
        return False

    pair_id = pair_context.table_to_pair.get(table_id)
    if pair_id is None:
        return False

    members = pair_context.pair_to_tables.get(pair_id, [])
    return len(members) >= 2 and other_table_id in members


def _compact_groupwork_pair_targets(
    scene_state: SceneState,
    targets: list[TableTarget],
    by_id: dict[str, TableState],
    pair_context: PairContext,
) -> bool:
    if scene_state.learning_format != "groupwork" or not pair_context.pair_to_tables:
        return False

    by_target_id = {target.table_id: target for target in targets}
    changed = False

    for pair_id, members in pair_context.pair_to_tables.items():
        if len(members) != 2:
            continue

        first_id, second_id = members
        first = by_target_id.get(first_id)
        second = by_target_id.get(second_id)
        first_state = by_id.get(first_id)
        second_state = by_id.get(second_id)
        if first is None or second is None or first_state is None or second_state is None:
            continue

        pair_geometry = pair_context.pair_geometry.get(pair_id)
        if pair_geometry is not None:
            pair_normal = _unit_vector(pair_geometry.normal, fallback=(1.0, 0.0))
            preferred_gap = max(1.0, pair_geometry.gap_cm)
        else:
            pair_normal = _unit_vector(
                (second.target_x - first.target_x, second.target_y - first.target_y),
                fallback=(1.0, 0.0),
            )
            preferred_gap = DEFAULT_GROUPWORK_PAIR_GAP_CM

        min_pair_gap = preferred_gap
        max_pair_gap = preferred_gap + 5.0

        signed_distance = _dot(
            (second.target_x - first.target_x, second.target_y - first.target_y),
            pair_normal,
        )
        direction_sign = 1.0 if signed_distance >= 0.0 else -1.0
        current_gap = abs(signed_distance)

        if current_gap < min_pair_gap:
            push = ((min_pair_gap - current_gap) * 0.56) + 0.75
            move = (
                pair_normal[0] * direction_sign * push,
                pair_normal[1] * direction_sign * push,
            )
            first.target_x -= move[0]
            first.target_y -= move[1]
            second.target_x += move[0]
            second.target_y += move[1]

            first.target_x, first.target_y = _clamp_table_center_to_roi(
                center=(first.target_x, first.target_y),
                width=first_state.width,
                height=first_state.height,
                rot_deg=first.target_rot_deg,
                roi=scene_state.roi,
            )
            second.target_x, second.target_y = _clamp_table_center_to_roi(
                center=(second.target_x, second.target_y),
                width=second_state.width,
                height=second_state.height,
                rot_deg=second.target_rot_deg,
                roi=scene_state.roi,
            )
            changed = True
            continue

        if current_gap <= max_pair_gap:
            continue

        pull = current_gap - max_pair_gap
        move = (
            pair_normal[0] * direction_sign * pull * 0.5,
            pair_normal[1] * direction_sign * pull * 0.5,
        )

        first.target_x += move[0]
        first.target_y += move[1]
        second.target_x -= move[0]
        second.target_y -= move[1]

        first.target_x, first.target_y = _clamp_table_center_to_roi(
            center=(first.target_x, first.target_y),
            width=first_state.width,
            height=first_state.height,
            rot_deg=first.target_rot_deg,
            roi=scene_state.roi,
        )
        second.target_x, second.target_y = _clamp_table_center_to_roi(
            center=(second.target_x, second.target_y),
            width=second_state.width,
            height=second_state.height,
            rot_deg=second.target_rot_deg,
            roi=scene_state.roi,
        )
        changed = True

    return changed


def _repair_groupwork_pair_overlap_if_needed(
    scene_state: SceneState,
    target_a: TableTarget,
    target_b: TableTarget,
    state_a: TableState,
    state_b: TableState,
    pair_context: PairContext,
) -> bool:
    pair_id = pair_context.table_to_pair.get(target_a.table_id)
    if pair_id is None or pair_context.table_to_pair.get(target_b.table_id) != pair_id:
        return False

    geometry = pair_context.pair_geometry.get(pair_id)
    if geometry is not None:
        pair_normal = _unit_vector(geometry.normal, fallback=(1.0, 0.0))
        desired_gap = max(1.0, geometry.gap_cm)
    else:
        pair_normal = _unit_vector(
            (target_b.target_x - target_a.target_x, target_b.target_y - target_a.target_y),
            fallback=(1.0, 0.0),
        )
        desired_gap = DEFAULT_GROUPWORK_PAIR_GAP_CM

    delta = (target_b.target_x - target_a.target_x, target_b.target_y - target_a.target_y)
    signed = _dot(delta, pair_normal)
    direction_sign = 1.0 if signed >= 0.0 else -1.0
    projected_gap = abs(signed)

    required_no_overlap_gap = _required_separation_along_axis(
        width_a=state_a.width,
        height_a=state_a.height,
        rot_deg_a=target_a.target_rot_deg,
        width_b=state_b.width,
        height_b=state_b.height,
        rot_deg_b=target_b.target_rot_deg,
        axis=pair_normal,
        gap=1.0,
    )
    target_gap = max(desired_gap, required_no_overlap_gap)

    intersects = _obb_intersects(
        center_a=(target_a.target_x, target_a.target_y),
        width_a=state_a.width,
        height_a=state_a.height,
        rot_deg_a=target_a.target_rot_deg,
        center_b=(target_b.target_x, target_b.target_y),
        width_b=state_b.width,
        height_b=state_b.height,
        rot_deg_b=target_b.target_rot_deg,
        gap=0.0,
    )

    if projected_gap >= target_gap and not intersects:
        return False

    push = ((target_gap - projected_gap) * 0.58) + 0.75
    move = (
        pair_normal[0] * direction_sign * push,
        pair_normal[1] * direction_sign * push,
    )
    target_a.target_x -= move[0]
    target_a.target_y -= move[1]
    target_b.target_x += move[0]
    target_b.target_y += move[1]

    target_a.target_x, target_a.target_y = _clamp_table_center_to_roi(
        center=(target_a.target_x, target_a.target_y),
        width=state_a.width,
        height=state_a.height,
        rot_deg=target_a.target_rot_deg,
        roi=scene_state.roi,
    )
    target_b.target_x, target_b.target_y = _clamp_table_center_to_roi(
        center=(target_b.target_x, target_b.target_y),
        width=state_b.width,
        height=state_b.height,
        rot_deg=target_b.target_rot_deg,
        roi=scene_state.roi,
    )
    return True


def _parse_pair_geometry_vector(value: str) -> tuple[float, float] | None:
    parts = [part.strip() for part in value.split(",")]
    if len(parts) != 2:
        return None
    x_value = _parse_float(parts[0])
    y_value = _parse_float(parts[1])
    if x_value is None or y_value is None:
        return None
    return (x_value, y_value)


def _parse_float(value: str) -> float | None:
    try:
        return float(value)
    except ValueError:
        return None


def _source_target_pairs(
    scene_state: SceneState,
    table_targets: list[TableTarget],
) -> list[tuple[tuple[float, float], tuple[float, float]]]:
    by_id = _table_state_by_id(scene_state)
    pairs: list[tuple[tuple[float, float], tuple[float, float]]] = []
    for target in table_targets:
        source = by_id.get(target.table_id)
        if source is None:
            continue
        pairs.append(((source.x, source.y), (target.target_x, target.target_y)))
    return pairs


def _pairwise_distances(points: list[tuple[float, float]]) -> list[float]:
    distances: list[float] = []
    for idx in range(len(points)):
        for jdx in range(idx + 1, len(points)):
            distances.append(_distance(points[idx], points[jdx]))
    return distances


def _table_state_by_id(scene_state: SceneState) -> dict[str, TableState]:
    return {table.table_id: table for table in scene_state.tables}


def _copy_target(target: TableTarget) -> TableTarget:
    return TableTarget(
        table_id=target.table_id,
        target_x=target.target_x,
        target_y=target.target_y,
        source_rot_deg=target.source_rot_deg,
        target_rot_deg=target.target_rot_deg,
        facing_target_x=target.facing_target_x,
        facing_target_y=target.facing_target_y,
    )


def _table_inside_roi(
    center: tuple[float, float],
    width: float,
    height: float,
    rot_deg: float,
    roi: ROI,
) -> bool:
    extent_x, extent_y = _obb_extents_on_world_axes(width, height, rot_deg)
    return (
        center[0] - extent_x >= roi.x_min
        and center[0] + extent_x <= roi.x_max
        and center[1] - extent_y >= roi.y_min
        and center[1] + extent_y <= roi.y_max
    )


def _clamp_table_center_to_roi(
    center: tuple[float, float],
    width: float,
    height: float,
    rot_deg: float,
    roi: ROI,
) -> tuple[float, float]:
    extent_x, extent_y = _obb_extents_on_world_axes(width, height, rot_deg)
    x_min = roi.x_min + extent_x
    x_max = roi.x_max - extent_x
    y_min = roi.y_min + extent_y
    y_max = roi.y_max - extent_y

    if x_min > x_max:
        clamped_x = (roi.x_min + roi.x_max) * 0.5
    else:
        clamped_x = _clamp(center[0], x_min, x_max)

    if y_min > y_max:
        clamped_y = (roi.y_min + roi.y_max) * 0.5
    else:
        clamped_y = _clamp(center[1], y_min, y_max)

    return (clamped_x, clamped_y)


def _obb_extents_on_world_axes(width: float, height: float, rot_deg: float) -> tuple[float, float]:
    long_axis, short_axis = _axes_from_rotation(rot_deg)
    half_w = max(1.0, width) * 0.5
    half_h = max(1.0, height) * 0.5
    extent_x = abs(long_axis[0]) * half_w + abs(short_axis[0]) * half_h
    extent_y = abs(long_axis[1]) * half_w + abs(short_axis[1]) * half_h
    return extent_x, extent_y


def _required_separation_along_axis(
    width_a: float,
    height_a: float,
    rot_deg_a: float,
    width_b: float,
    height_b: float,
    rot_deg_b: float,
    axis: tuple[float, float],
    gap: float,
) -> float:
    return (
        _projected_half_extent(width_a, height_a, rot_deg_a, axis)
        + _projected_half_extent(width_b, height_b, rot_deg_b, axis)
        + max(0.0, gap)
    )


def _projected_half_extent(
    width: float,
    height: float,
    rot_deg: float,
    axis: tuple[float, float],
) -> float:
    long_axis, short_axis = _axes_from_rotation(rot_deg)
    half_w = max(1.0, width) * 0.5
    half_h = max(1.0, height) * 0.5
    return abs(_dot(axis, long_axis)) * half_w + abs(_dot(axis, short_axis)) * half_h


def _obb_intersects(
    center_a: tuple[float, float],
    width_a: float,
    height_a: float,
    rot_deg_a: float,
    center_b: tuple[float, float],
    width_b: float,
    height_b: float,
    rot_deg_b: float,
    gap: float,
) -> bool:
    axes_a = _axes_from_rotation(rot_deg_a)
    axes_b = _axes_from_rotation(rot_deg_b)
    delta = (center_b[0] - center_a[0], center_b[1] - center_a[1])

    for axis in (axes_a[0], axes_a[1], axes_b[0], axes_b[1]):
        required = _required_separation_along_axis(
            width_a=width_a,
            height_a=height_a,
            rot_deg_a=rot_deg_a,
            width_b=width_b,
            height_b=height_b,
            rot_deg_b=rot_deg_b,
            axis=axis,
            gap=gap,
        )
        projection = abs(_dot(delta, axis))
        if projection > required:
            return False

    return True


def _axes_from_rotation(rot_deg: float) -> tuple[tuple[float, float], tuple[float, float]]:
    theta = math.radians(rot_deg)
    long_axis = (math.cos(theta), math.sin(theta))
    short_axis = (-math.sin(theta), math.cos(theta))
    return long_axis, short_axis


def _dominant_axis(points: list[tuple[float, float]]) -> tuple[tuple[float, float], float]:
    if len(points) < 2:
        return (1.0, 0.0), 0.0

    cx = mean(point[0] for point in points)
    cy = mean(point[1] for point in points)
    sxx = mean((point[0] - cx) ** 2 for point in points)
    syy = mean((point[1] - cy) ** 2 for point in points)
    sxy = mean((point[0] - cx) * (point[1] - cy) for point in points)

    if abs(sxy) < 1e-9 and abs(sxx - syy) < 1e-9:
        return (1.0, 0.0), 0.0

    theta = 0.5 * math.atan2(2.0 * sxy, sxx - syy)
    axis = (math.cos(theta), math.sin(theta))

    trace = max(1e-9, sxx + syy)
    anisotropy = _clamp(abs(sxx - syy) / trace, 0.0, 1.0)
    return axis, anisotropy


def _shear_strength(points: list[tuple[float, float]], axis: tuple[float, float]) -> float:
    if len(points) < 3:
        return 0.0

    normal = (-axis[1], axis[0])
    cx = mean(point[0] for point in points)
    cy = mean(point[1] for point in points)

    projected_u = [_dot((point[0] - cx, point[1] - cy), axis) for point in points]
    projected_v = [_dot((point[0] - cx, point[1] - cy), normal) for point in points]

    mean_u = mean(projected_u)
    mean_v = mean(projected_v)

    var_u = mean((value - mean_u) ** 2 for value in projected_u)
    var_v = mean((value - mean_v) ** 2 for value in projected_v)
    if var_u <= 1e-6 or var_v <= 1e-6:
        return 0.0

    cov = mean((u - mean_u) * (v - mean_v) for u, v in zip(projected_u, projected_v))
    corr = abs(cov) / math.sqrt(var_u * var_v)
    return _clamp(corr, 0.0, 1.0)


def _axis_diagonal_strength(axis: tuple[float, float]) -> float:
    alignment = max(abs(axis[0]), abs(axis[1]))
    return _clamp((0.90 - alignment) / 0.20, 0.0, 1.0)


def _deterministic_pair_axis(idx: int, jdx: int) -> tuple[float, float]:
    phase = (idx * 17 + jdx * 31 + 1) * 0.6180339887498949
    return _unit_vector((math.cos(phase), math.sin(phase)), fallback=(1.0, 0.0))


def _unit_vector(
    vector: tuple[float, float],
    fallback: tuple[float, float],
) -> tuple[float, float]:
    norm = math.hypot(vector[0], vector[1])
    if norm <= 1e-9:
        return fallback
    return (vector[0] / norm, vector[1] / norm)


def _distance(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _dot(a: tuple[float, float], b: tuple[float, float]) -> float:
    return a[0] * b[0] + a[1] * b[1]


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))
