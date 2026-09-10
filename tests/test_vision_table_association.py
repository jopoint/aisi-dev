"""Focused synthetic tests for the current-room Rect-table association core."""

from __future__ import annotations

import math
import unittest
from unittest.mock import patch

from src.vision.pipeline import VisionPipeline, update_table_obb_yaw


def _det(x1: int, y1: int, x2: int, y2: int) -> dict:
    return {"bbox_px": [x1, y1, x2, y2], "score": 0.9}


def _track(bbox: list[int], *, miss_count: int = 0) -> dict:
    return {"bbox": bbox, "miss_count": miss_count, "age": 1}


def _pipeline() -> VisionPipeline:
    pipeline = VisionPipeline.__new__(VisionPipeline)
    pipeline._class_match_dist_px = {"table": 150.0}
    pipeline._class_match_iou_min = {"table": 0.05}
    pipeline.reacquire_max_dist = 150.0
    pipeline.reacquire_min_iou = 0.05
    pipeline.table_new_confirm_frames = 2
    pipeline.table_new_fragment_area_ratio = 0.70
    pipeline.table_new_fragment_overlap_ratio = 0.60
    pipeline._pending_table_births = []
    return pipeline


class VisionTableAssociationTests(unittest.TestCase):
    def test_fresh_pipeline_initializes_pending_births_before_first_unmatched_table(self) -> None:
        # Avoid loading a vision model; this covers the real __init__ path that
        # previously omitted the pending-birth buffer.
        with patch("src.vision.pipeline.SAM3Segmenter"):
            pipeline = VisionPipeline(proposals_mode=None, device="cpu")
        self.assertEqual(pipeline._pending_table_births, [])
        self.assertFalse(pipeline._advance_pending_table_birth([100, 100, 300, 220], 0))
        self.assertEqual(len(pipeline._pending_table_births), 1)

    def test_one_stable_table_keeps_its_tracker_id(self) -> None:
        pipeline = _pipeline()
        matches = pipeline._greedy_track_match(
            [_det(102, 100, 202, 180)],
            {"table_00": _track([100, 100, 200, 180])}, ["table_00"], {0}, "table",
        )
        self.assertEqual(matches, {"table_00": 0})

    def test_multiple_stationary_tables_and_detection_order_changes_keep_ids(self) -> None:
        pipeline = _pipeline()
        tracks = {
            "table_00": _track([100, 100, 200, 180]),
            "table_01": _track([400, 100, 500, 180]),
        }
        # The detector order is reversed; association is geometric, not list-order based.
        matches = pipeline._greedy_track_match(
            [_det(401, 100, 501, 180), _det(99, 100, 199, 180)],
            tracks, list(tracks), {0, 1}, "table",
        )
        self.assertEqual(matches, {"table_01": 0, "table_00": 1})

    def test_two_tables_moving_near_each_other_match_by_overlap_before_center_distance(self) -> None:
        pipeline = _pipeline()
        tracks = {
            "table_00": _track([200, 100, 300, 180]),
            "table_01": _track([320, 100, 420, 180]),
        }
        matches = pipeline._greedy_track_match(
            [_det(210, 100, 310, 180), _det(310, 100, 410, 180)],
            tracks, list(tracks), {0, 1}, "table",
        )
        self.assertEqual(matches, {"table_00": 0, "table_01": 1})

    def test_temporary_missed_table_is_reacquired_with_its_existing_id(self) -> None:
        pipeline = _pipeline()
        ghost_tracks = {"table_00": _track([100, 100, 200, 180], miss_count=1)}
        matches = pipeline._greedy_track_match(
            [_det(105, 100, 205, 180)], ghost_tracks, ["table_00"], {0}, "table",
        )
        self.assertEqual(matches, {"table_00": 0})

    def test_four_stable_full_size_tables_confirm_to_exactly_four_births(self) -> None:
        pipeline = _pipeline()
        tables = [
            [100, 100, 300, 220], [400, 100, 600, 220],
            [100, 400, 300, 520], [400, 400, 600, 520],
        ]
        # The first observations are only pending and cannot affect association.
        self.assertEqual(
            [pipeline._advance_pending_table_birth(box, 0) for box in tables],
            [False, False, False, False],
        )
        self.assertEqual(
            [pipeline._advance_pending_table_birth(box, 1) for box in tables],
            [True, True, True, True],
        )
        self.assertEqual(pipeline._pending_table_births, [])

    def test_occlusion_fragments_do_not_receive_a_new_persistent_table_id(self) -> None:
        pipeline = _pipeline()
        full_table = [100, 100, 300, 260]
        # Two visible halves of one 200 x 160 px table are each 50% of its
        # area and fully covered by its established bbox.
        fragments = ([100, 100, 200, 260], [200, 100, 300, 260])
        self.assertTrue(all(
            pipeline._is_table_fragment_of_track(fragment, full_table)
            for fragment in fragments
        ))
        # Suppressed fragments never enter the pending-birth buffer and hence
        # never allocate table_04/table_05-style persistent IDs.
        self.assertEqual(pipeline._pending_table_births, [])

    def test_fragment_disappearing_leaves_original_track_available_for_continuity(self) -> None:
        pipeline = _pipeline()
        full_table = [100, 100, 300, 260]
        fragment = [100, 100, 200, 260]
        self.assertTrue(pipeline._is_table_fragment_of_track(fragment, full_table))
        matches = pipeline._greedy_track_match(
            [_det(*full_table)], {"table_00": _track(full_table, miss_count=1)},
            ["table_00"], {0}, "table",
        )
        self.assertEqual(matches, {"table_00": 0})

    def test_genuine_fifth_full_size_table_is_confirmed_after_two_frames(self) -> None:
        pipeline = _pipeline()
        existing_table = [100, 100, 300, 260]
        fifth_table = [500, 100, 700, 260]
        self.assertFalse(pipeline._is_table_fragment_of_track(fifth_table, existing_table))
        self.assertFalse(pipeline._advance_pending_table_birth(fifth_table, 10))
        self.assertTrue(pipeline._advance_pending_table_birth(fifth_table, 11))

    def test_table_zero_survives_a_temporary_occlusion_within_ttl(self) -> None:
        pipeline = _pipeline()
        returned = _det(104, 100, 204, 180)
        matches = pipeline._greedy_track_match(
            [returned], {"table_00": _track([100, 100, 200, 180], miss_count=3)},
            ["table_00"], {0}, "table",
        )
        self.assertEqual(matches, {"table_00": 0})

    def test_rect_obb_angle_flip_by_pi_preserves_the_same_axis(self) -> None:
        self.assertAlmostEqual(
            update_table_obb_yaw(math.radians(180.0), 0.0), 0.0, places=6
        )

    def test_reset_initializes_a_clean_tracker_session(self) -> None:
        pipeline = _pipeline()
        pipeline._tracks = {"chair": {}, "table": {"table_170": _track([1, 1, 2, 2])}, "person": {}}
        pipeline._next_id = {"chair": 4, "table": 171, "person": 2}
        pipeline._person_new_ids_since_log = 3
        pipeline._pending_table_births = [{"bbox": [1, 1, 2, 2], "last_seen_frame": 5, "confirm_count": 1}]
        pipeline.reset_tracks()
        self.assertEqual(pipeline._tracks, {"chair": {}, "table": {}, "person": {}})
        self.assertEqual(pipeline._next_id, {"chair": 0, "table": 0, "person": 0})
        self.assertEqual(pipeline._pending_table_births, [])

    def test_stale_tracks_cannot_associate_into_a_new_single_table_session(self) -> None:
        pipeline = _pipeline()
        pipeline._tracks = {"chair": {}, "table": {"table_170": _track([100, 100, 200, 180])}, "person": {}}
        pipeline._next_id = {"chair": 0, "table": 171, "person": 0}
        pipeline._person_new_ids_since_log = 0
        pipeline.reset_tracks()
        matches = pipeline._greedy_track_match(
            [_det(100, 100, 200, 180)], pipeline._tracks["table"], [], {0}, "table",
        )
        self.assertEqual(matches, {})


if __name__ == "__main__":
    unittest.main()
