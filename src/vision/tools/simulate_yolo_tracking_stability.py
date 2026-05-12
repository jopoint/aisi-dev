"""Lightweight synthetic simulation for YOLO ID stability (TTL + reacquire).

Run:
  python -m src.vision.tools.simulate_yolo_tracking_stability
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple
import math


@dataclass
class Track:
    id: str
    bbox: List[int]
    score: float
    miss_count: int = 0
    age: int = 1


def bbox_iou(a: List[int], b: List[int]) -> float:
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    iw, ih = max(0, ix2 - ix1), max(0, iy2 - iy1)
    inter = float(iw * ih)
    if inter <= 0:
        return 0.0
    area_a = float(max(0, ax2 - ax1) * max(0, ay2 - ay1))
    area_b = float(max(0, bx2 - bx1) * max(0, by2 - by1))
    union = area_a + area_b - inter
    return inter / union if union > 0 else 0.0


def center(b: List[int]) -> Tuple[float, float]:
    x1, y1, x2, y2 = b
    return ((x1 + x2) * 0.5, (y1 + y2) * 0.5)


def center_dist(c1: Tuple[float, float], c2: Tuple[float, float]) -> float:
    return float(math.hypot(c1[0] - c2[0], c1[1] - c2[1]))


def greedy_match(
    tracks: Dict[str, Track],
    track_ids: List[str],
    detections: List[dict],
    available_det_idxs: set,
    reacquire_max_dist: float,
    reacquire_min_iou: float,
) -> Dict[str, int]:
    candidates = []
    max_dist = max(1e-6, float(reacquire_max_dist))

    for tid in track_ids:
        t = tracks[tid]
        tc = center(t.bbox)
        for didx in list(available_det_idxs):
            db = detections[didx]["bbox_px"]
            iou = bbox_iou(t.bbox, db)
            if iou < reacquire_min_iou:
                continue
            dist = center_dist(tc, center(db))
            if dist > max_dist:
                continue
            score = 0.7 * iou + 0.3 * (1.0 - min(1.0, dist / max_dist))
            candidates.append((score, iou, -dist, tid, didx))

    candidates.sort(key=lambda x: (x[0], x[1], x[2]), reverse=True)
    matches: Dict[str, int] = {}
    used_t = set()
    used_d = set()
    for _, _, _, tid, didx in candidates:
        if tid in used_t or didx in used_d:
            continue
        matches[tid] = didx
        used_t.add(tid)
        used_d.add(didx)
    return matches


def main() -> None:
    track_ttl_frames = 3
    conf_create = 0.30
    conf_keep = 0.15
    reacquire_max_age = 3
    reacquire_max_dist = 120.0
    reacquire_min_iou = 0.05

    frames = [
        [{"bbox_px": [100, 100, 180, 180], "score": 0.95}],
        [{"bbox_px": [105, 102, 185, 182], "score": 0.86}],
        [],  # short occlusion
        [],  # short occlusion
        [{"bbox_px": [112, 108, 192, 188], "score": 0.41}],  # should reacquire same id
        [{"bbox_px": [340, 260, 420, 340], "score": 0.32}],  # far away -> new id
    ]

    tracks: Dict[str, Track] = {}
    next_id = 0

    for frame_id, dets_raw in enumerate(frames):
        detections = [d for d in dets_raw if float(d["score"]) >= conf_keep]
        available = set(range(len(detections)))

        active_ids = [tid for tid, t in tracks.items() if t.miss_count == 0]
        ghost_ids = [tid for tid, t in tracks.items() if 0 < t.miss_count <= reacquire_max_age]

        matches = greedy_match(tracks, active_ids, detections, available, reacquire_max_dist, reacquire_min_iou)
        for _, didx in matches.items():
            available.discard(didx)
        reacq = greedy_match(tracks, ghost_ids, detections, available, reacquire_max_dist, reacquire_min_iou)
        for _, didx in reacq.items():
            available.discard(didx)
        matches.update(reacq)

        matched_ids = set(matches.keys())
        for tid, didx in matches.items():
            d = detections[didx]
            tracks[tid].bbox = d["bbox_px"]
            tracks[tid].score = float(d["score"])
            tracks[tid].miss_count = 0
            tracks[tid].age += 1

        to_delete = []
        for tid, t in tracks.items():
            if tid in matched_ids:
                continue
            t.miss_count += 1
            t.age += 1
            if t.miss_count > track_ttl_frames:
                to_delete.append(tid)
        for tid in to_delete:
            del tracks[tid]

        for didx in sorted(list(available)):
            d = detections[didx]
            if float(d["score"]) < conf_create:
                continue
            tid = f"person_{next_id:02d}"
            next_id += 1
            tracks[tid] = Track(id=tid, bbox=d["bbox_px"], score=float(d["score"]))

        ids_sorted = sorted(tracks.keys())
        ghosts = [tid for tid in ids_sorted if tracks[tid].miss_count > 0]
        print(f"frame={frame_id} ids={ids_sorted} ghosts={ghosts} matches={matches}")


if __name__ == "__main__":
    main()
