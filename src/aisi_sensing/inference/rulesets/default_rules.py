from __future__ import annotations

from typing import Dict, Tuple, List
from ...core.types import FrameEvent
from ...features.proxemics import people_clusters, cluster_centroids, relations_to_objects, circle_variance, row_alignment_score
from typing import Tuple as _Tuple
import statistics

def _group_along_axis(points, axis: str, tol: float):
    if not points:
        return []
    vals = sorted(p[0] if axis == 'x' else p[1] for p in points)
    groups = []
    cur = [vals[0]]
    for v in vals[1:]:
        if abs(v - cur[-1]) <= tol:
            cur.append(v)
        else:
            groups.append((sum(cur)/len(cur), len(cur)))
            cur = [v]
    groups.append((sum(cur)/len(cur), len(cur)))
    groups.sort(key=lambda t: t[0])
    return groups

def _even_spacing(centers, tol: float) -> bool:
    if len(centers) < 3:
        return True
    deltas = [centers[i+1] - centers[i] for i in range(len(centers)-1)]
    mean_d = sum(deltas)/len(deltas)
    return all(abs(d - mean_d) <= tol for d in deltas)


def infer_layout(frame: FrameEvent, cfg: Dict) -> Tuple[str, float, Dict]:
    """Heuristic layout classification with candidate transparency.

    Returns (label, score, debug) where debug contains rule and candidates.
    """
    feats = cfg.get("features", {})
    tables = [(f.pose.x, f.pose.y) for f in frame.furniture if f.kind == "table"]
    chairs = [(f.pose.x, f.pose.y) for f in frame.furniture if f.kind == "chair"]
    screens = [(f.pose.x, f.pose.y) for f in frame.furniture if f.kind == "screen"]

    chair_circle_var = circle_variance(chairs if len(chairs) >= 6 else tables)
    row_score = row_alignment_score(chairs if chairs else tables)
    base_debug = {
        "n_tables": len(tables),
        "n_chairs": len(chairs),
        "n_screens": len(screens),
        "chair_circle_var": chair_circle_var,
        "row_score": row_score,
    }
    candidates: List[Dict] = []

    # Circle: variance of radii small and enough furniture/people
    circ_ok = (len(chairs) + len(tables)) >= int(feats.get("circle_min_points", 8)) and chair_circle_var <= float(feats.get("circle_variance_threshold_m2", 0.15))
    circ_score = max(0.0, min(0.95, 0.95 - (chair_circle_var / max(1e-6, float(feats.get("circle_variance_threshold_m2", 0.15)))) * 0.5)) if circ_ok else 0.0
    candidates.append({"label": "circle", "score": float(circ_score), "metrics": {"var": chair_circle_var}})
    if circ_ok:
        chosen = ("circle", circ_score, {**base_debug, "rule": "circle_var", "candidates": candidates})
        return chosen

    # Group islands (prioritized before rows): cluster tables into 2–4 valid clusters with separation
    islands_score = 0.0
    islands_dbg: Dict = {}
    if len(tables) >= 4:
        from ...features.clustering import cluster_entities_xy
        import math
        pxy = [(p.pose.x, p.pose.y) for p in frame.people]
        thresh = float(feats.get("islands_table_cluster_distance_m", feats.get("clustering_distance_m", 1.0)))
        clusters = cluster_entities_xy(tables, thresh)
        # Validate clusters: size>=min_size or (size==1 and >=2 people near)
        min_size = int(feats.get("islands_min_cluster_size", 2))
        near_thresh = float(feats.get("person_object_near_m", 1.2))
        valid = []
        for c in clusters:
            if len(c) >= min_size:
                valid.append(c)
            elif len(c) == 1 and pxy:
                ti = c[0]
                tx, ty = tables[ti]
                near = sum(1 for (x, y) in pxy if math.hypot(x - tx, y - ty) <= near_thresh)
                if near >= 2:
                    valid.append(c)
        cents = cluster_centroids(tables, valid) if valid else []
        num_clusters = len(valid)
        # Centroid separations
        dists = []
        for i in range(len(cents)):
            for j in range(i+1, len(cents)):
                dists.append(math.hypot(cents[i][0]-cents[j][0], cents[i][1]-cents[j][1]))
        avg_sep = sum(dists)/len(dists) if dists else 0.0
        min_sep = min(dists) if dists else 0.0
        min_req = float(feats.get("islands_min_separation_m", 1.2))
        avg_req = float(feats.get("islands_avg_separation_m", 1.4))
        size_ok = 2 <= num_clusters <= 4
        sep_ok = (min_sep >= min_req) and (avg_sep >= avg_req)
        if size_ok and sep_ok and valid:
            # Islands score combines cluster count, separation, and size validity
            count_score = min(1.0, (num_clusters - 1) / 3.0)
            sep_score = min(1.0, (min(min_sep / max(min_req,1e-6), avg_sep / max(avg_req,1e-6))))
            size_score = min(1.0, sum(len(c) for c in valid) / max(1, len(tables)))
            islands_score = 0.4 * count_score + 0.35 * sep_score + 0.25 * size_score
            islands_dbg = {"rule": "table_clusters", "num_clusters": num_clusters, "cluster_sizes": [len(c) for c in valid], "avg_centroid_dist": avg_sep, "min_centroid_dist": min_sep, "islands_score": islands_score}
    candidates.append({"label": "group_islands", "score": float(islands_score), "metrics": islands_dbg})
    if islands_score > 0.0:
        return "group_islands", islands_score, {**base_debug, **islands_dbg, "candidates": candidates}

    # Seminar rows: banding along one axis with even spacing; guard against false positives
    tol = float(feats.get("row_alignment_tolerance_m", 0.25))
    pts = chairs if chairs else tables
    axis_groups_y = _group_along_axis(pts, 'y', tol)
    # Only consider bands with at least 2 points; need >=3 bands and >= rows_min_tables overall
    min_tables = int(feats.get("rows_min_tables", 4))
    y_bands = [(c, n) for c, n in axis_groups_y if n >= 2]
    y_centers = [c for c, n in y_bands]
    total_in_bands = sum(n for _, n in y_bands)
    row_strength = total_in_bands / max(1, len(pts))
    rows_min_strength = float(feats.get("rows_min_strength", 0.65))
    rows_score = 0.0
    if 3 <= len(y_centers) <= 5 and _even_spacing(y_centers, tol * 1.2) and len(tables) >= min_tables and row_strength >= rows_min_strength:
        rows_score = min(0.85, 0.6 + 0.4 * (row_strength - rows_min_strength) / max(1e-6, (1.0 - rows_min_strength)))
        candidates.append({"label": "seminar_rows", "score": float(rows_score), "metrics": {"rows": y_centers, "row_strength": row_strength}})
        return "seminar_rows", rows_score, {**base_debug, "rows": y_centers, "row_strength": row_strength, "rule": "row_bands", "candidates": candidates}
    else:
        candidates.append({"label": "seminar_rows", "score": float(rows_score), "metrics": {"rows": y_centers, "row_strength": row_strength}})

    # Presentation front: using lab bounds front margin heuristic
    b = frame.world.get("bounds") if isinstance(frame.world, dict) else None
    if b and chairs:
        min_x, min_y, max_x, max_y = b
        front_margin = float(feats.get("front_margin_m", 0.6))
        front_y = max_y - front_margin
        frac_front = sum(1 for _, y in chairs if y >= front_y) / max(1, len(chairs))
        ppl = [(p.pose.x, p.pose.y) for p in frame.people]
        frac_ppl_front = sum(1 for _, y in ppl if y >= front_y) / max(1, len(ppl)) if ppl else 0.0
        pres_score = 0.0
        if frac_front <= 0.25 and frac_ppl_front <= 0.2:
            pres_score = 0.7
            candidates.append({"label": "presentation_front", "score": float(pres_score), "metrics": {"frac_front": frac_front}})
            return "presentation_front", pres_score, {**base_debug, "rule": "front_margin", "frac_front": frac_front, "candidates": candidates}
        candidates.append({"label": "presentation_front", "score": float(pres_score), "metrics": {"frac_front": frac_front}})

    # Default unknown
    return "unknown", 0.1, {**base_debug, "rule": "none", "candidates": candidates}


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
