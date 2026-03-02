from __future__ import annotations

from typing import Dict, Tuple, List
from ...core.types import FrameEvent
from ...features.proxemics import people_clusters, cluster_centroids, relations_to_objects, circle_variance, row_alignment_score


def infer_layout(frame: FrameEvent, cfg: Dict) -> Tuple[str, float, Dict]:
    """Heuristic layout classification.

    Returns (label, score, debug).
    """
    feats = cfg.get("features", {})
    tables = [(f.pose.x, f.pose.y) for f in frame.furniture if f.kind == "table"]
    chairs = [(f.pose.x, f.pose.y) for f in frame.furniture if f.kind == "chair"]
    screens = [(f.pose.x, f.pose.y) for f in frame.furniture if f.kind == "screen"]

    chair_circle_var = circle_variance(chairs)
    row_score = row_alignment_score(chairs)
    debug = {
        "n_tables": len(tables),
        "n_chairs": len(chairs),
        "n_screens": len(screens),
        "chair_circle_var": chair_circle_var,
        "row_score": row_score,
    }

    # Circle if many chairs with low variance of radii
    if len(chairs) >= 6 and chair_circle_var <= float(feats.get("circle_variance_threshold_m2", 0.2)):
        return "circle", 0.8, debug

    # Seminar rows if rows-aligned (low variance in either axis) and enough chairs
    if len(chairs) >= 4 and row_score <= float(feats.get("row_alignment_tolerance_m", 0.25)):
        return "seminar_rows", 0.7, debug

    # Presentation front if a screen exists and most chairs are on one side of it
    if screens and chairs:
        sx, sy = screens[0]
        left = sum(1 for x, _ in chairs if x < sx)
        right = len(chairs) - left
        if max(left, right) >= int(0.7 * len(chairs)):
            return "presentation_front", 0.75, debug

    # Group islands if chairs cluster around multiple tables
    if len(tables) >= 2 and len(chairs) >= 4:
        return "group_islands", 0.6, debug

    return "unknown", 0.1, debug


def infer_social(frame: FrameEvent, cfg: Dict) -> Tuple[str, float, Dict]:
    """Heuristic social constellation classification.

    Returns (label, score, debug).
    """
    feats = cfg.get("features", {})
    pxy = [(p.pose.x, p.pose.y) for p in frame.people]
    n_people = len(pxy)
    clusters = people_clusters(frame, float(feats.get("clustering_distance_m", 1.0)))
    n_clusters = len([c for c in clusters if len(c) > 0])

    debug = {"n_people": n_people, "n_clusters": n_clusters}

    if n_people == 2:
        # One-to-one if close
        import math
        d = math.hypot(pxy[0][0] - pxy[1][0], pxy[0][1] - pxy[1][1])
        if d <= float(feats.get("clustering_distance_m", 1.0)):
            return "one_to_one", 0.85, {**debug, "pair_distance": d}

    if n_people >= 3 and n_clusters == 1:
        return "single_group", 0.8, debug
    if n_people >= 4 and n_clusters >= 2:
        return "multi_group", 0.75, debug

    # Plenary if many and spread but near screen/partition assumed as front
    objs = [(f.kind, (f.pose.x, f.pose.y)) for f in frame.furniture if f.kind in ("screen", "partition")]
    if n_people >= 6 and objs:
        near = relations_to_objects(pxy, objs, float(feats.get("person_object_near_m", 1.2)))
        if sum(near.values()) >= int(0.5 * n_people):
            return "plenary", 0.6, {**debug, "near_front_counts": near}

    # Observers if people are few and far from furniture
    if 1 <= n_people <= 3 and not objs:
        return "observers", 0.5, debug

    return "unknown", 0.1, debug
