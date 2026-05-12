from __future__ import annotations

from dataclasses import dataclass
import itertools
import math
from statistics import mean

from aisi.core.models import LayoutProposal, SceneState, TableState, TableTarget


@dataclass(slots=True)
class AssignmentResult:
    table_targets: list[TableTarget]
    assignment_cost_total: float
    notes: list[str]


def assign_tables_to_targets_min_cost(
    scene_state: SceneState,
    target_slots: list[TableTarget],
) -> AssignmentResult:
    """Assign existing tables to target slots with a small, transparent min-cost search.

    For small tables counts, brute-force permutations are used so the mapping is
    exact and easy to reason about. The target geometry stays unchanged; only the
    source table-to-slot assignment changes.
    """
    sources = sorted(scene_state.tables, key=lambda table: table.table_id)
    if not sources or not target_slots:
        return AssignmentResult(table_targets=list(target_slots), assignment_cost_total=0.0, notes=[])

    if len(sources) != len(target_slots):
        return _assign_greedy(scene_state, sources, target_slots)

    n = len(sources)
    if n <= 6:
        return _assign_exhaustive(scene_state, sources, target_slots)

    return _assign_greedy(scene_state, sources, target_slots)


def _assign_exhaustive(
    scene_state: SceneState,
    sources: list[TableState],
    target_slots: list[TableTarget],
) -> AssignmentResult:
    best_cost = math.inf
    best_perm: tuple[int, ...] | None = None
    for perm in itertools.permutations(range(len(target_slots))):
        cost = _assignment_cost(scene_state, sources, target_slots, list(perm))
        if cost < best_cost:
            best_cost = cost
            best_perm = perm

    if best_perm is None:
        return AssignmentResult(table_targets=list(target_slots), assignment_cost_total=math.inf, notes=[])

    return _materialize_assignment(scene_state, sources, target_slots, list(best_perm), best_cost)


def _assign_greedy(
    scene_state: SceneState,
    sources: list[TableState],
    target_slots: list[TableTarget],
) -> AssignmentResult:
    remaining = set(range(len(target_slots)))
    assignment: list[int] = [-1] * len(sources)
    total_cost = 0.0

    for source_idx, source in enumerate(sources):
        best_slot = min(
            remaining,
            key=lambda slot_idx: _single_pair_cost(scene_state, source, target_slots[slot_idx], source_idx, slot_idx),
        )
        assignment[source_idx] = best_slot
        remaining.remove(best_slot)
        total_cost += _single_pair_cost(scene_state, source, target_slots[best_slot], source_idx, best_slot)

    return _materialize_assignment(scene_state, sources, target_slots, assignment, total_cost)


def _materialize_assignment(
    scene_state: SceneState,
    sources: list[TableState],
    target_slots: list[TableTarget],
    slot_for_source: list[int],
    total_cost: float,
) -> AssignmentResult:
    assigned_targets: list[TableTarget] = []
    notes: list[str] = [f"assignment_cost_total={total_cost:.3f}"]

    for source_idx, slot_idx in enumerate(slot_for_source):
        source = sources[source_idx]
        slot = target_slots[slot_idx]
        movement_distance = _distance((source.x, source.y), (slot.target_x, slot.target_y))
        assigned_targets.append(
            TableTarget(
                table_id=source.table_id,
                target_x=slot.target_x,
                target_y=slot.target_y,
                source_rot_deg=source.rot_deg,
                target_rot_deg=slot.target_rot_deg,
                facing_target_x=slot.facing_target_x,
                facing_target_y=slot.facing_target_y,
            )
        )
        notes.append(
            f"{source.table_id}:assigned_target_index={slot_idx}:movement_distance={movement_distance:.1f}"
        )

    notes.append(f"assignment_strategy={'exhaustive' if len(sources) <= 6 else 'greedy'}")
    return AssignmentResult(
        table_targets=assigned_targets,
        assignment_cost_total=total_cost,
        notes=notes,
    )


def _assignment_cost(
    scene_state: SceneState,
    sources: list[TableState],
    target_slots: list[TableTarget],
    slot_for_source: list[int],
) -> float:
    roi_diag = max(1.0, math.hypot(scene_state.roi.width, scene_state.roi.height))
    total = 0.0
    for source_idx, slot_idx in enumerate(slot_for_source):
        total += _single_pair_cost(scene_state, sources[source_idx], target_slots[slot_idx], source_idx, slot_idx)

    total -= _neighbor_preservation_bonus(sources, target_slots, slot_for_source)
    return total / max(1, len(sources))


def _single_pair_cost(
    scene_state: SceneState,
    source: TableState,
    target_slot: TableTarget,
    source_idx: int,
    slot_idx: int,
) -> float:
    roi_diag = max(1.0, math.hypot(scene_state.roi.width, scene_state.roi.height))
    movement = _distance((source.x, source.y), (target_slot.target_x, target_slot.target_y)) / roi_diag
    rotation = _angle_delta_deg(source.rot_deg, target_slot.target_rot_deg) / 180.0
    return (movement * 0.82) + (rotation * 0.18)


def _neighbor_preservation_bonus(
    sources: list[TableState],
    target_slots: list[TableTarget],
    slot_for_source: list[int],
) -> float:
    if len(sources) < 2:
        return 0.0

    source_pairs = _source_neighbor_pairs(sources)
    if not source_pairs:
        return 0.0

    bonus = 0.0
    max_slot_distance = max(1, len(target_slots) - 1)
    for source_a_idx, source_b_idx, proximity_weight in source_pairs:
        slot_a = slot_for_source[source_a_idx]
        slot_b = slot_for_source[source_b_idx]
        slot_distance = abs(slot_a - slot_b)
        preserved = 1.0 - (slot_distance / max_slot_distance)
        bonus += proximity_weight * max(0.0, preserved)

    return bonus * 0.03


def _source_neighbor_pairs(sources: list[TableState]) -> list[tuple[int, int, float]]:
    if len(sources) < 2:
        return []

    centroid_x = mean(source.x for source in sources)
    centroid_y = mean(source.y for source in sources)
    base_distances = [
        _distance((source.x, source.y), (centroid_x, centroid_y))
        for source in sources
    ]
    scale = max(1.0, mean(base_distances))

    pairs: list[tuple[int, int, float]] = []
    for idx in range(len(sources)):
        for jdx in range(idx + 1, len(sources)):
            distance = _distance((sources[idx].x, sources[idx].y), (sources[jdx].x, sources[jdx].y))
            proximity_weight = max(0.0, 1.0 - (distance / (scale * 1.3)))
            if proximity_weight > 0.0:
                pairs.append((idx, jdx, proximity_weight))
    return pairs


def _distance(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _angle_delta_deg(source: float, target: float) -> float:
    delta = (target - source + 180.0) % 360.0 - 180.0
    return abs(delta)
