from src.vision.tools.simulate_yolo_tracking_stability import Track, greedy_match


def test_track_ttl_and_reacquire_id_stability():
    track_ttl_frames = 3
    conf_create = 0.30
    conf_keep = 0.15
    reacquire_max_age = 3
    reacquire_max_dist = 120.0
    reacquire_min_iou = 0.05

    frames = [
        [{"bbox_px": [100, 100, 180, 180], "score": 0.95}],
        [{"bbox_px": [104, 102, 184, 182], "score": 0.86}],
        [],
        [],
        [{"bbox_px": [112, 108, 192, 188], "score": 0.41}],
    ]

    tracks = {}
    next_id = 0
    first_id = None

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

        for tid, t in list(tracks.items()):
            if tid in matched_ids:
                continue
            t.miss_count += 1
            t.age += 1
            if t.miss_count > track_ttl_frames:
                del tracks[tid]

        for didx in sorted(list(available)):
            d = detections[didx]
            if float(d["score"]) < conf_create:
                continue
            tid = f"person_{next_id:02d}"
            next_id += 1
            tracks[tid] = Track(id=tid, bbox=d["bbox_px"], score=float(d["score"]))
            if first_id is None:
                first_id = tid

        if frame_id in (2, 3):
            # During misses, the original track should still be alive as ghost.
            assert first_id in tracks
            assert tracks[first_id].miss_count > 0

    # Reappearance should reacquire the same ID instead of creating a new one.
    assert first_id in tracks
    assert tracks[first_id].miss_count == 0
    assert len(tracks) == 1
