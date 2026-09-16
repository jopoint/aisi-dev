import csv
import json
import tempfile
import unittest
from pathlib import Path

import cv2
import numpy as np

from src.vision.tools.table_obb_preprocess_debug import (
    run_table_obb_preprocess_comparison,
    table_obb_preprocess_variants,
)


class _FakeTableOBBDetector:
    def detect_tables(self, frame_bgr):
        height, width = frame_bgr.shape[:2]
        return [
            {
                "label": "table",
                "bbox_px": [10, 12, width - 10, height - 12],
                "score": 0.91,
                "obb_poly_px": [[10, 12], [width - 10, 12], [width - 10, height - 12], [10, height - 12]],
                "obb_center_px": [width / 2.0, height / 2.0],
                "obb_yaw_rad": 0.0,
            }
        ]


class TableObbPreprocessDebugTests(unittest.TestCase):
    def test_variants_are_named_and_preserve_frame_shape(self):
        frame = np.full((32, 48, 3), 240, dtype=np.uint8)
        variants = table_obb_preprocess_variants()
        self.assertEqual([name for name, _ in variants], [
            "original", "grayscale", "gamma_1p15", "exposure_down", "highlight_clip_225",
            "gaussian_blur_3", "gaussian_blur_5", "gaussian_blur_7", "exposure_down_gaussian_5",
        ])
        for _name, transform in variants:
            processed = transform(frame)
            self.assertEqual(processed.shape, frame.shape)
            self.assertEqual(processed.dtype, np.uint8)

    def test_comparison_writes_per_variant_pngs_and_raw_detector_jsonl(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            image_path = root / "problem.png"
            self.assertTrue(cv2.imwrite(str(image_path), np.full((60, 80, 3), 200, dtype=np.uint8)))
            output = root / "debug"
            jsonl_path = run_table_obb_preprocess_comparison(
                image_path, output, _FakeTableOBBDetector()
            )

            records = [json.loads(line) for line in jsonl_path.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(len(records), 9)
            self.assertEqual({record["preprocessing_variant"] for record in records}, {
                "original", "grayscale", "gamma_1p15", "exposure_down", "highlight_clip_225",
                "gaussian_blur_3", "gaussian_blur_5", "gaussian_blur_7", "exposure_down_gaussian_5",
            })
            for record in records:
                self.assertEqual(record["raw_table_obb_count"], 1)
                self.assertIsNotNone(record["selected_raw_obb"])
                self.assertIsNone(record["final_selected_table_obb"])
                self.assertIsNone(record["final_track_id"])
                prefix = f"frame_00000_{record['preprocessing_variant']}"
                self.assertTrue((output / f"{prefix}_processed.png").exists())
                self.assertTrue((output / f"{prefix}_raw_obb.png").exists())

            with (output / "table_obb_preprocess_summary.csv").open(encoding="utf-8", newline="") as summary_file:
                summary_rows = list(csv.DictReader(summary_file))
            self.assertEqual(len(summary_rows), 9)
            self.assertEqual(summary_rows[0]["detected_table_count"], "1")
            self.assertEqual(summary_rows[0]["highest_confidence"], "0.91")
            self.assertIn("aspect_ratio", summary_rows[0])

    def test_gaussian_variants_smooth_an_impulse_without_changing_dimensions(self):
        frame = np.zeros((17, 17, 3), dtype=np.uint8)
        frame[8, 8] = 255
        variants = dict(table_obb_preprocess_variants())
        for name in ("gaussian_blur_3", "gaussian_blur_5", "gaussian_blur_7", "exposure_down_gaussian_5"):
            processed = variants[name](frame)
            self.assertEqual(processed.shape, frame.shape)
            self.assertLess(int(processed[8, 8, 0]), 255, name)
            self.assertGreater(int(processed[8, 7, 0]), 0, name)
