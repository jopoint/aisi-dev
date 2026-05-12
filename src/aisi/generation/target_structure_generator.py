from __future__ import annotations

import math
from statistics import mean, median

from aisi.core.models import ClusterZone, Point2D, SceneFeatures, SceneState, TargetProfile, TargetStructure


def generate_target_structure(
    scene_state: SceneState,
    scene_features: SceneFeatures,
    target_profile: TargetProfile,
) -> TargetStructure:
    """Generate an adaptive target structure from the current scene geometry."""
    learning_format = scene_state.learning_format

    if learning_format == "input":
        front_direction, _row_axis = derive_input_front_direction(scene_state)
        row_layout = choose_input_row_layout(scene_state, front_direction)
        row_centers = derive_input_row_centers(scene_state, row_layout, front_direction)
        return TargetStructure(
            structure_type="frontal_rows",
            focus_direction=Point2D(*front_direction),
            front_direction=Point2D(*front_direction),
            row_centers=[Point2D(*center) for center in row_centers],
            row_layout=list(row_layout),
        )

    if learning_format == "groupwork":
        pair_count = max(1, math.ceil(len(scene_state.tables) / 2)) if scene_state.tables else 2
        zones = derive_group_cluster_zones_from_scene(scene_state, target_cluster_count=pair_count)
        return TargetStructure(structure_type="cluster_zones", cluster_zones=zones)

    shared_center = derive_shared_field_center_from_scene(scene_state)
    return TargetStructure(structure_type="shared_field", shared_field_center=shared_center)


def compute_table_centroid(tables: list) -> Point2D:
    """Compute centroid of table centers; caller must handle empty list."""
    return Point2D(
        x=mean(table.x for table in tables),
        y=mean(table.y for table in tables),
    )


def derive_focus_line_from_scene(scene_state: SceneState) -> tuple[tuple[float, float], tuple[float, float], tuple[float, float]]:
    """Derive an adaptive input focus line from table spread and dominant direction.

    The line models a shared front edge rather than a single point:
    - the line direction follows the dominant table spread axis
    - the line location is offset in front of the current table centroid
    - the result is clipped to a plausible in-ROI segment
    """
    roi = scene_state.roi
    if not scene_state.tables:
        center = (roi.center[0], roi.y_min + roi.height * 0.20)
        direction = (1.0, 0.0)
        line_half_length = roi.width * 0.28
        return direction, (center[0] - line_half_length, center[1]), (center[0] + line_half_length, center[1])

    centroid = compute_table_centroid(scene_state.tables)
    axis = _dominant_axis_unit(scene_state.tables, centroid)
    direction = _normalize_vector(axis)
    normal = (-direction[1], direction[0])

    # For readable frontal setups in image coordinates, we prefer the normal
    # that points roughly toward smaller y (upper scene direction).
    if normal[1] > 0.0:
        normal = (-normal[0], -normal[1])

    roi_min_dim = max(1.0, min(roi.width, roi.height))
    normal_spread = median(abs(_dot((table.x - centroid.x, table.y - centroid.y), normal)) for table in scene_state.tables)
    radial_spread = median(_distance((table.x, table.y), (centroid.x, centroid.y)) for table in scene_state.tables)

    offset = max(roi_min_dim * 0.14, normal_spread * 1.15, radial_spread * 0.55)
    offset = min(offset, roi_min_dim * 0.30)

    line_center = _clip_point_to_roi(
        (centroid.x + normal[0] * offset, centroid.y + normal[1] * offset),
        roi,
        margin=roi_min_dim * 0.08,
    )

    line_half_length = max(roi.width, roi.height) * 0.30
    start = _clip_point_to_roi(
        (line_center[0] - direction[0] * line_half_length, line_center[1] - direction[1] * line_half_length),
        roi,
        margin=roi_min_dim * 0.08,
    )
    end = _clip_point_to_roi(
        (line_center[0] + direction[0] * line_half_length, line_center[1] + direction[1] * line_half_length),
        roi,
        margin=roi_min_dim * 0.08,
    )
    return direction, start, end


def derive_input_front_direction(scene_state: SceneState) -> tuple[tuple[float, float], tuple[float, float]]:
    """Derive stable frontal input orientation.

    Returns:
    - front_direction: where table-facing should point
    - row_axis: lateral axis along each row
    """
    if not scene_state.tables:
        return (0.0, -1.0), (1.0, 0.0)

    centroid = compute_table_centroid(scene_state.tables)
    source_row_axis = _normalize_vector(_dominant_axis_unit(scene_state.tables, centroid))
    row_axis, _axis_note = _regularize_input_row_axis(source_row_axis, scene_state.tables)

    front_direction = _perpendicular(row_axis)
    if front_direction[1] > 0.0:
        front_direction = (-front_direction[0], -front_direction[1])

    return _normalize_vector(front_direction), _normalize_vector(row_axis)


def choose_input_row_layout(
    scene_state: SceneState,
    front_direction: tuple[float, float],
) -> list[int]:
    """Choose row layout for input by table count with simple depth heuristics."""
    table_count = len(scene_state.tables)
    candidates = _input_row_layout_candidates(table_count)
    if not scene_state.tables or len(candidates) == 1:
        return list(candidates[0])

    back_axis = (-front_direction[0], -front_direction[1])
    depth_values = sorted(
        _dot((table.x, table.y), back_axis)
        for table in scene_state.tables
    )

    best_layout = list(candidates[0])
    best_cost = math.inf
    for layout in candidates:
        candidate_cost = _score_input_row_layout_depths(depth_values, layout)
        if candidate_cost < best_cost:
            best_cost = candidate_cost
            best_layout = list(layout)

    return best_layout


def derive_input_row_centers(
    scene_state: SceneState,
    row_layout: list[int],
    front_direction: tuple[float, float],
) -> list[tuple[float, float]]:
    """Place row centers along the depth axis for a frontal classroom-like structure."""
    roi = scene_state.roi
    row_count = max(1, len(row_layout))
    if not scene_state.tables:
        base_center = roi.center
    else:
        centroid = compute_table_centroid(scene_state.tables)
        base_center = (centroid.x, centroid.y)

    back_axis = (-front_direction[0], -front_direction[1])
    row_spacing = _input_row_spacing(scene_state)
    roi_min = max(1.0, min(roi.width, roi.height))
    margin = max(roi_min * 0.10, row_spacing * 0.60)

    centers: list[tuple[float, float]] = []
    for row_index in range(row_count):
        depth_offset = (row_index - (row_count - 1) * 0.5) * row_spacing
        raw = (
            base_center[0] + back_axis[0] * depth_offset,
            base_center[1] + back_axis[1] * depth_offset,
        )
        centers.append(_clip_point_to_roi(raw, roi, margin=margin))

    return centers


def derive_group_cluster_zones_from_scene(
    scene_state: SceneState,
    target_cluster_count: int,
) -> list[ClusterZone]:
    """Derive group zones from existing spatial tendencies.

    Strategy:
    - explicitly build table pairs as primary groupwork islands
    - derive one zone center per pair/single island
    - keep singleton only when table count is odd
    """
    tables = scene_state.tables
    if not tables:
        return _fallback_grid_zones(scene_state, max(2, target_cluster_count))

    pair_groups = pair_tables_for_groupwork(tables)
    zones = [_build_zone_from_group(group, scene_state) for group in pair_groups]
    zones = _normalize_zone_count(zones, scene_state, max(1, min(target_cluster_count, len(pair_groups))))
    return zones


def pair_tables_for_groupwork(tables: list) -> list[list]:
    """Build explicit pair islands for groupwork.

    Pairing objective:
    - primary: spatial proximity
    - secondary: similar long-axis orientation
    - preserve already plausible 2-table islands
    """
    if not tables:
        return []

    ordered = sorted(tables, key=lambda table: table.table_id)
    if len(ordered) == 1:
        return [[ordered[0]]]

    full_mask = (1 << len(ordered)) - 1
    memo: dict[int, tuple[float, list[list[int]]]] = {}

    def solve(mask: int) -> tuple[float, list[list[int]]]:
        if mask == 0:
            return 0.0, []
        if mask in memo:
            return memo[mask]

        first_idx = _first_set_bit_index(mask)
        rest_mask = mask & ~(1 << first_idx)

        best_cost = math.inf
        best_groups: list[list[int]] = []

        if _bit_count(mask) % 2 == 1:
            singleton_cost = _groupwork_singleton_cost(ordered, first_idx, mask)
            remainder_cost, remainder_groups = solve(rest_mask)
            candidate_cost = singleton_cost + remainder_cost
            if candidate_cost < best_cost:
                best_cost = candidate_cost
                best_groups = [[first_idx], *remainder_groups]

        idx = first_idx + 1
        while idx < len(ordered):
            if mask & (1 << idx):
                pair_cost = _groupwork_pair_cost(ordered[first_idx], ordered[idx])
                remainder_cost, remainder_groups = solve(rest_mask & ~(1 << idx))
                candidate_cost = pair_cost + remainder_cost
                if candidate_cost < best_cost:
                    best_cost = candidate_cost
                    best_groups = [[first_idx, idx], *remainder_groups]
            idx += 1

        memo[mask] = (best_cost, best_groups)
        return memo[mask]

    _, best_index_groups = solve(full_mask)
    groups = [[ordered[idx] for idx in group] for group in best_index_groups]
    groups.sort(key=lambda group: min(table.table_id for table in group))
    return groups


def derive_shared_field_center_from_scene(scene_state: SceneState) -> Point2D:
    """Derive adaptive shared-field center from current table centroid.

    The center follows current geometry, with only a mild correction toward ROI
    center and clipping to keep it in a plausible in-bounds area.
    """
    roi = scene_state.roi
    if not scene_state.tables:
        return Point2D(*roi.center)

    centroid = compute_table_centroid(scene_state.tables)
    roi_center = Point2D(*roi.center)

    blended = (
        0.88 * centroid.x + 0.12 * roi_center.x,
        0.88 * centroid.y + 0.12 * roi_center.y,
    )
    clipped = _clip_point_to_roi(blended, roi, margin=max(1.0, min(roi.width, roi.height) * 0.08))
    return Point2D(*clipped)


def pair_tables_by_proximity(tables: list) -> list[list]:
    """Greedy nearest-neighbor pairing, with optional single remainder."""
    remaining = list(tables)
    pairs: list[list] = []

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

        first = remaining.pop(best_j)
        second = remaining.pop(best_i)
        pairs.append([second, first])

    if remaining:
        pairs.append([remaining[0]])

    return pairs


def _groupwork_pair_cost(table_a, table_b) -> float:
    mean_height = max(1.0, (max(1.0, table_a.height) + max(1.0, table_b.height)) * 0.5)
    distance = _distance((table_a.x, table_a.y), (table_b.x, table_b.y))
    preferred_distance = mean_height * 1.02

    distance_ratio = distance / preferred_distance
    distance_penalty = abs(distance_ratio - 1.0)
    if distance_ratio > 2.3:
        distance_penalty += (distance_ratio - 2.3) * 0.9

    orientation_delta = _angle_delta_mod180(table_a.rot_deg, table_b.rot_deg)
    orientation_penalty = orientation_delta / 70.0

    preserve_bonus = 0.0
    if 0.75 <= distance_ratio <= 1.45 and orientation_delta <= 18.0:
        preserve_bonus = 0.42
    elif 0.65 <= distance_ratio <= 1.65 and orientation_delta <= 32.0:
        preserve_bonus = 0.18

    return (distance_penalty * 0.80) + (orientation_penalty * 0.20) - preserve_bonus


def _groupwork_singleton_cost(tables: list, idx: int, mask: int) -> float:
    table = tables[idx]
    mean_diag = mean(math.hypot(max(1.0, item.width), max(1.0, item.height)) for item in tables)
    nearest = math.inf
    for other_idx, other in enumerate(tables):
        if other_idx == idx or not (mask & (1 << other_idx)):
            continue
        nearest = min(nearest, _distance((table.x, table.y), (other.x, other.y)))

    if not math.isfinite(nearest):
        return 1.2

    normalized_nearest = nearest / max(1.0, mean_diag)
    return 0.95 + _clamp(normalized_nearest * 0.35, 0.0, 1.1)


def _angle_delta_mod180(a_deg: float, b_deg: float) -> float:
    return abs(((a_deg - b_deg + 90.0) % 180.0) - 90.0)


def _first_set_bit_index(mask: int) -> int:
    idx = 0
    while mask:
        if mask & 1:
            return idx
        idx += 1
        mask >>= 1
    raise ValueError("mask must contain at least one bit")


def _bit_count(mask: int) -> int:
    return mask.bit_count()


def _dominant_axis_unit(tables: list, centroid: Point2D) -> tuple[float, float]:
    if len(tables) < 2:
        return (1.0, 0.0)

    sxx = mean((table.x - centroid.x) ** 2 for table in tables)
    syy = mean((table.y - centroid.y) ** 2 for table in tables)
    sxy = mean((table.x - centroid.x) * (table.y - centroid.y) for table in tables)

    if abs(sxy) < 1e-9 and abs(sxx - syy) < 1e-9:
        return (1.0, 0.0)

    theta = 0.5 * math.atan2(2.0 * sxy, sxx - syy)
    return (math.cos(theta), math.sin(theta))


def _regularize_input_row_axis(
    suggested_axis: tuple[float, float],
    tables: list,
) -> tuple[tuple[float, float], str]:
    """Favor clear frontal row axes over arbitrary diagonals for input format."""
    if len(tables) < 3:
        return _normalize_vector(suggested_axis), "input_axis_regularization=kept_small_set"

    centroid = compute_table_centroid(tables)
    source_axis = _normalize_vector(_dominant_axis_unit(tables, centroid))
    source_diag = _axis_diagonal_strength(source_axis)
    source_anisotropy = _axis_anisotropy(tables, centroid)

    diagonal_plausible = source_diag > 0.55 and source_anisotropy > 0.42
    if diagonal_plausible:
        return _normalize_vector(suggested_axis), "input_axis_regularization=kept"

    horizontal = (1.0, 0.0)
    vertical = (0.0, 1.0)
    horizontal_score = abs(_dot(suggested_axis, horizontal))
    vertical_score = abs(_dot(suggested_axis, vertical))
    snapped = horizontal if horizontal_score >= vertical_score else vertical
    if _dot(suggested_axis, snapped) < 0.0:
        snapped = (-snapped[0], -snapped[1])

    blended = _normalize_vector(
        (
            _lerp(suggested_axis[0], snapped[0], 0.68),
            _lerp(suggested_axis[1], snapped[1], 0.68),
        )
    )
    return blended, "input_axis_regularization=soft_snap"


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

    # Above 6 is out of scope for now, but keep deterministic fallback.
    twos = [2 for _ in range(table_count // 2)]
    if table_count % 2:
        twos.append(1)
    return [twos]


def _score_input_row_layout_depths(depth_values: list[float], layout: list[int]) -> float:
    if not layout or sum(layout) != len(depth_values):
        return math.inf

    start = 0
    spreads: list[float] = []
    centers: list[float] = []
    for size in layout:
        row_depths = depth_values[start : start + size]
        start += size
        spread = (max(row_depths) - min(row_depths)) if len(row_depths) >= 2 else 0.0
        spreads.append(spread)
        centers.append(mean(row_depths))

    compactness = mean(spreads) if spreads else 0.0
    separations = [abs(centers[idx + 1] - centers[idx]) for idx in range(len(centers) - 1)]
    separation_bonus = mean(separations) if separations else 0.0

    singleton_penalty = 0.22 * sum(1 for size in layout if size == 1)
    three_row_penalty = 0.07 * max(0, len(layout) - 2)
    three_table_penalty = 0.04 * sum(1 for size in layout if size == 3)
    two_row_reward = 0.03 * sum(1 for size in layout if size == 2)

    return (
        compactness * 0.08
        + singleton_penalty
        + three_row_penalty
        + three_table_penalty
        - two_row_reward
        - (separation_bonus * 0.002)
    )


def _input_row_spacing(scene_state: SceneState) -> float:
    if not scene_state.tables:
        return max(60.0, scene_state.roi.height * 0.16)

    median_height = median(max(1.0, table.height) for table in scene_state.tables)
    median_width = median(max(1.0, table.width) for table in scene_state.tables)
    roi_min = max(1.0, min(scene_state.roi.width, scene_state.roi.height))
    return max(median_height * 1.35, median_width * 0.95, roi_min * 0.16)


def _axis_anisotropy(tables: list, centroid: Point2D) -> float:
    if len(tables) < 2:
        return 0.0

    sxx = mean((table.x - centroid.x) ** 2 for table in tables)
    syy = mean((table.y - centroid.y) ** 2 for table in tables)
    trace = max(1e-9, sxx + syy)
    return _clamp(abs(sxx - syy) / trace, 0.0, 1.0)


def _axis_diagonal_strength(axis: tuple[float, float]) -> float:
    alignment = max(abs(axis[0]), abs(axis[1]))
    return _clamp((0.90 - alignment) / 0.20, 0.0, 1.0)


def _perpendicular(vector: tuple[float, float]) -> tuple[float, float]:
    return (-vector[1], vector[0])


def _normalize_vector(vector: tuple[float, float]) -> tuple[float, float]:
    length = math.hypot(vector[0], vector[1])
    if length <= 1e-9:
        return (1.0, 0.0)
    return (vector[0] / length, vector[1] / length)


def _proximity_threshold_from_tables(tables: list) -> float:
    diagonals = [math.hypot(max(1.0, table.width), max(1.0, table.height)) for table in tables]
    return max(1.0, 1.28 * median(diagonals))


def _connected_components_by_proximity(tables: list, threshold: float) -> list[list]:
    adjacency = [set() for _ in tables]
    for i in range(len(tables)):
        for j in range(i + 1, len(tables)):
            if _distance((tables[i].x, tables[i].y), (tables[j].x, tables[j].y)) <= threshold:
                adjacency[i].add(j)
                adjacency[j].add(i)

    visited = [False] * len(tables)
    components: list[list] = []
    for root in range(len(tables)):
        if visited[root]:
            continue

        stack = [root]
        visited[root] = True
        group: list = []
        while stack:
            current = stack.pop()
            group.append(tables[current])
            for neighbor in adjacency[current]:
                if not visited[neighbor]:
                    visited[neighbor] = True
                    stack.append(neighbor)

        components.append(group)

    return components


def _build_zone_from_group(group: list, scene_state: SceneState) -> ClusterZone:
    centroid = compute_table_centroid(group)
    roi = scene_state.roi
    roi_min = max(1.0, min(roi.width, roi.height))
    center = _clip_point_to_roi((centroid.x, centroid.y), roi, margin=roi_min * 0.05)

    mean_diag = mean(math.hypot(max(1.0, table.width), max(1.0, table.height)) for table in group)
    if len(group) == 1:
        radius = mean_diag * 0.72
    elif len(group) == 2:
        pair_sep = _distance((group[0].x, group[0].y), (group[1].x, group[1].y))
        mean_height = max(1.0, mean(max(1.0, table.height) for table in group))
        compact_sep = _lerp(pair_sep, mean_height * 1.02, 0.62)
        radius = (compact_sep * 0.62) + (mean_diag * 0.34)
    else:
        spread = mean(_distance((table.x, table.y), center) for table in group)
        radius = spread + mean_diag * 0.45

    radius = _clamp(radius, roi_min * 0.09, roi_min * 0.24)
    return ClusterZone(center=Point2D(*center), radius=radius)


def _normalize_zone_count(
    zones: list[ClusterZone],
    scene_state: SceneState,
    target_count: int,
) -> list[ClusterZone]:
    roi = scene_state.roi
    roi_min = max(1.0, min(roi.width, roi.height))
    normalized = list(zones)

    while len(normalized) > target_count:
        best_i = 0
        best_j = 1
        best_dist = math.inf
        for i in range(len(normalized)):
            for j in range(i + 1, len(normalized)):
                dist = _distance(
                    (normalized[i].center.x, normalized[i].center.y),
                    (normalized[j].center.x, normalized[j].center.y),
                )
                if dist < best_dist:
                    best_dist = dist
                    best_i = i
                    best_j = j

        zone_b = normalized.pop(best_j)
        zone_a = normalized.pop(best_i)
        merged_center = (
            (zone_a.center.x + zone_b.center.x) * 0.5,
            (zone_a.center.y + zone_b.center.y) * 0.5,
        )
        merged_center = _clip_point_to_roi(merged_center, roi, margin=roi_min * 0.05)
        merged_radius = max(zone_a.radius, zone_b.radius)
        normalized.append(
            ClusterZone(center=Point2D(*merged_center), radius=merged_radius)
        )

    while len(normalized) < target_count and scene_state.tables:
        if not normalized:
            table = scene_state.tables[0]
            center = _clip_point_to_roi((table.x, table.y), roi, margin=roi_min * 0.05)
            normalized.append(
                ClusterZone(center=Point2D(*center), radius=roi_min * 0.14)
            )
            continue

        # Add zone near the table farthest from all existing zones.
        farthest_table = max(
            scene_state.tables,
            key=lambda table: min(
                _distance((table.x, table.y), (zone.center.x, zone.center.y))
                for zone in normalized
            ),
        )
        center = _clip_point_to_roi((farthest_table.x, farthest_table.y), roi, margin=roi_min * 0.05)
        normalized.append(ClusterZone(center=Point2D(*center), radius=roi_min * 0.14))

    return normalized


def _fallback_grid_zones(scene_state: SceneState, cluster_count: int) -> list[ClusterZone]:
    """Fallback only when no tables are available."""
    roi = scene_state.roi
    zones: list[ClusterZone] = []
    cols = max(1, cluster_count)
    x_step = roi.width / (cols + 1)
    y = roi.center[1]

    for idx in range(cluster_count):
        center = Point2D(x=roi.x_min + (idx + 1) * x_step, y=y)
        zones.append(ClusterZone(center=center, radius=min(roi.width, roi.height) * 0.16))

    return zones


def _clip_point_to_roi(point: tuple[float, float], roi, margin: float) -> tuple[float, float]:
    x = _clamp(point[0], roi.x_min + margin, roi.x_max - margin)
    y = _clamp(point[1], roi.y_min + margin, roi.y_max - margin)
    return (x, y)


def _dot(a: tuple[float, float], b: tuple[float, float]) -> float:
    return a[0] * b[0] + a[1] * b[1]


def _distance(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def _lerp(start: float, end: float, t: float) -> float:
    return start + (end - start) * t
