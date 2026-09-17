"""Focused synthetic tests for the current-room Rect-table association core."""

from __future__ import annotations

import math
import unittest
from unittest.mock import patch

import numpy as np

from src.vision.calibration.tabletop import TabletopCalibration
from src.vision.pipeline import (
    RECT_TABLE_OBVIOUSLY_OVERSIZED_AREA_CM2,
    VisionPipeline,
    update_table_obb_yaw,
)


def _det(x1: int, y1: int, x2: int, y2: int) -> dict:
    return {"bbox_px": [x1, y1, x2, y2], "score": 0.9}


def _obb_det(bbox: list[int], long_side: float, short_side: float) -> dict:
    """Synthetic table detection whose OBB metrics are explicit and stable."""
    return {
        "bbox_px": bbox,
        "score": 0.9,
        "obb_poly_px": [
            [0.0, 0.0], [long_side, 0.0],
            [long_side, short_side], [0.0, short_side],
        ],
    }


def _track(bbox: list[int], *, miss_count: int = 0) -> dict:
    return {"bbox": bbox, "miss_count": miss_count, "age": 1}


def _pipeline() -> VisionPipeline:
    pipeline = VisionPipeline.__new__(VisionPipeline)
    pipeline._class_match_dist_px = {"table": 120.0}
    pipeline._class_match_iou_min = {"table": 0.05}
    pipeline.reacquire_max_dist = 150.0
    pipeline.reacquire_min_iou = 0.05
    pipeline.table_new_confirm_frames = 2
    pipeline.table_new_fragment_area_ratio = 0.70
    pipeline.table_new_fragment_overlap_ratio = 0.60
    pipeline.table_full_anchor_aspect_min = 1.80
    pipeline.table_full_anchor_aspect_max = 2.15
    pipeline.table_full_anchor_area_ratio = 0.70
    pipeline.table_full_anchor_long_side_ratio = 0.75
    pipeline.table_full_anchor_follow_center_alpha = 0.20
    pipeline.table_lost_anchor_reacquire_coverage_ratio = 0.60
    pipeline._pending_table_births = []
    pipeline._table_tombstones = {}
    pipeline.table_tombstone_reactivation = True
    pipeline.table_tombstone_max_age_seconds = 10.0
    pipeline.table_tombstone_max_distance_cm = 35.0
    pipeline.table_tombstone_max_rotation_deg = 15.0
    pipeline.calibration_profile = TabletopCalibration(np.eye(3, dtype=np.float64))
    pipeline.H = pipeline.calibration_profile.homography
    return pipeline


class VisionTableAssociationTests(unittest.TestCase):
    @staticmethod
    def _tombstone_track(center: tuple[float, float], rotation_deg: float) -> dict:
        return {
            "id": "table_02",
            "bbox": [300, 300, 500, 420],
            "center": center,
            "center_smoothed": center,
            "prev_theta": math.radians(rotation_deg),
            "obb_yaw_rad": math.radians(rotation_deg),
            "obb_poly_px": None,
            "miss_count": 16,
            "table_confirmed": True,
            "table_full_anchor": {"bbox": [300, 300, 500, 420], "obb_long_side": 200.0, "obb_short_side": 100.0, "obb_area": 20000.0, "obb_aspect_ratio": 2.0},
        }

    @staticmethod
    def _tombstone_candidate(center: tuple[float, float], rotation_deg: float) -> dict:
        return {
            "bbox_px": [300, 300, 500, 420],
            "obb_center_px": center,
            "obb_yaw_rad": math.radians(rotation_deg),
            "obb_poly_px": [[300, 300], [500, 300], [500, 420], [300, 420]],
            "score": 0.9,
        }

    def test_documented_post_ttl_rebirth_matches_table_02_tombstone(self) -> None:
        pipeline = _pipeline()
        event = pipeline._create_table_tombstone(
            "table_02", self._tombstone_track((414.80, 358.67), -97.58), 72570, 100.0
        )
        self.assertEqual(event["event"], "tombstone_created")
        match, evaluations = pipeline._evaluate_table_tombstone_reactivation(
            self._tombstone_candidate((407.18, 352.13), -100.20), 106.54
        )
        self.assertEqual(match["tombstone"]["id"], "table_02")
        self.assertAlmostEqual(evaluations[0]["world_distance_cm"], 10.05, places=1)
        self.assertAlmostEqual(evaluations[0]["rotation_delta_deg_mod180"], 2.62, places=1)

    def test_tombstone_rejects_expired_distance_and_rotation_candidates(self) -> None:
        pipeline = _pipeline()
        pipeline._create_table_tombstone("table_02", self._tombstone_track((100, 100), 5), 10, 10.0)
        match, evaluations = pipeline._evaluate_table_tombstone_reactivation(
            self._tombstone_candidate((150, 100), 30), 20.1
        )
        self.assertIsNone(match)
        self.assertIn("expired", evaluations[0]["rejection_reasons"])
        self.assertIn("distance", evaluations[0]["rejection_reasons"])
        self.assertIn("rotation", evaluations[0]["rejection_reasons"])

    def test_tombstone_treats_180_degree_rect_rotations_as_equivalent(self) -> None:
        pipeline = _pipeline()
        pipeline._create_table_tombstone("table_02", self._tombstone_track((100, 100), 5), 10, 10.0)
        match, evaluations = pipeline._evaluate_table_tombstone_reactivation(
            self._tombstone_candidate((100, 100), 184), 11.0
        )
        self.assertEqual(match["tombstone"]["id"], "table_02")
        self.assertAlmostEqual(evaluations[0]["rotation_delta_deg_mod180"], 1.0)

    def test_ambiguous_tombstones_do_not_guess_an_identity(self) -> None:
        pipeline = _pipeline()
        pipeline._create_table_tombstone("table_02", self._tombstone_track((100, 100), 5), 10, 10.0)
        pipeline._create_table_tombstone("table_03", {**self._tombstone_track((101, 100), 5), "id": "table_03"}, 10, 10.0)
        match, evaluations = pipeline._evaluate_table_tombstone_reactivation(
            self._tombstone_candidate((100, 100), 5), 11.0
        )
        self.assertIsNone(match)
        self.assertTrue(all("ambiguous" in item["rejection_reasons"] for item in evaluations))

    def test_unconfirmed_track_never_creates_a_tombstone(self) -> None:
        pipeline = _pipeline()
        track = self._tombstone_track((100, 100), 5)
        track["table_confirmed"] = False
        self.assertIsNone(pipeline._create_table_tombstone("table_02", track, 10, 10.0))
        self.assertEqual(pipeline._table_tombstones, {})

    @staticmethod
    def _lost_anchor_track(
        bbox: list[int],
        anchor_bbox: list[int],
        *,
        long_side: float,
        short_side: float,
        area: float,
        miss_count: int,
    ) -> dict:
        return {
            **_track(bbox, miss_count=miss_count),
            "table_confirmed": True,
            "table_full_anchor": {
                "bbox": anchor_bbox,
                "obb_long_side": long_side,
                "obb_short_side": short_side,
                "obb_area": area,
                "obb_aspect_ratio": long_side / short_side,
            },
        }

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

    def test_recorded_table_04_candidate_reacquires_lost_table_02_anchor(self) -> None:
        pipeline = _pipeline()
        candidate = _obb_det([976, 178, 1247, 540], 321.4094, 171.1286)
        tracks = {
            "table_02": self._lost_anchor_track(
                [969, 399, 1165, 558], [929, 265, 1219, 662],
                long_side=356.35, short_side=180.36, area=63068.0, miss_count=15,
            )
        }
        matches, audit = pipeline._table_anchor_reacquisition_matches(
            [candidate], tracks, {0}, table_ttl_frames=15,
        )
        self.assertEqual(matches, {"table_02": 0})
        evidence = audit[0]["eligible_lost_tracks"][0]
        self.assertAlmostEqual(evidence["center_distance_px"], 111.0, delta=1.0)
        self.assertGreater(evidence["anchor_candidate_coverage"], 0.68)
        self.assertEqual(evidence["plausibility_reasons"], [])
        self.assertEqual(audit[0]["final_action"], "reacquired_existing_id")

    def test_recorded_table_05_candidate_reacquires_lost_table_00_anchor(self) -> None:
        pipeline = _pipeline()
        candidate = _obb_det([1203, 320, 1458, 690], 335.3080, 177.0544)
        tracks = {
            "table_00": self._lost_anchor_track(
                [1263, 306, 1465, 464], [1222, 225, 1494, 611],
                long_side=348.08, short_side=180.36, area=62780.0, miss_count=15,
            )
        }
        matches, audit = pipeline._table_anchor_reacquisition_matches(
            [candidate], tracks, {0}, table_ttl_frames=15,
        )
        self.assertEqual(matches, {"table_00": 0})
        evidence = audit[0]["eligible_lost_tracks"][0]
        self.assertAlmostEqual(evidence["center_distance_px"], 91.2, delta=1.0)
        self.assertGreater(evidence["anchor_candidate_coverage"], 0.72)
        self.assertEqual(evidence["plausibility_reasons"], [])

    def test_small_occlusion_fragment_cannot_anchor_reacquire(self) -> None:
        pipeline = _pipeline()
        fragment = _obb_det([100, 100, 200, 260], 175.1, 109.6)
        tracks = {
            "table_00": self._lost_anchor_track(
                [100, 100, 300, 260], [100, 100, 300, 260],
                long_side=345.0, short_side=177.0, area=61100.0, miss_count=3,
            )
        }
        matches, audit = pipeline._table_anchor_reacquisition_matches(
            [fragment], tracks, {0}, table_ttl_frames=15,
        )
        self.assertEqual(matches, {})
        self.assertEqual(
            audit[0]["eligible_lost_tracks"][0]["plausibility_reasons"],
            ["implausible_aspect", "implausible_area", "implausible_long_side"],
        )

    def test_lost_track_outside_ttl_cannot_anchor_reacquire(self) -> None:
        pipeline = _pipeline()
        full = _obb_det([100, 100, 300, 260], 345.0, 177.0)
        tracks = {
            "table_00": self._lost_anchor_track(
                [100, 100, 300, 260], [100, 100, 300, 260],
                long_side=345.0, short_side=177.0, area=61100.0, miss_count=16,
            )
        }
        matches, audit = pipeline._table_anchor_reacquisition_matches(
            [full], tracks, {0}, table_ttl_frames=15,
        )
        self.assertEqual(matches, {})
        self.assertEqual(audit[0]["eligible_lost_tracks"], [])

    def test_distant_genuine_fifth_table_does_not_steal_lost_id(self) -> None:
        pipeline = _pipeline()
        fifth = _obb_det([700, 100, 900, 260], 345.0, 177.0)
        tracks = {
            "table_00": self._lost_anchor_track(
                [100, 100, 300, 260], [100, 100, 300, 260],
                long_side=345.0, short_side=177.0, area=61100.0, miss_count=3,
            )
        }
        matches, audit = pipeline._table_anchor_reacquisition_matches(
            [fifth], tracks, {0}, table_ttl_frames=15,
        )
        self.assertEqual(matches, {})
        self.assertIn("not_anchor_continuous", audit[0]["eligible_lost_tracks"][0]["rejection_reasons"])

    def test_two_nearby_lost_tracks_use_deterministic_best_anchor_match(self) -> None:
        pipeline = _pipeline()
        candidate = _obb_det([150, 100, 350, 260], 345.0, 177.0)
        tracks = {
            "table_01": self._lost_anchor_track(
                [140, 100, 340, 260], [140, 100, 340, 260],
                long_side=345.0, short_side=177.0, area=61100.0, miss_count=3,
            ),
            "table_00": self._lost_anchor_track(
                [100, 100, 300, 260], [100, 100, 300, 260],
                long_side=345.0, short_side=177.0, area=61100.0, miss_count=3,
            ),
        }
        matches, _ = pipeline._table_anchor_reacquisition_matches(
            [candidate], tracks, {0}, table_ttl_frames=15,
        )
        self.assertEqual(matches, {"table_01": 0})

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

    def test_full_anchor_cannot_ratchet_down_from_gradual_shrink(self) -> None:
        pipeline = _pipeline()
        track: dict = {}
        anchor_metrics = {"long_side": 200.0, "short_side": 100.0, "area": 20000.0, "aspect_ratio": 2.0}
        pipeline._set_table_full_anchor(track, [100, 100, 300, 200], anchor_metrics)
        # Each apparent observation is individually plausible, but smaller.
        # They must not cumulatively replace the full-table dimensions.
        for scale in (0.95, 0.92, 0.93):
            metrics = {
                "long_side": 200.0 * scale,
                "short_side": 100.0 * scale,
                "area": 20000.0 * scale * scale,
                "aspect_ratio": 2.0,
            }
            pipeline._update_table_full_anchor(track, [100, 100, 290, 195], metrics)
        anchor = track["table_full_anchor"]
        self.assertEqual(anchor["obb_long_side"], 200.0)
        self.assertEqual(anchor["obb_short_side"], 100.0)
        self.assertEqual(anchor["obb_area"], 20000.0)

    def test_partial_table_motion_moves_anchor_center_without_shrinking_it(self) -> None:
        pipeline = _pipeline()
        track: dict = {}
        metrics = {"long_side": 200.0, "short_side": 100.0, "area": 20000.0, "aspect_ratio": 2.0}
        pipeline._set_table_full_anchor(track, [100, 100, 300, 200], metrics)
        fragment = {"long_side": 120.0, "short_side": 100.0, "area": 12000.0, "aspect_ratio": 1.2}
        pipeline._update_table_full_anchor(track, [180, 100, 300, 200], fragment)
        anchor = track["table_full_anchor"]
        self.assertEqual(anchor["obb_area"], 20000.0)
        self.assertGreater(pipeline._bbox_center(anchor["bbox"])[0], 200.0)

    def test_full_size_observation_refreshes_anchor(self) -> None:
        pipeline = _pipeline()
        track: dict = {}
        pipeline._set_table_full_anchor(
            track, [100, 100, 300, 200],
            {"long_side": 200.0, "short_side": 100.0, "area": 20000.0, "aspect_ratio": 2.0},
        )
        returned_full = {"long_side": 210.0, "short_side": 105.0, "area": 22050.0, "aspect_ratio": 2.0}
        pipeline._update_table_full_anchor(track, [140, 100, 350, 205], returned_full)
        self.assertEqual(track["table_full_anchor"]["bbox"], [140, 100, 350, 205])
        self.assertEqual(track["table_full_anchor"]["obb_area"], 22050.0)

    def test_recorded_false_birth_obb_shapes_are_locally_implausible(self) -> None:
        pipeline = _pipeline()
        anchor = {"obb_long_side": 345.0, "obb_short_side": 177.0, "obb_area": 61100.0, "obb_aspect_ratio": 1.95}
        table_04 = {"long_side": 175.1, "short_side": 109.6, "area": 19186.0, "aspect_ratio": 1.60}
        table_05 = {"long_side": 231.4, "short_side": 134.8, "area": 31205.5, "aspect_ratio": 1.72}
        for candidate in (table_04, table_05):
            self.assertEqual(
                pipeline._table_obb_plausibility_reasons(candidate, anchor),
                ("implausible_aspect", "implausible_area", "implausible_long_side"),
            )

    def test_obb_metrics_use_polygon_side_lengths(self) -> None:
        metrics = VisionPipeline._table_obb_metrics({
            "obb_poly_px": [[0, 0], [200, 0], [200, 100], [0, 100]],
        })
        self.assertEqual(metrics, {
            "long_side": 200.0,
            "short_side": 100.0,
            "area": 20000.0,
            "aspect_ratio": 2.0,
        })

    def test_calibrated_160_by_80_rect_candidate_is_allowed_for_creation(self) -> None:
        pipeline = _pipeline()
        pipeline.calibration_profile = TabletopCalibration(np.eye(3, dtype=np.float64))
        candidate = _obb_det([0, 0, 160, 80], 160.0, 80.0)

        metrics = pipeline._table_obb_world_metrics(candidate)

        self.assertEqual(metrics, {
            "width_cm": 160.0,
            "height_cm": 80.0,
            "long_side_cm": 160.0,
            "short_side_cm": 80.0,
            "area_cm2": 12800.0,
            "aspect_ratio": 2.0,
        })
        self.assertEqual(pipeline._new_table_world_size_rejection_reasons(metrics), ())

    def test_calibrated_oversized_phantom_candidate_is_rejected_for_creation(self) -> None:
        pipeline = _pipeline()
        pipeline.calibration_profile = TabletopCalibration(np.eye(3, dtype=np.float64))
        phantom = _obb_det([0, 0, 320, 160], 320.0, 160.0)

        metrics = pipeline._table_obb_world_metrics(phantom)

        self.assertGreater(metrics["area_cm2"], RECT_TABLE_OBVIOUSLY_OVERSIZED_AREA_CM2)
        self.assertEqual(
            pipeline._new_table_world_size_rejection_reasons(metrics),
            ("world_area_too_large",),
        )

    def test_confirmed_track_association_does_not_use_new_birth_size_gate(self) -> None:
        pipeline = _pipeline()
        pipeline.calibration_profile = TabletopCalibration(np.eye(3, dtype=np.float64))
        confirmed = _track([100, 100, 420, 260])
        confirmed["table_confirmed"] = True
        oversized = _obb_det([100, 100, 420, 260], 320.0, 160.0)

        self.assertEqual(
            pipeline._greedy_track_match(
                [oversized], {"table_00": confirmed}, ["table_00"], {0}, "table"
            ),
            {"table_00": 0},
        )

    def test_full_size_candidate_near_or_far_remains_plausible(self) -> None:
        pipeline = _pipeline()
        anchor = {"obb_long_side": 345.0, "obb_short_side": 177.0, "obb_area": 61100.0, "obb_aspect_ratio": 1.95}
        candidate = {"long_side": 330.0, "short_side": 170.0, "area": 56100.0, "aspect_ratio": 1.94}
        self.assertEqual(pipeline._table_obb_plausibility_reasons(candidate, anchor), ())

    def test_distant_candidate_is_outside_the_local_anchor_gate(self) -> None:
        pipeline = _pipeline()
        self.assertFalse(
            pipeline._is_table_birth_near_anchor([600, 100, 700, 180], [100, 100, 300, 260])
        )
        # A candidate that overlaps the full anchor is intentionally local
        # even when its center lies beyond the standard association distance.
        self.assertTrue(
            pipeline._is_table_birth_near_anchor([280, 100, 380, 180], [100, 100, 300, 260])
        )

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
        pipeline._tracks = {
            "chair": {},
            "table": {
                "table_170": {
                    **_track([1, 1, 2, 2]),
                    "table_full_anchor": {
                        "bbox": [1, 1, 2, 2],
                        "obb_long_side": 2.0,
                        "obb_short_side": 1.0,
                        "obb_area": 2.0,
                        "obb_aspect_ratio": 2.0,
                    },
                }
            },
            "person": {},
        }
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
