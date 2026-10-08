"""Quelladaptiver Suchkern für Rect Groupwork.

Der Suchkern enumeriert für kleine Szenen alle Pair-/Singleton-Partitionen und
bewertet lokale, frei gedrehte Pair-Anordnungen gegen die kanonischen harten
Geometriebedingungen. Analyseplots und produktive Synthese verwenden dieselbe
Geometrie.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from functools import lru_cache
import itertools
import math
from typing import Callable, Iterable

from aisi.core.models import SceneState, TableState, TableTarget
from aisi.core.table_geometry import (
    convex_polygons_intersect,
    polygon_inside_roi,
    required_table_center_separation,
    resolve_table_state_geometry,
    table_support_distance,
    table_world_footprint,
    footprint_bounds,
    transform_local_footprint,
)
PAIR_SEAM_CM = 8.0
SEAT_CLEARANCE_DEPTH_CM = 60.0
SINGLETON_OUTER_CORNER_RADIUS_CM = 30.0
_RESULT_CACHE_LIMIT = 32
_result_cache: dict[tuple[object, ...], "PrototypeResult"] = {}


@dataclass(frozen=True, slots=True)
class PrototypeObjective:
    pair_orientation_deviation_deg: float
    max_displacement_cm: float
    total_displacement_cm: float
    total_rotation_change_deg: float
    crossing_count: int
    min_intergroup_gap_cm: float
    clearance_overlap_area_cm2: float

    def key(self) -> tuple[float, float, float, float, int]:
        return (
            round(self.pair_orientation_deviation_deg, 8),
            round(self.max_displacement_cm, 8),
            round(self.total_displacement_cm, 8),
            round(self.total_rotation_change_deg, 8),
            self.crossing_count,
        )


@dataclass(frozen=True, slots=True)
class PrototypeResult:
    table_targets: tuple[TableTarget, ...]
    groups: tuple[tuple[str, ...], ...]
    generation_notes: tuple[str, ...]
    objective: PrototypeObjective
    used_refinement: bool


@dataclass(frozen=True, slots=True)
class _GroupOption:
    targets: tuple[TableTarget, ...]
    group_ids: tuple[str, ...]
    geometry_note: str | None
    refinement: bool


def solve_rect_groupwork_prototype(
    scene_state: SceneState,
    *,
    selection: str = "movement",
    movement_budget_cm: float | None = None,
    cluster_sizes: tuple[int, ...] | None = None,
    candidate_filter: Callable[[PrototypeResult], bool] | None = None,
) -> PrototypeResult:
    """Return the best local Rect Groupwork candidate for counts two through five.

    Angles are derived from source vectors and refined by real-valued local
    offsets; they are never snapped to an orthogonal or other angle raster.
    ``table_id`` is carried only by the emitted target, never used for pairing
    or geometric ordering.
    """
    cache_key = _solver_cache_key(scene_state, selection, movement_budget_cm)
    cache_key += (cluster_sizes,)
    cached = _result_cache.get(cache_key) if candidate_filter is None else None
    if cached is not None:
        return cached

    tables = tuple(scene_state.tables)
    if not 2 <= len(tables) <= 5:
        raise ValueError("Der adaptive Rect-Groupwork-Prototyp unterstützt Counts 2–5.")
    if any(table.table_type not in (None, "rect") for table in tables):
        raise ValueError("Der adaptive Prototyp ist ausschließlich für Rect-Tische bestimmt.")

    candidates: list[PrototypeResult] = []
    option_geometry = {}
    option_compatibility = {}
    filtered_best_key = None
    for refined in (False, True):
        partitions = (enumerate_pair_partitions(tables) if cluster_sizes is None
                      else enumerate_cluster_partitions(tables, cluster_sizes))
        for partition in partitions:
            option_sets = [
                _select_local_options(
                    scene_state,
                    tuple(
                        _fit_option_to_roi(scene_state, option)
                        for option in _group_options(group, pair_index=index, refined=refined,
                                                     expanded_singletons=cluster_sizes is not None,
                                                     singleton_rotations=(tuple(t.rot_deg for t in tables)
                                                        if selection == 'source_movement' else ()))
                    ),
                    # Twelve representatives preserve source-oriented outward
                    # candidates for every local island without expanding the
                    # exhaustive cross-product to the full raw option set.
                    limit=(8 if len(partition) >= 4 else 12) if refined else None,
                )
                for index, group in enumerate(partition)
            ]
            combinations = (_compatible_option_combinations(scene_state, option_sets,
                                option_geometry, option_compatibility)
                            if candidate_filter is not None else itertools.product(*option_sets))
            for selected_options in combinations:
                if filtered_best_key is not None:
                    selected = {t.table_id:t for option in selected_options for t in option.targets}
                    # Use original Scene Order, matching _objective's sum and
                    # rounding exactly. No costly geometry/objective rebuild
                    # is needed when displacement alone already loses.
                    distances = [math.dist((t.x,t.y),(selected[t.table_id].target_x,
                        selected[t.table_id].target_y)) for t in scene_state.tables]
                    if (round(max(distances),8),round(sum(distances),8)) > filtered_best_key[:2]:
                        continue
                candidate = _materialize_candidate(scene_state, partition, selected_options, refined)
                if candidate is None:
                    continue
                # Seat feasibility cannot improve the displacement objective.
                # Once a fully accepted result exists, worse/equal candidates
                # cannot win; equality retains the original first-result tie.
                candidate_key = (_source_movement_candidate_key(candidate)
                    if selection == 'source_movement' and candidate_filter is not None else None)
                if candidate_key is not None and filtered_best_key is not None and candidate_key >= filtered_best_key:
                    continue
                if candidate_filter is not None and not candidate_filter(candidate):
                    continue
                if candidate_key is not None:
                    filtered_best_key = candidate_key
                candidates.append(candidate)

    if not candidates:
        raise ValueError("Keine quelladaptive Rect-Groupwork-Lösung erfüllt alle harten Bedingungen.")
    if selection == "movement":
        result = min(candidates, key=_candidate_key)
        return _cache_result(cache_key, result) if candidate_filter is None else result
    if selection == "clearance":
        result = min(candidates, key=_clearance_candidate_key)
        return _cache_result(cache_key, result) if candidate_filter is None else result
    if selection == "source_movement":
        result = min(candidates, key=_source_movement_candidate_key)
        return _cache_result(cache_key, result) if candidate_filter is None else result
    if selection != "spread":
        raise ValueError("selection muss 'movement', 'clearance', 'source_movement' oder 'spread' sein.")

    minimum_max_movement = min(candidate.objective.max_displacement_cm for candidate in candidates)
    if movement_budget_cm is None:
        raise ValueError("Die Spread-Auswahl benötigt ein explizites Bewegungsbudget.")
    eligible = [
        candidate
        for candidate in candidates
        if candidate.objective.max_displacement_cm <= minimum_max_movement + movement_budget_cm + 1e-8
    ]
    result = min(eligible, key=_spread_candidate_key)
    return _cache_result(cache_key, result) if candidate_filter is None else result


def _solver_cache_key(
    scene_state: SceneState,
    selection: str,
    movement_budget_cm: float | None,
) -> tuple[object, ...]:
    """Create a bounded deterministic cache key for unchanged live scenes."""
    return (
        selection,
        None if movement_budget_cm is None else round(movement_budget_cm, 8),
        round(scene_state.roi.x_min, 8),
        round(scene_state.roi.y_min, 8),
        round(scene_state.roi.x_max, 8),
        round(scene_state.roi.y_max, 8),
        tuple(
            (
                table.table_id,
                round(table.x, 8),
                round(table.y, 8),
                round(table.rot_deg, 8),
                round(table.width, 8),
                round(table.height, 8),
                table.table_type,
            )
            for table in scene_state.tables
        ),
    )


def _cache_result(cache_key: tuple[object, ...], result: "PrototypeResult") -> "PrototypeResult":
    """Keep only a small number of complete live-scene solves in memory."""
    if len(_result_cache) >= _RESULT_CACHE_LIMIT:
        _result_cache.pop(next(iter(_result_cache)))
    _result_cache[cache_key] = result
    return result


def enumerate_pair_partitions(tables: Iterable[TableState]) -> tuple[tuple[tuple[TableState, ...], ...], ...]:
    """Enumerate all pair partitions, with exactly one singleton for odd counts.

    The canonical order is spatial, avoiding an accidental dependence on IDs or
    on the incoming Scene Order.
    """
    ordered = tuple(sorted(tables, key=_spatial_key))

    def build(remaining: tuple[TableState, ...]) -> list[tuple[tuple[TableState, ...], ...]]:
        if not remaining:
            return [()]
        first, rest = remaining[0], remaining[1:]
        built: list[tuple[tuple[TableState, ...], ...]] = []
        if len(remaining) % 2:
            for remainder in build(rest):
                built.append(((first,), *remainder))
        for index, other in enumerate(rest):
            after_pair = rest[:index] + rest[index + 1 :]
            for remainder in build(after_pair):
                built.append(((first, other), *remainder))
        return built

    partitions = build(ordered)
    return tuple(sorted(partitions, key=_partition_geometry_key))


def enumerate_cluster_partitions(tables: Iterable[TableState], sizes: tuple[int, ...]):
    """Enumerate requested singleton/pair topology without assigning social groups."""
    ordered = tuple(sorted(tables, key=_spatial_key))
    if sum(sizes) != len(ordered) or any(size not in (1, 2) for size in sizes):
        raise ValueError("Clustergrößen müssen die Tische vollständig in Singletons/Pairs aufteilen.")

    def build(remaining, pending):
        if not remaining:
            yield ()
            return
        first, rest = remaining[0], remaining[1:]
        for size in sorted(set(pending)):
            after_size = list(pending)
            after_size.remove(size)
            for companions in itertools.combinations(range(len(rest)), size - 1):
                group = (first, *(rest[index] for index in companions))
                after = tuple(table for index, table in enumerate(rest) if index not in companions)
                for tail in build(after, tuple(after_size)):
                    yield (group, *tail)
    return tuple(sorted(build(ordered, sizes), key=_partition_geometry_key))


def singleton_end_clearance_regions(target: TableTarget, table: TableState):
    """Canonical rounded 60-cm strips on the two Rect short ends."""
    geometry = resolve_table_state_geometry(table)
    rotation = target.target_rot_deg % 180
    angle = math.radians(rotation)
    long_axis = (math.cos(angle), math.sin(angle))
    offset = geometry.nominal_width * 0.5 + SEAT_CLEARANCE_DEPTH_CM * 0.5
    return tuple(
        transform_local_footprint(
            _rounded_outer_singleton_strip(geometry.nominal_depth, SEAT_CLEARANCE_DEPTH_CM,
                                           outer_direction=direction),
            target.target_x - direction * long_axis[0] * offset,
            target.target_y - direction * long_axis[1] * offset,
            rotation + 90.0,
        ) for direction in (-1.0, 1.0)
    )


def _compatible_option_combinations(scene_state, option_sets, geometry_cache, compatibility_cache):
    """Discard only canonically invalid combinations; retain product order.

    Caches belong to one solve, so geometry never survives a changed source,
    ROI or table shape. Final materialization still runs its complete guard.
    """
    tables = {t.table_id:t for t in scene_state.tables}
    prepared_sets = []
    for options in option_sets:
        prepared = []
        for option in options:
            key = tuple((t.table_id,t.target_x,t.target_y,t.target_rot_deg) for t in option.targets)
            if key not in geometry_cache:
                ids = tuple(t.table_id for t in option.targets)
                if not _satisfies_prototype_hard_constraints(scene_state,option.targets,(ids,),()):
                    geometry_cache[key] = None
                else:
                    footprints = tuple(table_world_footprint(tables[t.table_id],
                        (t.target_x,t.target_y),t.target_rot_deg) for t in option.targets)
                    regions = _clearance_regions_for_group(list(option.targets),tables)
                    geometry_cache[key] = footprints,regions
            if geometry_cache[key] is not None:
                prepared.append((option,key))
        prepared_sets.append(prepared)

    def compatible(first, second):
        key = first[1],second[1]
        if key not in compatibility_cache:
            first_tables,first_regions = geometry_cache[key[0]]
            second_tables,second_regions = geometry_cache[key[1]]
            compatibility_cache[key] = not any(
                _polygons_overlap_with_positive_area(a,b)
                for first_polygons,second_polygons in ((first_tables,second_tables),
                    (first_regions,second_tables),(second_regions,first_tables))
                for a in first_polygons for b in second_polygons)
        return compatibility_cache[key]

    for choice in itertools.product(*prepared_sets):
        if all(compatible(a,b) for a,b in itertools.combinations(choice,2)):
            yield tuple(item[0] for item in choice)


def _group_options(group: tuple[TableState, ...], *, pair_index: int, refined: bool,
                   expanded_singletons: bool = False,
                   singleton_rotations: tuple[float, ...] = ()) -> tuple[_GroupOption, ...]:
    if len(group) == 1:
        table = group[0]
        options = list(_singleton_options(table, refined=refined, expanded=expanded_singletons))
        # Participant planning may rotate in place instead of moving a distant
        # table into this role. Angles remain source-derived, with no fixed slots.
        for rotation in sorted(set(singleton_rotations)):
            angle = table.rot_deg + (rotation-table.rot_deg+90.) % 180. - 90.
            if abs(angle-table.rot_deg) < 1e-8:
                continue
            for option in _singleton_options(replace(table,rot_deg=angle),
                                              refined=refined,expanded=expanded_singletons):
                options.append(replace(option,targets=tuple(
                    replace(target,source_rot_deg=table.rot_deg) for target in option.targets)))
        return tuple(_deduplicate_options(options))
    return _pair_options(group[0], group[1], pair_index=pair_index, refined=refined)


def _pair_options(
    first: TableState,
    second: TableState,
    *,
    pair_index: int,
    refined: bool,
) -> tuple[_GroupOption, ...]:
    midpoint = ((first.x + second.x) * 0.5, (first.y + second.y) * 0.5)
    # Pair orientation follows the axial mean of its two source tables.  The
    # source positions still determine the local midpoint, but must not rotate
    # a vertical pair into a horizontal target simply because the two source
    # centers happen to be offset horizontally.
    base_rotation = _axial_mean_rotation(first.rot_deg, second.rot_deg)
    normal = _rotation_to_short_axis(base_rotation)
    separation = required_table_center_separation(
        first, base_rotation, second, base_rotation, normal, gap=PAIR_SEAM_CM
    )

    angle_offsets = (0.0,) if not refined else tuple(dict.fromkeys(
        (
            0.0, -17.0, 17.0, -34.0, 34.0, -51.0, 51.0, -68.0, 68.0,
            -8.5, 8.5, -4.25, 4.25,
            # The search remains continuous/source-derived.  These additional
            # candidates merely allow a near-cardinal source vector to align
            # exactly with an ROI edge when the clearance region otherwise
            # leaves only a zero-tolerance packing solution.
            *(_normalize_angle(axis - base_rotation) for axis in (0.0, 90.0, -90.0, 180.0)),
        )
    ))
    local_offsets = ((0.0, 0.0),) if not refined else (
        (0.0, 0.0), (12.0, 0.0), (-12.0, 0.0), (0.0, 12.0),
        (0.0, -12.0), (24.0, 0.0), (-24.0, 0.0), (0.0, 24.0),
        (0.0, -24.0), (48.0, 0.0), (-48.0, 0.0), (0.0, 48.0),
        (0.0, -48.0), (96.0, 0.0), (-96.0, 0.0), (0.0, 96.0),
        (0.0, -96.0), (144.0, 0.0), (-144.0, 0.0),
    )
    options: list[_GroupOption] = []
    for angle_offset in angle_offsets:
        rotation = _normalize_angle(base_rotation + angle_offset)
        current_normal = _rotation_to_short_axis(rotation)
        tangent = (current_normal[1], -current_normal[0])
        for normal_offset, tangent_offset in local_offsets:
            center = (
                midpoint[0] + current_normal[0] * normal_offset + tangent[0] * tangent_offset,
                midpoint[1] + current_normal[1] * normal_offset + tangent[1] * tangent_offset,
            )
            lower = (center[0] - current_normal[0] * separation * 0.5, center[1] - current_normal[1] * separation * 0.5)
            upper = (center[0] + current_normal[0] * separation * 0.5, center[1] + current_normal[1] * separation * 0.5)
            for swapped in (False, True):
                first_slot, second_slot = (upper, lower) if swapped else (lower, upper)
                targets = (
                    _target(first, first_slot, rotation, _outward_facing(first_slot, center)),
                    _target(second, second_slot, rotation, _outward_facing(second_slot, center)),
                )
                options.append(
                    _GroupOption(
                        targets=targets,
                        group_ids=(f"pair{pair_index}", f"pair{pair_index}"),
                        geometry_note=(
                            f"pair{pair_index}|center={center[0]:.6f},{center[1]:.6f}|"
                            f"normal={current_normal[0]:.6f},{current_normal[1]:.6f}|gap_cm={PAIR_SEAM_CM:.3f}"
                        ),
                        refinement=refined and (angle_offset != 0.0 or normal_offset != 0.0 or tangent_offset != 0.0),
                    )
                )
    return tuple(_deduplicate_options(options))


def _singleton_options(table: TableState, *, refined: bool, expanded: bool = False) -> tuple[_GroupOption, ...]:
    normal = _rotation_to_short_axis(table.rot_deg)
    tangent = (normal[1], -normal[0])
    offsets = ((0.0, 0.0),) if not refined else (
        (0.0, 0.0), (12.0, 0.0), (-12.0, 0.0), (0.0, 12.0), (0.0, -12.0),
        (48.0, 0.0), (-48.0, 0.0), (0.0, 48.0), (0.0, -48.0),
        (96.0, 0.0), (-96.0, 0.0), (0.0, 96.0), (0.0, -96.0),
    )
    if refined and expanded:
        offsets += ((144.0,0.0),(-144.0,0.0),(0.0,144.0),(0.0,-144.0))
    options: list[_GroupOption] = []
    for normal_offset, tangent_offset in offsets:
        point = (
            table.x + normal[0] * normal_offset + tangent[0] * tangent_offset,
            table.y + normal[1] * normal_offset + tangent[1] * tangent_offset,
        )
        options.append(
            _GroupOption(
                targets=(_target(table, point, table.rot_deg, normal),),
                group_ids=("singleton",),
                geometry_note=None,
                refinement=refined and (normal_offset != 0.0 or tangent_offset != 0.0),
            )
        )
    return tuple(_deduplicate_options(options))


def _materialize_candidate(
    scene_state: SceneState,
    partition: tuple[tuple[TableState, ...], ...],
    options: tuple[_GroupOption, ...],
    refined: bool,
) -> PrototypeResult | None:
    targets_by_id: dict[str, TableTarget] = {}
    assignments: list[str] = []
    geometry_notes: list[str] = []
    used_refinement = False
    for option in options:
        for target, group_id in zip(option.targets, option.group_ids):
            targets_by_id[target.table_id] = target
            assignments.append(f"{target.table_id}->{group_id}")
        if option.geometry_note:
            geometry_notes.append(option.geometry_note)
        used_refinement = used_refinement or option.refinement

    targets = tuple(targets_by_id[table.table_id] for table in scene_state.tables)
    notes = (
        "rect_groupwork_prototype=adaptive_local",
        f"groupwork_assignments={', '.join(assignments)}",
        f"groupwork_pair_geometry={'; '.join(geometry_notes)}",
        f"groupwork_pair_seam_gap_cm={PAIR_SEAM_CM:.1f}",
    )
    groups = tuple(tuple(table.table_id for table in group) for group in partition)
    if not _satisfies_prototype_hard_constraints(scene_state, targets, groups, notes):
        return None
    return PrototypeResult(
        table_targets=targets,
        groups=groups,
        generation_notes=notes,
        objective=_objective(scene_state, targets, groups),
        used_refinement=used_refinement or refined,
    )


def _satisfies_prototype_hard_constraints(
    scene_state: SceneState,
    targets: tuple[TableTarget, ...],
    groups: tuple[tuple[str, ...], ...],
    generation_notes: tuple[str, ...],
) -> bool:
    """Apply canonical footprint checks plus type-specific 60-cm clearances.

    Singletons receive two complete long-side strips. Pairs receive an ellipse
    around their joint footprint, avoiding a square's overemphasis on corners.
    This remains prototype-only.
    """
    # ``evaluate_hard_constraints`` adds the legacy, one-sided rectangular
    # Groupwork clearance.  Rect Groupwork deliberately replaces that model
    # with the approved singleton strips and pair ellipses below.  Checking
    # only the shared table-footprint invariants here avoids evaluating a
    # superseded clearance model for every search candidate.
    tables_by_id = {table.table_id: table for table in scene_state.tables}
    footprints = {
        target.table_id: table_world_footprint(
            tables_by_id[target.table_id],
            (target.target_x, target.target_y),
            target.target_rot_deg,
        )
        for target in targets
    }
    group_regions = _group_clearance_regions(scene_state, targets, groups)
    if any(
        not polygon_inside_roi(
            footprint,
            x_min=scene_state.roi.x_min,
            y_min=scene_state.roi.y_min,
            x_max=scene_state.roi.x_max,
            y_max=scene_state.roi.y_max,
        )
        for footprint in footprints.values()
    ) or any(
        _polygons_overlap_with_positive_area(first, second)
        for first, second in itertools.combinations(footprints.values(), 2)
    ) or any(
        not polygon_inside_roi(
            region,
            x_min=scene_state.roi.x_min,
            y_min=scene_state.roi.y_min,
            x_max=scene_state.roi.x_max,
            y_max=scene_state.roi.y_max,
        )
        for _, regions in group_regions
        for region in regions
    ):
        return False

    for group, regions in group_regions:
        for other in targets:
            if other.table_id in group:
                continue
            other_polygon = footprints[other.table_id]
            if any(_polygons_overlap_with_positive_area(region, other_polygon) for region in regions):
                return False
    return True


def _all_group_clearance_regions_inside_roi(
    scene_state: SceneState,
    targets: tuple[TableTarget, ...],
    groups: tuple[tuple[str, ...], ...],
) -> bool:
    return all(
        polygon_inside_roi(
            region,
            x_min=scene_state.roi.x_min,
            y_min=scene_state.roi.y_min,
            x_max=scene_state.roi.x_max,
            y_max=scene_state.roi.y_max,
        )
        for _, regions in _group_clearance_regions(scene_state, targets, groups)
        for region in regions
    )


def _group_clearance_regions(
    scene_state: SceneState,
    targets: tuple[TableTarget, ...],
    groups: tuple[tuple[str, ...], ...],
) -> tuple[tuple[tuple[str, ...], tuple[tuple[tuple[float, float], ...], ...]], ...]:
    """Return the approved clearance polygons for every island."""
    targets_by_id = {target.table_id: target for target in targets}
    tables_by_id = {table.table_id: table for table in scene_state.tables}
    return tuple(
        (
            group,
            _clearance_regions_for_group(
                [targets_by_id[table_id] for table_id in group],
                tables_by_id,
            ),
        )
        for group in groups
    )


def _clearance_regions_for_group(
    targets: list[TableTarget],
    tables_by_id: dict[str, TableState],
) -> tuple[tuple[tuple[float, float], ...], ...]:
    """Return singleton long-side strips or a rounded pair ellipse."""
    if len(targets) == 1:
        return singleton_long_side_clearance_regions(targets[0], tables_by_id[targets[0].table_id])
    return (_pair_clearance_ellipse(targets, tables_by_id),)


def singleton_long_side_clearance_regions(
    target: TableTarget,
    table: TableState,
    *,
    clearance_depth_cm: float = SEAT_CLEARANCE_DEPTH_CM,
) -> tuple[tuple[tuple[float, float], ...], tuple[tuple[float, float], ...]]:
    """Return two full-width strips with rounded table-distant corners."""
    geometry = resolve_table_state_geometry(table)
    short_axis = _rotation_to_short_axis(target.target_rot_deg)
    offset = table_support_distance(table, target.target_rot_deg, short_axis) + clearance_depth_cm * 0.5
    return tuple(
        transform_local_footprint(
            _rounded_outer_singleton_strip(
                geometry.nominal_width,
                clearance_depth_cm,
                outer_direction=direction,
            ),
            target.target_x + direction * short_axis[0] * offset,
            target.target_y + direction * short_axis[1] * offset,
            target.target_rot_deg,
        )
        for direction in (-1.0, 1.0)
    )


def single_long_side_clearance_region(
    target: TableTarget,
    table: TableState,
    *,
    seat_direction: tuple[float, float],
    clearance_depth_cm: float,
) -> tuple[tuple[float, float], ...]:
    """Return one rounded, full-width clearance strip on a semantic long side."""
    geometry = resolve_table_state_geometry(table)
    short_axis = _rotation_to_short_axis(target.target_rot_deg)
    direction = 1.0 if short_axis[0] * seat_direction[0] + short_axis[1] * seat_direction[1] >= 0.0 else -1.0
    offset = table_support_distance(table, target.target_rot_deg, short_axis) + clearance_depth_cm * 0.5
    return transform_local_footprint(
        _rounded_outer_singleton_strip(geometry.nominal_width, clearance_depth_cm, outer_direction=direction),
        target.target_x + direction * short_axis[0] * offset,
        target.target_y + direction * short_axis[1] * offset,
        target.target_rot_deg,
    )


# Compatibility alias for existing analysis scripts.  Product code should use
# the descriptive shared helper above and pass an explicit depth where needed.
_singleton_long_side_regions = singleton_long_side_clearance_regions


def _rounded_outer_singleton_strip(
    width: float,
    depth: float,
    *,
    outer_direction: float,
) -> tuple[tuple[float, float], ...]:
    """Return one local strip with its two table-distant corners rounded.

    The straight edge facing the table retains the complete long-side seating
    width.  A 30-cm radius rounds only the two far corners of the 60-cm-deep
    strip, matching the approved singleton sketch without adding end seating.
    """
    return _cached_rounded_outer_strip(width,depth,
        1.0 if outer_direction >= 0.0 else -1.0,
        min(SINGLETON_OUTER_CORNER_RADIUS_CM,width*0.5,depth))


@lru_cache(maxsize=64)
def _cached_rounded_outer_strip(width, depth, outer_sign, radius):
    """Cache only immutable local geometry, including its effective radius."""
    half_width = width * 0.5
    half_depth = depth * 0.5
    vertices: list[tuple[float, float]] = [
        (-half_width, -outer_sign * half_depth),
        (half_width, -outer_sign * half_depth),
        (half_width, outer_sign * (half_depth - radius)),
    ]
    for index in range(1, 9):
        angle = index * (math.pi * 0.5 / 8.0)
        vertices.append(
            (
                half_width - radius + radius * math.cos(angle),
                outer_sign * (half_depth - radius + radius * math.sin(angle)),
            )
        )
    vertices.append((-half_width + radius, outer_sign * half_depth))
    for index in range(1, 9):
        angle = math.pi * 0.5 + index * (math.pi * 0.5 / 8.0)
        vertices.append(
            (
                -half_width + radius + radius * math.cos(angle),
                outer_sign * (half_depth - radius + radius * math.sin(angle)),
            )
        )
    return tuple(vertices)


def _pair_clearance_ellipse(
    targets: list[TableTarget],
    tables_by_id: dict[str, TableState],
) -> tuple[tuple[float, float], ...]:
    """Circumscribe a pair with a 60-cm cardinal-radius ellipse.

    The ellipse keeps a 60-cm extension at the pair's long and short extrema,
    while its curved diagonals avoid turning the pair into a square clearance
    box.  Its axes derive from the pair's actual target orientation.
    """
    rotation = targets[0].target_rot_deg
    short_axis = _rotation_to_short_axis(rotation)
    long_axis = (short_axis[1], -short_axis[0])
    vertices = [
        vertex
        for target in targets
        for vertex in table_world_footprint(
            tables_by_id[target.table_id],
            (target.target_x, target.target_y),
            target.target_rot_deg,
        )
    ]
    short_values = [vertex[0] * short_axis[0] + vertex[1] * short_axis[1] for vertex in vertices]
    long_values = [vertex[0] * long_axis[0] + vertex[1] * long_axis[1] for vertex in vertices]
    short_center = (min(short_values) + max(short_values)) * 0.5
    long_center = (min(long_values) + max(long_values)) * 0.5
    short_radius = (max(short_values) - min(short_values)) * 0.5 + SEAT_CLEARANCE_DEPTH_CM
    long_radius = (max(long_values) - min(long_values)) * 0.5 + SEAT_CLEARANCE_DEPTH_CM

    def point(short_value: float, long_value: float) -> tuple[float, float]:
        return (
            short_axis[0] * short_value + long_axis[0] * long_value,
            short_axis[1] * short_value + long_axis[1] * long_value,
        )

    return tuple(
        point(
            short_center + short_radius * math.sin(index * math.tau / 48.0),
            long_center + long_radius * math.cos(index * math.tau / 48.0),
        )
        for index in range(48)
    )


@lru_cache(maxsize=4096)
def _polygons_overlap_with_positive_area(
    first: tuple[tuple[float, float], ...],
    second: tuple[tuple[float, float], ...],
) -> bool:
    """Treat exactly 60 cm of separation as valid; reject only area overlap."""
    # A conservative broad phase: only clearly disjoint canonical bounds
    # bypass SAT. Near contacts retain the existing tolerances and checks.
    if len(first) >= 3 and len(second) >= 3:
        first_bounds,second_bounds = footprint_bounds(first),footprint_bounds(second)
        if (first_bounds[2] < second_bounds[0]-1e-7 or second_bounds[2] < first_bounds[0]-1e-7
            or first_bounds[3] < second_bounds[1]-1e-7 or second_bounds[3] < first_bounds[1]-1e-7):
            return False
    if not convex_polygons_intersect(first, second):
        return False
    for polygon in (first, second):
        for start, end in zip(polygon, polygon[1:] + polygon[:1]):
            axis = (-(end[1] - start[1]), end[0] - start[0])
            first_values = [point[0] * axis[0] + point[1] * axis[1] for point in first]
            second_values = [point[0] * axis[0] + point[1] * axis[1] for point in second]
            if max(first_values) <= min(second_values) + 1e-7 or max(second_values) <= min(first_values) + 1e-7:
                return False
    return True


def _fit_option_to_roi(scene_state: SceneState, option: _GroupOption) -> _GroupOption:
    """Translate an entire local group only as far as its clearance needs."""
    tables_by_id = {table.table_id: table for table in scene_state.tables}
    polygons = _clearance_regions_for_group(list(option.targets), tables_by_id)
    min_x = min(x for polygon in polygons for x, _ in polygon)
    max_x = max(x for polygon in polygons for x, _ in polygon)
    min_y = min(y for polygon in polygons for _, y in polygon)
    max_y = max(y for polygon in polygons for _, y in polygon)
    shift_x = max(scene_state.roi.x_min - min_x, 0.0) + min(scene_state.roi.x_max - max_x, 0.0)
    shift_y = max(scene_state.roi.y_min - min_y, 0.0) + min(scene_state.roi.y_max - max_y, 0.0)
    if abs(shift_x) <= 1e-9 and abs(shift_y) <= 1e-9:
        return option

    shifted_targets = tuple(
        TableTarget(
            table_id=target.table_id,
            target_x=target.target_x + shift_x,
            target_y=target.target_y + shift_y,
            source_rot_deg=target.source_rot_deg,
            target_rot_deg=target.target_rot_deg,
            facing_target_x=target.facing_target_x + shift_x if target.facing_target_x is not None else None,
            facing_target_y=target.facing_target_y + shift_y if target.facing_target_y is not None else None,
        )
        for target in option.targets
    )
    note = option.geometry_note
    if note:
        note = f"{note}|roi_shift={shift_x:.6f},{shift_y:.6f}"
    return _GroupOption(
        targets=shifted_targets,
        group_ids=option.group_ids,
        geometry_note=note,
        refinement=True,
    )


def _select_local_options(
    scene_state: SceneState,
    options: tuple[_GroupOption, ...],
    *,
    limit: int | None,
) -> tuple[_GroupOption, ...]:
    """Keep the locally least-invasive candidates before global enumeration."""
    if limit is None or len(options) <= limit:
        return options
    sources = {table.table_id: table for table in scene_state.tables}

    def key(option: _GroupOption) -> tuple[float, float, float, float, tuple]:
        movements = [
            math.dist((sources[target.table_id].x, sources[target.table_id].y), (target.target_x, target.target_y))
            for target in option.targets
        ]
        rotations = [
            _angular_distance(sources[target.table_id].rot_deg, target.target_rot_deg)
            for target in option.targets
        ]
        geometry = tuple(
            (round(target.target_x, 5), round(target.target_y, 5), round(target.target_rot_deg, 5))
            for target in option.targets
        )
        orientation_deviation = (
            _axial_angular_distance(
                _axial_mean_rotation(*(sources[target.table_id].rot_deg for target in option.targets)),
                option.targets[0].target_rot_deg,
            )
            if len(option.targets) == 2
            else 0.0
        )
        return orientation_deviation, max(movements), sum(movements), sum(rotations), geometry

    ranked = sorted(options, key=key)
    selected = ranked[: max(1, limit // 2)]
    source_center = (
        sum(sources[target.table_id].x for target in options[0].targets) / len(options[0].targets),
        sum(sources[target.table_id].y for target in options[0].targets) / len(options[0].targets),
    )

    def target_center(option: _GroupOption) -> tuple[float, float]:
        return (
            sum(target.target_x for target in option.targets) / len(option.targets),
            sum(target.target_y for target in option.targets) / len(option.targets),
        )

    def direction(option: _GroupOption) -> int | None:
        center = target_center(option)
        dx, dy = center[0] - source_center[0], center[1] - source_center[1]
        if math.hypot(dx, dy) <= 1e-8:
            return None
        return int(round(math.atan2(dy, dx) / (math.pi / 4.0))) % 8

    def orientation_deviation(option: _GroupOption) -> float:
        if len(option.targets) != 2:
            return 0.0
        return _axial_angular_distance(
            _axial_mean_rotation(*(sources[target.table_id].rot_deg for target in option.targets)),
            option.targets[0].target_rot_deg,
        )

    def add(option: _GroupOption) -> None:
        if option not in selected and len(selected) < limit:
            selected.append(option)

    # Preserve locally minimal candidates, but also retain an outward candidate
    # in every source-relative direction.  The outward representative must
    # retain the pair's source orientation whenever possible; otherwise the
    # finite prefilter can discard the only zero-overlap composition that
    # respects the approved rotation preference.
    for sector in range(8):
        candidates = [option for option in ranked if direction(option) == sector]
        if candidates:
            add(
                min(
                    candidates,
                    key=lambda option: (
                        orientation_deviation(option),
                        -math.dist(target_center(option), source_center),
                    ),
                )
            )
    for chooser in (lambda point: point[0], lambda point: -point[0], lambda point: point[1], lambda point: -point[1]):
        add(max(ranked, key=lambda option: chooser(target_center(option))))
    add(min(ranked, key=lambda option: option.targets[0].target_rot_deg))
    add(max(ranked, key=lambda option: option.targets[0].target_rot_deg))
    for index in range(len(ranked)):
        if len(selected) >= limit:
            break
        add(ranked[index])
    return tuple(selected)


def _objective(
    scene_state: SceneState,
    targets: tuple[TableTarget, ...],
    groups: tuple[tuple[str, ...], ...],
) -> PrototypeObjective:
    source_by_id = {table.table_id: table for table in scene_state.tables}
    distances = [
        math.dist((source_by_id[target.table_id].x, source_by_id[target.table_id].y), (target.target_x, target.target_y))
        for target in targets
    ]
    rotations = [
        _angular_distance(source_by_id[target.table_id].rot_deg, target.target_rot_deg)
        for target in targets
    ]
    targets_by_id = {target.table_id: target for target in targets}
    pair_orientation_deviation = sum(
        _axial_angular_distance(
            _axial_mean_rotation(*(source_by_id[table_id].rot_deg for table_id in group)),
            targets_by_id[group[0]].target_rot_deg,
        )
        for group in groups
        if len(group) == 2
    )
    segments = [
        ((source_by_id[target.table_id].x, source_by_id[target.table_id].y), (target.target_x, target.target_y))
        for target in targets
    ]
    crossings = sum(
        _segments_cross(first, second)
        for index, first in enumerate(segments)
        for second in segments[index + 1 :]
    )
    return PrototypeObjective(
        pair_orientation_deviation,
        max(distances),
        sum(distances),
        sum(rotations),
        crossings,
        _minimum_intergroup_gap(scene_state, targets, groups),
        _clearance_overlap_area(scene_state, targets, groups),
    )


def _candidate_key(result: PrototypeResult) -> tuple[float, float, float, float, int, tuple]:
    geometry_key = tuple(
        (round(target.target_x, 6), round(target.target_y, 6), round(target.target_rot_deg, 6))
        for target in sorted(result.table_targets, key=lambda target: (target.target_x, target.target_y, target.target_rot_deg))
    )
    return (*result.objective.key(), geometry_key)


def _source_movement_candidate_key(result: PrototypeResult) -> tuple:
    """Rank valid participant candidates by source displacement before rotation."""
    objective = result.objective
    return (round(objective.max_displacement_cm, 8),
            round(objective.total_displacement_cm, 8),
            round(objective.total_rotation_change_deg, 8),
            objective.crossing_count, *_candidate_key(result))


def _spread_candidate_key(result: PrototypeResult) -> tuple[float, float, float, float, float, float, int, tuple]:
    objective = result.objective
    geometry_key = tuple(
        (round(target.target_x, 6), round(target.target_y, 6), round(target.target_rot_deg, 6))
        for target in sorted(result.table_targets, key=lambda target: (target.target_x, target.target_y, target.target_rot_deg))
    )
    return (
        round(objective.clearance_overlap_area_cm2, 8),
        round(objective.pair_orientation_deviation_deg, 8),
        -round(objective.min_intergroup_gap_cm, 8),
        round(objective.max_displacement_cm, 8),
        round(objective.total_displacement_cm, 8),
        round(objective.total_rotation_change_deg, 8),
        objective.crossing_count,
        geometry_key,
    )


def _clearance_candidate_key(result: PrototypeResult) -> tuple[float, float, float, float, float, int, float, tuple]:
    """Aggressively seek minimal zone overlap without a movement cap."""
    objective = result.objective
    geometry_key = tuple(
        (round(target.target_x, 6), round(target.target_y, 6), round(target.target_rot_deg, 6))
        for target in sorted(result.table_targets, key=lambda target: (target.target_x, target.target_y, target.target_rot_deg))
    )
    return (
        round(objective.clearance_overlap_area_cm2, 8),
        round(objective.pair_orientation_deviation_deg, 8),
        round(objective.max_displacement_cm, 8),
        round(objective.total_displacement_cm, 8),
        round(objective.total_rotation_change_deg, 8),
        objective.crossing_count,
        -round(objective.min_intergroup_gap_cm, 8),
        geometry_key,
    )


def _clearance_overlap_area(
    scene_state: SceneState,
    targets: tuple[TableTarget, ...],
    groups: tuple[tuple[str, ...], ...],
) -> float:
    """Return total pairwise overlap of regions belonging to different islands."""
    regions = _group_clearance_regions(scene_state, targets, groups)
    return sum(
        _convex_intersection_area(first_region, second_region)
        for first_index, (_, first_regions) in enumerate(regions)
        for _, second_regions in regions[first_index + 1 :]
        for first_region in first_regions
        for second_region in second_regions
    )


def _convex_intersection_area(
    subject: tuple[tuple[float, float], ...],
    clipper: tuple[tuple[float, float], ...],
) -> float:
    """Clip two convex polygons and return their intersection area."""
    output = list(subject)
    orientation = 1.0 if _signed_polygon_area(clipper) >= 0.0 else -1.0
    for edge_start, edge_end in zip(clipper, clipper[1:] + clipper[:1]):
        if not output:
            return 0.0
        input_points = output
        output = []
        previous = input_points[-1]
        previous_inside = _is_inside_edge(previous, edge_start, edge_end, orientation)
        for current in input_points:
            current_inside = _is_inside_edge(current, edge_start, edge_end, orientation)
            if current_inside != previous_inside:
                output.append(_line_intersection(previous, current, edge_start, edge_end))
            if current_inside:
                output.append(current)
            previous, previous_inside = current, current_inside
    return abs(_signed_polygon_area(tuple(output)))


def _is_inside_edge(
    point: tuple[float, float],
    edge_start: tuple[float, float],
    edge_end: tuple[float, float],
    orientation: float,
) -> bool:
    cross = (edge_end[0] - edge_start[0]) * (point[1] - edge_start[1]) - (edge_end[1] - edge_start[1]) * (point[0] - edge_start[0])
    return cross * orientation >= -1e-9


def _line_intersection(
    first_start: tuple[float, float],
    first_end: tuple[float, float],
    second_start: tuple[float, float],
    second_end: tuple[float, float],
) -> tuple[float, float]:
    first_vector = (first_end[0] - first_start[0], first_end[1] - first_start[1])
    second_vector = (second_end[0] - second_start[0], second_end[1] - second_start[1])
    denominator = first_vector[0] * second_vector[1] - first_vector[1] * second_vector[0]
    if abs(denominator) <= 1e-12:
        return first_end
    offset = (second_start[0] - first_start[0], second_start[1] - first_start[1])
    ratio = (offset[0] * second_vector[1] - offset[1] * second_vector[0]) / denominator
    return (first_start[0] + ratio * first_vector[0], first_start[1] + ratio * first_vector[1])


def _signed_polygon_area(polygon: tuple[tuple[float, float], ...]) -> float:
    return 0.5 * sum(
        start[0] * end[1] - end[0] * start[1]
        for start, end in zip(polygon, polygon[1:] + polygon[:1])
    )


def _minimum_intergroup_gap(
    scene_state: SceneState,
    targets: tuple[TableTarget, ...],
    groups: tuple[tuple[str, ...], ...],
) -> float:
    """Return minimum support-derived gap between tables in different groups."""
    if len(groups) < 2:
        return math.inf
    group_by_id = {
        table_id: group_index
        for group_index, group in enumerate(groups)
        for table_id in group
    }
    source_by_id = {table.table_id: table for table in scene_state.tables}
    gaps: list[float] = []
    for index, first in enumerate(targets):
        for second in targets[index + 1 :]:
            if group_by_id[first.table_id] == group_by_id[second.table_id]:
                continue
            first_polygon = table_world_footprint(
                source_by_id[first.table_id], (first.target_x, first.target_y), first.target_rot_deg
            )
            second_polygon = table_world_footprint(
                source_by_id[second.table_id], (second.target_x, second.target_y), second.target_rot_deg
            )
            gaps.append(_polygon_distance(first_polygon, second_polygon))
    return min(gaps) if gaps else math.inf


def _polygon_distance(
    first: tuple[tuple[float, float], ...], second: tuple[tuple[float, float], ...]
) -> float:
    return min(
        _point_segment_distance(point, segment_start, segment_end)
        for polygon, other in ((first, second), (second, first))
        for point in polygon
        for segment_start, segment_end in zip(other, other[1:] + other[:1])
    )


def _point_segment_distance(
    point: tuple[float, float], start: tuple[float, float], end: tuple[float, float]
) -> float:
    vector = (end[0] - start[0], end[1] - start[1])
    denominator = vector[0] ** 2 + vector[1] ** 2
    if denominator <= 1e-12:
        return math.dist(point, start)
    ratio = ((point[0] - start[0]) * vector[0] + (point[1] - start[1]) * vector[1]) / denominator
    ratio = min(1.0, max(0.0, ratio))
    projection = (start[0] + ratio * vector[0], start[1] + ratio * vector[1])
    return math.dist(point, projection)


def _target(table: TableState, point: tuple[float, float], rotation: float, facing: tuple[float, float]) -> TableTarget:
    return TableTarget(
        table_id=table.table_id,
        target_x=point[0],
        target_y=point[1],
        source_rot_deg=table.rot_deg,
        target_rot_deg=_normalize_angle(rotation),
        facing_target_x=point[0] + facing[0] * 100.0,
        facing_target_y=point[1] + facing[1] * 100.0,
    )


def _outward_facing(point: tuple[float, float], center: tuple[float, float]) -> tuple[float, float]:
    return _unit((point[0] - center[0], point[1] - center[1]), (0.0, -1.0))


def _axial_mean_rotation(*angles_deg: float) -> float:
    """Return a table-orientation mean where 0° and 180° are equivalent."""
    sine = sum(math.sin(math.radians(angle * 2.0)) for angle in angles_deg)
    cosine = sum(math.cos(math.radians(angle * 2.0)) for angle in angles_deg)
    if math.hypot(sine, cosine) <= 1e-9:
        return _normalize_angle(angles_deg[0])
    return _normalize_angle(math.degrees(math.atan2(sine, cosine)) * 0.5)


def _axial_angular_distance(first: float, second: float) -> float:
    """Measure physical table-orientation difference modulo 180°."""
    return abs(_normalize_angle((second - first) * 2.0)) * 0.5


def _rotation_to_short_axis(rotation_deg: float) -> tuple[float, float]:
    radians = math.radians(rotation_deg)
    return (-math.sin(radians), math.cos(radians))


def _normal_to_rotation(normal: tuple[float, float]) -> float:
    return _normalize_angle(math.degrees(math.atan2(normal[1], normal[0])) - 90.0)


def _unit(vector: tuple[float, float], fallback: tuple[float, float]) -> tuple[float, float]:
    length = math.hypot(*vector)
    if length <= 1e-9:
        return fallback
    return vector[0] / length, vector[1] / length


def _normalize_angle(angle: float) -> float:
    return (angle + 180.0) % 360.0 - 180.0


def _angular_distance(first: float, second: float) -> float:
    return abs(_normalize_angle(second - first))


def _segments_cross(
    first: tuple[tuple[float, float], tuple[float, float]],
    second: tuple[tuple[float, float], tuple[float, float]],
) -> bool:
    (ax, ay), (bx, by) = first
    (cx, cy), (dx, dy) = second

    def orientation(px: float, py: float, qx: float, qy: float, rx: float, ry: float) -> float:
        return (qx - px) * (ry - py) - (qy - py) * (rx - px)

    first_a = orientation(ax, ay, bx, by, cx, cy)
    first_b = orientation(ax, ay, bx, by, dx, dy)
    second_a = orientation(cx, cy, dx, dy, ax, ay)
    second_b = orientation(cx, cy, dx, dy, bx, by)
    return first_a * first_b < -1e-9 and second_a * second_b < -1e-9


def _spatial_key(table: TableState) -> tuple[float, float, float, float, float]:
    return (round(table.x, 8), round(table.y, 8), round(table.rot_deg, 8), round(table.width, 8), round(table.height, 8))


def _partition_geometry_key(partition: tuple[tuple[TableState, ...], ...]) -> tuple:
    return tuple(tuple(_spatial_key(table) for table in group) for group in partition)


def _deduplicate_options(options: list[_GroupOption]) -> list[_GroupOption]:
    seen: set[tuple] = set()
    unique: list[_GroupOption] = []
    for option in options:
        key = tuple(
            (target.table_id, round(target.target_x, 7), round(target.target_y, 7), round(target.target_rot_deg, 7))
            for target in option.targets
        )
        if key not in seen:
            seen.add(key)
            unique.append(option)
    return unique
