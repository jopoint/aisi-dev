from __future__ import annotations

import ast
import inspect
from pathlib import Path
import time
import unittest

import numpy as np

from src.vision.pipeline import (
    LatestFrameCameraCapture,
    VisionPipeline,
    camera_capture_perf_label,
    format_vision_perf_log,
)


class _FakeCapture:
    def __init__(self, frames: list[np.ndarray]) -> None:
        self.frames = list(frames)
        self.read_count = 0

    def read(self):
        self.read_count += 1
        if not self.frames:
            return False, None
        return True, self.frames.pop(0)


class _ReadSequenceCapture:
    def __init__(self, results, *, delay_seconds: float = 0.0) -> None:
        self._results = list(results)
        self._delay_seconds = delay_seconds
        self._last_frame = np.zeros((2, 2, 3), dtype=np.uint8)

    def read(self):
        if self._delay_seconds:
            time.sleep(self._delay_seconds)
        if not self._results:
            return True, self._last_frame.copy()
        result = self._results.pop(0)
        if isinstance(result, BaseException):
            raise result
        ret, frame = result
        if ret:
            self._last_frame = frame
        return ret, frame


class LatestFrameCameraCaptureTests(unittest.TestCase):
    def test_direct_is_the_process_camera_default(self) -> None:
        self.assertEqual(inspect.signature(VisionPipeline.process_camera_stream).parameters["camera_capture_mode"].default, "direct")

    def test_perf_label_distinguishes_background_capture_from_direct_capture(self) -> None:
        self.assertEqual(camera_capture_perf_label("latest"), "capture_read")
        self.assertEqual(camera_capture_perf_label("direct"), "capture")

    def test_perf_formatter_uses_capture_mode_in_the_runtime_line(self) -> None:
        common = {
            "fps": 19.1,
            "capture_ms": 9.7,
            "generic_yolo_ms": 18.4,
            "table_obb_ms": 20.7,
            "tracking_post_ms": 5.1,
            "jsonl_ms": 2.8,
            "frame_total_ms": 52.3,
            "frame_total_p95_ms": 56.7,
        }
        self.assertIn(
            "capture_read=9.7ms",
            format_vision_perf_log(camera_capture_mode="latest", **common),
        )
        self.assertIn(
            "capture=9.7ms",
            format_vision_perf_log(camera_capture_mode="direct", **common),
        )

    def test_camera_cli_forwards_capture_mode_to_the_runtime_stream(self) -> None:
        tool_path = Path(__file__).parents[1] / "src/vision/tools/run_vision_pipeline.py"
        tree = ast.parse(tool_path.read_text(encoding="utf-8"))
        calls = [
            node for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "process_camera_stream"
        ]
        self.assertEqual(len(calls), 1)
        capture_mode = next(
            keyword.value for keyword in calls[0].keywords
            if keyword.arg == "camera_capture_mode"
        )
        self.assertIsInstance(capture_mode, ast.Attribute)
        self.assertIsInstance(capture_mode.value, ast.Name)
        self.assertEqual(capture_mode.value.id, "args")
        self.assertEqual(capture_mode.attr, "camera_capture_mode")

    def test_latest_retains_only_the_newest_generation_and_its_timestamp(self) -> None:
        first = np.full((2, 2, 3), 1, dtype=np.uint8)
        newest = np.full((2, 2, 3), 2, dtype=np.uint8)
        fake = _FakeCapture([first, newest])
        capture = LatestFrameCameraCapture(fake)
        capture.start()
        deadline = time.monotonic() + 1.0
        while fake.read_count < 2 and time.monotonic() < deadline:
            time.sleep(0.001)
        latest = capture.next_after(0, timeout_seconds=1.0)
        capture.stop()
        self.assertIsNotNone(latest)
        generation, frame, capture_wall_ns, capture_read_ms = latest
        self.assertGreaterEqual(generation, 1)
        self.assertEqual(int(frame[0, 0, 0]), 2)
        self.assertGreater(capture_wall_ns, 0)
        self.assertGreaterEqual(capture_read_ms, 0.0)
        self.assertIsNone(capture.next_after(generation, timeout_seconds=0.01))

    def test_latest_waits_for_a_delayed_first_frame(self) -> None:
        frame = np.full((2, 2, 3), 7, dtype=np.uint8)
        capture = LatestFrameCameraCapture(
            _ReadSequenceCapture([(True, frame)], delay_seconds=0.02),
            first_frame_timeout_seconds=0.2,
        )
        capture.start()
        latest = capture.wait_for_first_frame(timeout_seconds=0.2)
        capture.stop()
        self.assertIsNotNone(latest)
        self.assertEqual(int(latest[1][0, 0, 0]), 7)

    def test_latest_retries_initial_failed_reads_before_first_frame(self) -> None:
        frame = np.full((2, 2, 3), 8, dtype=np.uint8)
        capture = LatestFrameCameraCapture(
            _ReadSequenceCapture([(False, None), (False, None), (True, frame)]),
            first_frame_timeout_seconds=0.2,
        )
        capture.start()
        latest = capture.wait_for_first_frame(timeout_seconds=0.2)
        capture.stop()
        self.assertIsNotNone(latest)
        self.assertEqual(int(latest[1][0, 0, 0]), 8)

    def test_latest_reports_persistent_initial_read_failure(self) -> None:
        capture = LatestFrameCameraCapture(
            _ReadSequenceCapture([(False, None)] * 100),
            first_frame_timeout_seconds=0.03,
        )
        capture.start()
        latest = capture.wait_for_first_frame(timeout_seconds=0.2)
        capture.stop()
        self.assertIsNone(latest)
        self.assertIn("timeout waiting for first frame", capture.status_message())

    def test_latest_reports_worker_exception(self) -> None:
        capture = LatestFrameCameraCapture(
            _ReadSequenceCapture([RuntimeError("camera disconnected")]),
        )
        capture.start()
        latest = capture.wait_for_first_frame(timeout_seconds=0.2)
        capture.stop()
        self.assertIsNone(latest)
        self.assertIn("capture worker exception", capture.status_message())
