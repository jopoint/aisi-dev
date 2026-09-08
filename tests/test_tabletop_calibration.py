from __future__ import annotations

import json
import math
from pathlib import Path
import tempfile
import unittest

import numpy as np
import cv2

from src.vision.calibration.tabletop import (
    TabletopCalibration,
    fit_homography,
    leave_one_out_report,
    load_tabletop_calibration,
    project_axis_angle,
    project_point,
    residual_report,
)
from src.vision.tools.calibrate_camera_world import run as run_calibration


class TabletopCalibrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.image_points = [(0.0, 0.0), (1000.0, 0.0), (1000.0, 800.0), (0.0, 800.0), (500.0, 400.0), (300.0, 600.0)]
        known = np.array([[0.48, 0.02, 10.0], [0.01, 0.57, 20.0], [0.00001, 0.00002, 1.0]])
        self.world_points = []
        for x, y in self.image_points:
            mapped = known @ np.array([x, y, 1.0])
            self.world_points.append((float(mapped[0] / mapped[2]), float(mapped[1] / mapped[2])))

    def test_fit_project_and_leave_one_out(self) -> None:
        matrix = fit_homography(self.image_points, self.world_points)
        calibration = TabletopCalibration(matrix)
        for pixel, world in zip(self.image_points, self.world_points):
            self.assertAlmostEqual(project_point(pixel, calibration)[0], world[0], places=4)
            self.assertAlmostEqual(project_point(pixel, calibration)[1], world[1], places=4)
        report = residual_report(self.image_points, self.world_points, matrix)
        self.assertLess(report["rmse_cm"], 1e-5)
        self.assertEqual(len(leave_one_out_report(self.image_points, self.world_points)), 6)

    def test_axis_angle_uses_world_homography(self) -> None:
        matrix = fit_homography(self.image_points, self.world_points)
        calibration = TabletopCalibration(matrix)
        angle = project_axis_angle((500.0, 400.0), 0.0, calibration)
        self.assertLess(abs(angle), math.radians(5.0))

    def test_profile_and_legacy_loading(self) -> None:
        matrix = fit_homography(self.image_points, self.world_points).tolist()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            profile_path = root / "profile.json"
            profile_path.write_text(json.dumps({
                "schema_version": 1, "calibration_id": "room-a", "coordinate_system": "aisi_world_cm",
                "calibration_plane": "rect_tabletop", "plane_height_cm": 74.0,
                "processed_image": {"width": 1920, "height": 1080},
                "preprocessing": {"camera_rotate": 0, "crop": None}, "homography": matrix,
            }), encoding="utf-8")
            profile = load_tabletop_calibration(profile_path)
            profile.validate_processed_frame(1920, 1080)
            with self.assertRaises(ValueError):
                profile.validate_processed_frame(1280, 720)
            self.assertEqual(profile.world_metadata()["calibration_plane"], "rect_tabletop")

            legacy_path = root / "legacy.json"
            legacy_path.write_text(json.dumps({"homography": matrix}), encoding="utf-8")
            self.assertFalse(load_tabletop_calibration(legacy_path).profile_backed)

    @unittest.skipUnless(hasattr(cv2, "aruco"), "OpenCV ArUco support unavailable")
    def test_multi_image_single_marker_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
            marker = cv2.aruco.generateImageMarker(dictionary, 7, 80)
            captures = []
            for index, (x, y) in enumerate(((80, 80), (560, 80), (560, 400), (80, 400), (320, 240))):
                image = np.full((480, 640), 255, dtype=np.uint8)
                image[y - 40:y + 40, x - 40:x + 40] = marker
                image_name = f"capture_{index}.png"
                cv2.imwrite(str(root / image_name), image)
                captures.append({"image": image_name, "points": [{"marker_id": 7, "world_cm": [x / 640 * 500, y / 480 * 500]}]})
            manifest = {
                "schema_version": 1, "coordinate_system": "aisi_world_cm", "calibration_plane": "rect_tabletop",
                "plane_height_cm": 74.0, "aruco_dictionary": "DICT_4X4_50",
                "preprocessing": {"camera_rotate": 0, "crop": None}, "captures": captures,
            }
            manifest_path = root / "manifest.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            profile = run_calibration(manifest_path, root / "profile.json", root / "report.json", root / "debug")
            self.assertEqual(profile["validation"]["point_count"], 5)
            self.assertLess(profile["validation"]["rmse_cm"], 0.01)


if __name__ == "__main__":
    unittest.main()
