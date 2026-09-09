from __future__ import annotations

import math
import unittest

import numpy as np

from src.vision.calibration.tabletop import TabletopCalibration
from src.vision.detection.yolo_detector import YOLOTableOBBDetector
from src.vision.pipeline import (
    VisionPipeline,
    adaptive_table_smoothing_alphas,
    smooth_tracking_center,
    table_pose_latency_record,
    update_table_obb_yaw,
    update_adaptive_table_smoothing_state,
    validate_table_bbox_smoothing_alpha,
    validate_table_center_smoothing_alpha,
    validate_table_yaw_smoothing_alpha,
)


def _rect_obb_polygon(center: tuple[float, float], width: float, height: float, yaw_rad: float) -> np.ndarray:
    """Build ordered synthetic OBB corners with the long edge along yaw_rad."""
    ux, uy = math.cos(yaw_rad), math.sin(yaw_rad)
    vx, vy = -uy, ux
    half_width, half_height = 0.5 * width, 0.5 * height
    cx, cy = center
    return np.asarray([
        (cx - half_width * ux - half_height * vx, cy - half_width * uy - half_height * vy),
        (cx + half_width * ux - half_height * vx, cy + half_width * uy - half_height * vy),
        (cx + half_width * ux + half_height * vx, cy + half_width * uy + half_height * vy),
        (cx - half_width * ux + half_height * vx, cy - half_width * uy + half_height * vy),
    ], dtype=np.float32)


class RectObbWorldRotationTests(unittest.TestCase):
    def test_adaptive_table_smoothing_uses_moving_alphas_until_stationary(self) -> None:
        self.assertEqual(
            adaptive_table_smoothing_alphas(False, 1.0, 1.0, 0.7),
            (1.0, 1.0, 0.7),
        )

    def test_adaptive_table_smoothing_enters_stationary_after_sustained_low_motion(self) -> None:
        stationary = False
        candidates = 0
        previous_center = (100.0, 100.0)
        previous_yaw = 0.0
        for offset in (0.2, 0.4, 0.6, 0.8, 1.0):
            stationary, candidates = update_adaptive_table_smoothing_state(
                previous_center, previous_yaw, stationary, candidates,
                (100.0 + offset, 100.0), math.radians(0.2),
                enter_center_delta_px=1.5, enter_yaw_delta_deg=0.5, enter_frames=5,
                exit_center_delta_px=3.0, exit_yaw_delta_deg=1.5,
            )
            previous_center = (100.0 + offset, 100.0)
            previous_yaw = math.radians(0.2)
        self.assertTrue(stationary)
        self.assertEqual(adaptive_table_smoothing_alphas(stationary, 1.0, 1.0, 0.7), (0.25, 0.25, 0.25))

    def test_adaptive_table_smoothing_leaves_stationary_immediately_on_motion(self) -> None:
        stationary, candidates = update_adaptive_table_smoothing_state(
            (100.0, 100.0), 0.0, True, 5,
            (104.0, 100.0), 0.0,
            enter_center_delta_px=1.5, enter_yaw_delta_deg=0.5, enter_frames=5,
            exit_center_delta_px=3.0, exit_yaw_delta_deg=1.5,
        )
        self.assertFalse(stationary)
        self.assertEqual(candidates, 0)

    def test_adaptive_table_smoothing_hysteresis_prevents_state_flicker(self) -> None:
        stationary, candidates = update_adaptive_table_smoothing_state(
            (100.0, 100.0), 0.0, True, 5,
            (102.0, 100.0), math.radians(1.0),
            enter_center_delta_px=1.5, enter_yaw_delta_deg=0.5, enter_frames=5,
            exit_center_delta_px=3.0, exit_yaw_delta_deg=1.5,
        )
        self.assertTrue(stationary)
        self.assertEqual(candidates, 5)

    def test_table_yaw_alpha_one_uses_current_small_angle_measurement(self) -> None:
        self.assertAlmostEqual(
            update_table_obb_yaw(0.10, 0.0, smoothing_alpha=1.0),
            0.10,
            places=6,
        )

    def test_table_yaw_alpha_default_preserves_existing_ema(self) -> None:
        self.assertAlmostEqual(
            update_table_obb_yaw(0.10, 0.0, smoothing_alpha=0.20),
            0.02,
            places=6,
        )

    def test_table_yaw_alpha_rejects_invalid_values(self) -> None:
        for alpha in (0.0, -0.1, 1.01):
            with self.subTest(alpha=alpha):
                with self.assertRaises(ValueError):
                    validate_table_yaw_smoothing_alpha(alpha)

    def test_table_pose_latency_record_contains_same_frame_pose_chain(self) -> None:
        record = table_pose_latency_record(
            frame_id=42,
            table_id="table_00",
            raw_obb_center_px=(100.5, 200.5),
            tracked_bbox_center_px=(101.0, 201.0),
            center_smoothed_px=(102.0, 202.0),
            emitted_world_xy_cm=(250.0, 125.0),
            raw_obb_yaw_rad=0.5,
            emitted_table_theta_rad=0.4,
        )
        self.assertEqual(record, {
            "frame_id": 42,
            "table_id": "table_00",
            "raw_obb_center_px": [100.5, 200.5],
            "tracked_bbox_center_px": [101.0, 201.0],
            "center_smoothed_px": [102.0, 202.0],
            "emitted_world_xy_cm": [250.0, 125.0],
            "raw_obb_yaw_rad": 0.5,
            "emitted_table_theta_rad": 0.4,
        })

    def test_table_bbox_alpha_one_uses_current_detection_immediately(self) -> None:
        self.assertEqual(
            VisionPipeline._ema_bbox([100, 200, 300, 400], [400, 600, 800, 1000], 1.0),
            [400, 600, 800, 1000],
        )

    def test_table_bbox_alpha_default_preserves_existing_ema(self) -> None:
        self.assertEqual(
            VisionPipeline._ema_bbox([100, 200, 300, 400], [400, 600, 800, 1000], 0.20),
            [160, 280, 400, 520],
        )

    def test_table_bbox_alpha_rejects_invalid_values(self) -> None:
        for alpha in (0.0, -0.1, 1.01):
            with self.subTest(alpha=alpha):
                with self.assertRaises(ValueError):
                    validate_table_bbox_smoothing_alpha(alpha)

    def test_table_center_alpha_one_uses_current_detection_immediately(self) -> None:
        self.assertEqual(
            smooth_tracking_center((100.0, 200.0), (400.0, 600.0), 1.0),
            (400.0, 600.0),
        )

    def test_table_center_alpha_default_preserves_existing_ema(self) -> None:
        self.assertEqual(
            smooth_tracking_center((100.0, 200.0), (400.0, 600.0), 0.20),
            (160.0, 280.0),
        )

    def test_table_center_alpha_rejects_invalid_values(self) -> None:
        for alpha in (0.0, -0.1, 1.01):
            with self.subTest(alpha=alpha):
                with self.assertRaises(ValueError):
                    validate_table_center_smoothing_alpha(alpha)

    def test_rotating_rect_obb_changes_emitted_world_theta_at_fixed_center(self) -> None:
        center = (320.0, 240.0)
        pipeline = VisionPipeline.__new__(VisionPipeline)
        pipeline.calibration_profile = TabletopCalibration(np.eye(3, dtype=np.float64))
        pipeline.H = pipeline.calibration_profile.homography

        previous = None
        emitted_thetas: list[float] = []
        emitted_centers: list[tuple[float, float]] = []
        for degrees in (0.0, 45.0, 90.0):
            polygon = _rect_obb_polygon(center, width=160.0, height=80.0, yaw_rad=math.radians(degrees))
            raw_yaw = YOLOTableOBBDetector._yaw_from_poly(polygon)
            self.assertIsNotNone(raw_yaw)
            tracked_yaw = update_table_obb_yaw(float(raw_yaw), previous)
            previous = tracked_yaw
            emitted_thetas.append(VisionPipeline._project_table_theta(pipeline, center, tracked_yaw))
            emitted_centers.append(pipeline._project_world_point(center))

        self.assertEqual(emitted_centers, [center, center, center])
        self.assertAlmostEqual(emitted_thetas[0], 0.0, places=6)
        self.assertAlmostEqual(emitted_thetas[1], math.radians(45.0), places=6)
        self.assertAlmostEqual(emitted_thetas[2], math.radians(90.0), places=6)

    def test_180_degree_axis_equivalence_does_not_create_a_turn(self) -> None:
        self.assertAlmostEqual(
            update_table_obb_yaw(math.radians(180.0), 0.0),
            0.0,
            places=6,
        )


if __name__ == "__main__":
    unittest.main()
