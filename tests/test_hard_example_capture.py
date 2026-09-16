from datetime import datetime
from pathlib import Path
import tempfile
import unittest

import cv2
import numpy as np

from src.vision.pipeline import VisionPipeline, hard_example_filename


class HardExampleCaptureTests(unittest.TestCase):
    def _pipeline(self, directory: str | None, burst_frames: int = 1):
        # The capture methods deliberately require no detector/tracker state.
        pipeline = object.__new__(VisionPipeline)
        pipeline.hard_example_capture_dir = directory
        pipeline.hard_example_burst_frames = burst_frames
        pipeline._hard_example_burst_remaining = 0
        pipeline._hard_example_capture_sequence = 0
        return pipeline

    def test_filename_is_unique_for_sequence_at_same_timestamp(self):
        now = datetime(2026, 9, 15, 12, 34, 56, 789000)
        self.assertEqual(
            hard_example_filename(42, 0, now),
            "hard_example_20260915_123456_789_f000042_000.png",
        )
        self.assertNotEqual(hard_example_filename(42, 0, now), hard_example_filename(42, 1, now))

    def test_single_capture_saves_the_exact_processed_frame(self):
        frame = np.full((13, 17, 3), (11, 22, 33), dtype=np.uint8)
        with tempfile.TemporaryDirectory() as directory:
            pipeline = self._pipeline(directory)
            path = pipeline._trigger_hard_example_capture(frame, 7)
            self.assertIsNotNone(path)
            np.testing.assert_array_equal(cv2.imread(str(path), cv2.IMREAD_COLOR), frame)
            self.assertEqual(pipeline._hard_example_burst_remaining, 0)

    def test_burst_arms_exactly_remaining_followup_frames_without_tracking_state(self):
        frame = np.full((9, 11, 3), 123, dtype=np.uint8)
        with tempfile.TemporaryDirectory() as directory:
            pipeline = self._pipeline(directory, burst_frames=3)
            pipeline._tracks = {"table": {"table_00": {"age": 9}}}
            pipeline._trigger_hard_example_capture(frame, 10)
            self.assertEqual(pipeline._hard_example_burst_remaining, 2)
            for frame_id in (11, 12):
                pipeline._save_hard_example_frame(frame, frame_id)
                pipeline._hard_example_burst_remaining -= 1
            self.assertEqual(pipeline._hard_example_burst_remaining, 0)
            self.assertEqual(len(list(Path(directory).glob("hard_example_*.png"))), 3)
            self.assertEqual(pipeline._tracks, {"table": {"table_00": {"age": 9}}})

    def test_capture_is_disabled_without_directory(self):
        pipeline = self._pipeline(None)
        self.assertIsNone(pipeline._trigger_hard_example_capture(np.zeros((4, 4, 3), dtype=np.uint8), 1))
        self.assertEqual(pipeline._hard_example_burst_remaining, 0)

