from __future__ import annotations

import math
from statistics import mean, median, pstdev
from typing import Iterable

from aisi.core.models import ROI, SceneFeatures, SceneState, TableState


# Rule thresholds are intentionally simple and centralized for easier tuning.
GROUPED_MIN_CLUSTERS = 2.0
GROUPED_MIN_COMPACTNESS = 0.52
LOW_CLUSTER_MAX = 1.5
FRONTAL_MIN_ALIGNMENT = 0.78
FIELD_MIN_CENTRALITY = 0.66
UNORDERED_MIN_SIGNAL = 0.22


def interpret_scene(scene_state: SceneState) -> SceneFeatures:
    """Compute robust scene features from simple geometric table heuristics."""
    tables = scene_state.tables

    cluster_count = compute_cluster_count(tables)
    cluster_compactness = compute_cluster_compactness(tables)
    distribution_evenness = compute_distribution_evenness(tables, scene_state.roi)
    frontal_alignment = compute_frontal_alignment(tables)
    shared_field_centrality = compute_shared_field_centrality(tables)
    local_vs_global_focus = compute_local_vs_global_focus(
        cluster_count=cluster_count,
        cluster_compactness=cluster_compactness,
        frontal_alignment=frontal_alignment,
        shared_field_centrality=shared_field_centrality,
    )
    scene_type = classify_scene_type(
        cluster_count=cluster_count,
        cluster_compactness=cluster_compactness,
        frontal_alignment=frontal_alignment,
        shared_field_centrality=shared_field_centrality,
    )

    return SceneFeatures(
        cluster_count=cluster_count,
        cluster_compactness=cluster_compactness,
        distribution_evenness=distribution_evenness,
        frontal_alignment=frontal_alignment,
        shared_field_centrality=shared_field_centrality,
        local_vs_global_focus=local_vs_global_focus,
        scene_type=scene_type,
    )


def compute_cluster_count(tables: list[TableState]) -> float:
    """Count connected table components using a size-relative distance threshold.

    Two tables are considered neighbors if their center distance is below a threshold
    derived from table size. This avoids brittle hardcoded pixel constants.
    """
    if not tables:
        return 0.0

    clusters = _compute_clusters(tables, _cluster_distance_threshold(tables))
    return float(len(clusters))


def compute_cluster_compactness(tables: list[TableState]) -> float:
    """Compute compactness from mean distance to cluster centroid for multi-table clusters.

    For each cluster with at least two tables:
    1) compute cluster centroid
    2) compute mean radius to that centroid
    3) normalize by representative table size
    4) invert to score in [0, 1]
    """
    if len(tables) < 2:
        return 0.0

    threshold = _cluster_distance_threshold(tables)
    cluster_indices = _compute_clusters(tables, threshold)

    multi_clusters = [indices for indices in cluster_indices if len(indices) >= 2]
    if not multi_clusters:
        return 0.0

    weighted_score_sum = 0.0
    total_weight = 0.0
    for indices in multi_clusters:
        cluster_tables = [tables[index] for index in indices]
        cx = mean(table.x for table in cluster_tables)
        cy = mean(table.y for table in cluster_tables)
        mean_radius = mean(_distance(table.x, table.y, cx, cy) for table in cluster_tables)

        # Cluster spread is normalized by local table size for interpretability.
        table_ref = max(1.0, _mean_table_diagonal(cluster_tables) * 0.70)
        normalized_spread = _clamp01(mean_radius / table_ref)
        compactness = 1.0 - normalized_spread

        weight = float(len(cluster_tables))
        weighted_score_sum += compactness * weight
        total_weight += weight

    return weighted_score_sum / max(1.0, total_weight)


def compute_distribution_evenness(tables: list[TableState], roi: ROI) -> float:
    """Compute 3x3-grid distribution evenness in [0, 1].

    The score is 1.0 when table counts are balanced across cells and approaches 0.0
    for strong concentration in a few cells.
    """
    if not tables:
        return 0.0

    grid_w = max(1.0, roi.width / 3.0)
    grid_h = max(1.0, roi.height / 3.0)
    counts = [0] * 9

    for table in tables:
        col = int((table.x - roi.x_min) / grid_w)
        row = int((table.y - roi.y_min) / grid_h)
        col = min(2, max(0, col))
        row = min(2, max(0, row))
        counts[row * 3 + col] += 1

    expected = len(tables) / 9.0
    deviation = sum(abs(count - expected) for count in counts)

    # Maximum L1 deviation for this setup occurs when all tables are in one cell.
    max_deviation = (16.0 / 9.0) * len(tables)
    if max_deviation <= 0.0:
        return 0.0

    return _clamp01(1.0 - (deviation / max_deviation))


def compute_frontal_alignment(tables: list[TableState]) -> float:
    """Measure orientation alignment on axis logic (0 deg ~ 180 deg).

    We use a doubled-angle circular mean. Doubling turns 180-degree periodicity into
    full-circle periodicity, so opposite headings collapse to the same axis.
    """
    if not tables:
        return 0.0

    doubled_radians = [math.radians(2.0 * normalize_rotation_deg(table.rot_deg)) for table in tables]
    mean_cos = mean(math.cos(value) for value in doubled_radians)
    mean_sin = mean(math.sin(value) for value in doubled_radians)
    resultant = math.hypot(mean_cos, mean_sin)

    return _clamp01(resultant)


def compute_shared_field_centrality(tables: list[TableState]) -> float:
    """Estimate whether tables form a shared field around a common center.

    Score combines:
    1) radius similarity around global centroid
    2) broad and even angular spread around that centroid
    """
    if len(tables) < 3:
        return 0.0

    cx = mean(table.x for table in tables)
    cy = mean(table.y for table in tables)

    radii = [_distance(table.x, table.y, cx, cy) for table in tables]
    mean_radius = mean(radii)
    if mean_radius <= 1e-6:
        return 0.0

    radius_cv = pstdev(radii) / max(mean_radius, 1e-6)
    radius_score = 1.0 - _clamp01(radius_cv / 0.80)

    angles = [math.atan2(table.y - cy, table.x - cx) for table in tables if _distance(table.x, table.y, cx, cy) > 1e-6]
    if len(angles) < 3:
        return 0.0

    mean_cos = mean(math.cos(angle) for angle in angles)
    mean_sin = mean(math.sin(angle) for angle in angles)
    angular_dispersion = 1.0 - math.hypot(mean_cos, mean_sin)

    bins = [0] * 8
    for angle in angles:
        normalized = (angle + math.pi) / (2.0 * math.pi)
        index = int(normalized * 8.0) % 8
        bins[index] += 1
    coverage_score = sum(1 for value in bins if value > 0) / 8.0

    gap_evenness = _angular_gap_evenness(angles)
    angle_score = 0.40 * angular_dispersion + 0.20 * coverage_score + 0.40 * gap_evenness

    return _clamp01(0.55 * radius_score + 0.45 * angle_score)


def compute_local_vs_global_focus(
    cluster_count: float,
    cluster_compactness: float,
    frontal_alignment: float,
    shared_field_centrality: float,
) -> float:
    """Derive local-vs-global focus from already computed signals.

    Interpretation:
    - 1.0: local (many compact clusters)
    - 0.0: global (few clusters + strong frontal/field signals)
    """
    cluster_signal = _clamp01((cluster_count - 1.0) / 2.0)
    local_signal = 0.65 * cluster_signal + 0.35 * cluster_compactness
    global_signal = max(frontal_alignment, shared_field_centrality)

    return _clamp01(0.50 + 0.50 * (local_signal - global_signal))


def classify_scene_type(
    cluster_count: float,
    cluster_compactness: float,
    frontal_alignment: float,
    shared_field_centrality: float,
) -> str:
    """Classify scene type with simple transparent threshold rules."""
    if cluster_count >= GROUPED_MIN_CLUSTERS and cluster_compactness >= GROUPED_MIN_COMPACTNESS:
        return "grouped"

    if frontal_alignment >= FRONTAL_MIN_ALIGNMENT and cluster_count <= LOW_CLUSTER_MAX:
        return "frontal"

    if shared_field_centrality >= FIELD_MIN_CENTRALITY and cluster_count <= LOW_CLUSTER_MAX:
        return "field_like"

    mixed_signal = max(cluster_compactness, frontal_alignment, shared_field_centrality)
    if mixed_signal < UNORDERED_MIN_SIGNAL:
        return "unordered"

    return "mixed"


def scene_features_to_debug_dict(scene_features: SceneFeatures) -> dict[str, float | str]:
    """Return a compact, stable, human-readable debug representation."""
    return {
        "scene_type": scene_features.scene_type,
        "cluster_count": round(scene_features.cluster_count, 3),
        "cluster_compactness": round(scene_features.cluster_compactness, 3),
        "distribution_evenness": round(scene_features.distribution_evenness, 3),
        "frontal_alignment": round(scene_features.frontal_alignment, 3),
        "shared_field_centrality": round(scene_features.shared_field_centrality, 3),
        "local_vs_global_focus": round(scene_features.local_vs_global_focus, 3),
    }


def summarize_scene_features(scene_features: SceneFeatures) -> str:
    """Format scene features as one concise debug line."""
    debug = scene_features_to_debug_dict(scene_features)
    return (
        f"scene_type={debug['scene_type']} | "
        f"clusters={debug['cluster_count']} | "
        f"compact={debug['cluster_compactness']} | "
        f"evenness={debug['distribution_evenness']} | "
        f"frontal={debug['frontal_alignment']} | "
        f"field={debug['shared_field_centrality']} | "
        f"local={debug['local_vs_global_focus']}"
    )


def _cluster_distance_threshold(tables: list[TableState]) -> float:
    """Distance threshold for neighbor linking based on typical table diagonal.

    Multiplier 1.25 allows tables that are near each other with modest gaps to connect,
    while separated groups usually remain disconnected.
    """
    typical_diagonal = median(_table_diagonal(table) for table in tables)
    return max(1.0, 1.25 * typical_diagonal)


def _compute_clusters(tables: list[TableState], threshold: float) -> list[list[int]]:
    """Return connected components over table-center proximity graph."""
    adjacency = [set() for _ in tables]
    for i in range(len(tables)):
        for j in range(i + 1, len(tables)):
            if _distance(tables[i].x, tables[i].y, tables[j].x, tables[j].y) <= threshold:
                adjacency[i].add(j)
                adjacency[j].add(i)

    visited = [False] * len(tables)
    components: list[list[int]] = []

    for root_index in range(len(tables)):
        if visited[root_index]:
            continue

        stack = [root_index]
        visited[root_index] = True
        component: list[int] = []
        while stack:
            current = stack.pop()
            component.append(current)
            for neighbor in adjacency[current]:
                if not visited[neighbor]:
                    visited[neighbor] = True
                    stack.append(neighbor)

        components.append(component)

    return components


def _angular_gap_evenness(angles: Iterable[float]) -> float:
    """Score evenness of angular gaps; 1.0 means near-uniform spacing."""
    sorted_angles = sorted((angle + 2.0 * math.pi) % (2.0 * math.pi) for angle in angles)
    if len(sorted_angles) < 3:
        return 0.0

    gaps: list[float] = []
    for index, value in enumerate(sorted_angles):
        nxt = sorted_angles[(index + 1) % len(sorted_angles)]
        if index == len(sorted_angles) - 1:
            nxt += 2.0 * math.pi
        gaps.append(nxt - value)

    ideal_gap = (2.0 * math.pi) / len(sorted_angles)
    normalized_gap_std = pstdev(gaps) / max(ideal_gap, 1e-6)
    return 1.0 - _clamp01(normalized_gap_std)


def _table_diagonal(table: TableState) -> float:
    return math.hypot(max(1.0, table.width), max(1.0, table.height))


def _mean_table_diagonal(tables: list[TableState]) -> float:
    return mean(_table_diagonal(table) for table in tables)


def normalize_rotation_deg(value: float) -> float:
    return ((value + 180.0) % 360.0) - 180.0


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))

def _distance(x1: float, y1: float, x2: float, y2: float) -> float:
    return math.hypot(x2 - x1, y2 - y1)
