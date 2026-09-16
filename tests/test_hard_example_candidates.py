from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import unittest

import cv2
import numpy as np

from src.vision.hard_example_candidates import (
    HardExampleFrame,
    decisions_for_burst,
    group_capture_bursts,
    image_similarity,
    parse_hard_example_filename,
    write_candidate_subset,
)


class HardExampleCandidateTests(unittest.TestCase):
    def _frame(self, directory: Path, index: int, value: int, timestamp: datetime) -> HardExampleFrame:
        name = f"hard_example_{timestamp:%Y%m%d_%H%M%S}_{timestamp.microsecond // 1000:03d}_f{index:06d}_{index:03d}.png"
        path = directory / name
        self.assertTrue(cv2.imwrite(str(path), np.full((20, 30, 3), value, dtype=np.uint8)))
        parsed = parse_hard_example_filename(path)
        self.assertIsNotNone(parsed)
        return parsed

    def test_parser_reads_timestamp_frame_and_sequence(self):
        parsed = parse_hard_example_filename(Path("hard_example_20260916_084148_651_f000151_000.png"))
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.frame_id, 151)
        self.assertEqual(parsed.sequence, 0)
        self.assertEqual(parsed.timestamp, datetime(2026, 9, 16, 8, 41, 48, 651000))

    def test_grouping_splits_timestamp_gaps(self):
        start = datetime(2026, 9, 16, 8, 0, 0)
        frames = [
            HardExampleFrame(Path(f"{index}.png"), start + timedelta(milliseconds=100 * index), index, index)
            for index in range(3)
        ] + [HardExampleFrame(Path("later.png"), start + timedelta(seconds=3), 4, 4)]
        self.assertEqual([len(group) for group in group_capture_bursts(frames)], [3, 1])

    def test_diverse_selection_keeps_first_and_largest_visual_change(self):
        with tempfile.TemporaryDirectory() as directory_name:
            directory = Path(directory_name)
            start = datetime(2026, 9, 16, 8, 0, 0)
            frames = [self._frame(directory, index, value, start + timedelta(milliseconds=index * 100))
                      for index, value in enumerate((0, 2, 255, 4))]
            decisions = decisions_for_burst(frames, representatives=2)
            selected = [item.frame.sequence for item in decisions if item.selected]
            self.assertEqual(selected, [0, 2])
            self.assertEqual(decisions[0].reason, "burst_first")
            self.assertEqual(decisions[2].reason, "maximin_visual_difference")

    def test_single_frame_burst_is_always_retained(self):
        with tempfile.TemporaryDirectory() as directory_name:
            directory = Path(directory_name)
            frame = self._frame(directory, 0, 42, datetime(2026, 9, 16, 8, 0, 0))
            decisions = decisions_for_burst([frame], representatives=3)
            self.assertEqual(len(decisions), 1)
            self.assertTrue(decisions[0].selected)
            self.assertEqual(decisions[0].reason, "burst_first")

    def test_similarity_is_one_for_identical_images(self):
        image = np.zeros((4, 5), dtype=np.float32)
        self.assertEqual(image_similarity(image, image), 1.0)

    def test_copy_writes_manifest_without_modifying_sources(self):
        with tempfile.TemporaryDirectory() as root_name:
            root = Path(root_name)
            source, output = root / "source", root / "output"
            source.mkdir()
            start = datetime(2026, 9, 16, 8, 0, 0)
            frames = [self._frame(source, index, value, start + timedelta(milliseconds=index * 100))
                      for index, value in enumerate((0, 255, 5))]
            decisions, manifest = write_candidate_subset(source, output, representatives=2)
            self.assertEqual(len(list(source.glob("*.png"))), len(frames))
            self.assertEqual(sum(item.selected for item in decisions), 2)
            self.assertTrue(manifest.is_file())
            self.assertEqual(len(list(output.glob("hard_example_*.png"))), 2)
