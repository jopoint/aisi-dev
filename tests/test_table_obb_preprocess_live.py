from pathlib import Path
import unittest

import cv2
import numpy as np

from src.vision.pipeline import table_obb_detector_input, yolo_detector_inputs


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


class TableObbPreprocessLiveTests(unittest.TestCase):
    def setUp(self):
        self.frame = np.zeros((17, 17, 3), dtype=np.uint8)
        self.frame[8, 8] = (255, 255, 255)

    def test_none_returns_original_frame_for_table_inference(self):
        self.assertIs(table_obb_detector_input(self.frame, "none"), self.frame)

    def test_gaussian5_matches_opencv_exactly(self):
        expected = cv2.GaussianBlur(self.frame, (5, 5), 0)
        actual = table_obb_detector_input(self.frame, "gaussian5")
        self.assertIsNot(actual, self.frame)
        np.testing.assert_array_equal(actual, expected)

    def test_generic_yolo_stays_original_while_table_obb_gets_preprocessed_copy(self):
        generic_input, table_input = yolo_detector_inputs(self.frame, "gaussian5")
        self.assertIs(generic_input, self.frame)
        self.assertIsNot(table_input, self.frame)
        np.testing.assert_array_equal(table_input, cv2.GaussianBlur(self.frame, (5, 5), 0))

    def test_unsupported_preprocess_mode_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "none.*gaussian5"):
            table_obb_detector_input(self.frame, "blur9")

    def test_current_room_launchers_forward_the_option(self):
        vision_launcher = (REPOSITORY_ROOT / "scripts" / "run_current_room_rect_vision.ps1").read_text(
            encoding="utf-8"
        )
        tracking_launcher = (REPOSITORY_ROOT / "scripts" / "run_current_room_tracking_only.ps1").read_text(
            encoding="utf-8"
        )
        self.assertIn('[ValidateSet("none", "gaussian5")]', vision_launcher)
        self.assertIn('"--table-obb-preprocess", $TableObbPreprocess', vision_launcher)
        self.assertIn("-TableObbPreprocess $TableObbPreprocess", tracking_launcher)

