from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from aisi.analysis.study_metrics import analyze_log, rect_angle_delta_deg, write_metrics_csv


def _event(event_type: str, time_s: float, *, pose: tuple[float, float, float] | None = None, target: tuple[float, float, float] = (100.0, 0.0, 0.0), **extra) -> dict:
    event = {
        "event_type": event_type,
        "monotonic_s": time_s,
        "timestamp_iso": f"2026-01-01T00:00:{time_s:05.2f}+00:00",
        "task_id": "T1", "task": 1, "variant": "A", "condition": 1,
        "target_x_cm": target[0], "target_y_cm": target[1], "target_rotation_deg": target[2],
    }
    if pose is not None:
        event["source_pose"] = {"id": "table_00", "x_cm": pose[0], "y_cm": pose[1], "rotation_deg": pose[2]}
    event.update(extra)
    return event


class StudyMetricTests(unittest.TestCase):
    def _analyze(self, events: list[dict | str]) -> dict:
        directory = tempfile.TemporaryDirectory(); self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "session.jsonl"
        path.write_text("\n".join(item if isinstance(item, str) else json.dumps(item) for item in events) + "\n", encoding="utf-8")
        rows = analyze_log(path)
        self.assertEqual(len(rows), 1)
        return rows[0]

    def test_straight_translation_duration_path_and_success(self) -> None:
        row = self._analyze([
            _event("trial_started", 0, pose=(0, 0, 0)),
            _event("active_pose_sample", 0.1, pose=(0, 0, 0)),
            _event("active_pose_sample", 1.0, pose=(50, 0, 0)),
            _event("active_pose_sample", 2.0, pose=(100, 0, 0)),
            _event("trial_completed", 2.5, pose=(100, 0, 0)),
        ])
        self.assertEqual(row["trial_duration_s"], 2.5)
        self.assertAlmostEqual(row["translation_path_cm"], 100.0)
        self.assertEqual(row["rotation_path_deg"], 0.0)
        self.assertTrue(row["success"])

    def test_translation_and_rotation_paths(self) -> None:
        row = self._analyze([
            _event("trial_started", 0), _event("active_pose_sample", .1, pose=(0, 0, 0), target=(50, 0, 45)),
            _event("active_pose_sample", 1, pose=(25, 0, 20), target=(50, 0, 45)),
            _event("active_pose_sample", 2, pose=(50, 0, 45), target=(50, 0, 45)),
            _event("trial_completed", 2.1, pose=(50, 0, 45), target=(50, 0, 45)),
        ])
        self.assertAlmostEqual(row["translation_path_cm"], 50.0)
        self.assertAlmostEqual(row["rotation_path_deg"], 45.0)

    def test_rect_equivalent_rotation_is_zero_error(self) -> None:
        self.assertEqual(rect_angle_delta_deg(0, 180), 0.0)
        row = self._analyze([_event("trial_started", 0, target=(0, 0, 0)), _event("active_pose_sample", 1, pose=(0, 0, 180), target=(0, 0, 0)), _event("trial_completed", 2, pose=(0, 0, 180), target=(0, 0, 0))])
        self.assertEqual(row["final_rotation_error_deg"], 0.0)
        self.assertTrue(row["success"])

    def test_stationary_jitter_does_not_accumulate_path(self) -> None:
        samples = [_event("trial_started", 0)]
        samples.extend(_event("active_pose_sample", index / 10, pose=((index % 2) * .3, ((index + 1) % 2) * .2, (index % 2) * .4)) for index in range(1, 21))
        samples.append(_event("trial_completed", 2.1, pose=(0, 0, 0)))
        row = self._analyze(samples)
        self.assertEqual(row["translation_path_cm"], 0.0)
        self.assertEqual(row["rotation_path_deg"], 0.0)

    def test_stop_detection_requires_resumed_movement(self) -> None:
        row = self._analyze([
            _event("trial_started", 0), _event("active_pose_sample", .1, pose=(0, 0, 0)),
            _event("active_pose_sample", .5, pose=(20, 0, 0)),
            _event("active_pose_sample", 1.6, pose=(20.2, 0, 0)),
            _event("active_pose_sample", 2.0, pose=(20.1, 0, 0)),
            _event("active_pose_sample", 2.2, pose=(40, 0, 0)),
            _event("trial_completed", 2.3, pose=(40, 0, 0)),
        ])
        self.assertEqual(row["stop_count"], 1)

    def test_correction_is_renewed_meaningful_movement_away_from_target(self) -> None:
        row = self._analyze([
            _event("trial_started", 0, target=(100, 0, 0)), _event("active_pose_sample", .1, pose=(0, 0, 0)),
            _event("active_pose_sample", 1, pose=(50, 0, 0)), _event("active_pose_sample", 2, pose=(35, 0, 0)),
            _event("active_pose_sample", 3, pose=(90, 0, 0)), _event("trial_completed", 3.1, pose=(90, 0, 0)),
        ])
        self.assertEqual(row["correction_count"], 1)

    def test_missing_samples_are_counted_without_failure(self) -> None:
        row = self._analyze([_event("trial_started", 0), _event("active_pose_sample", 1), _event("active_pose_sample", 2, pose=(100, 0, 0)), _event("trial_completed", 3, pose=(100, 0, 0))])
        self.assertEqual((row["valid_pose_sample_count"], row["missing_pose_sample_count"]), (1, 1))

    def test_multiple_trials_and_malformed_line_keep_completed_trials(self) -> None:
        directory = tempfile.TemporaryDirectory(); self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "multi.jsonl"
        events = [_event("trial_started", 0), "{bad json", _event("trial_completed", 1, pose=(100, 0, 0)), _event("trial_started", 2), _event("trial_completed", 3, pose=(100, 0, 0))]
        path.write_text("\n".join(item if isinstance(item, str) else json.dumps(item) for item in events), encoding="utf-8")
        self.assertEqual(len(analyze_log(path)), 2)

    def test_incomplete_trial_is_ignored(self) -> None:
        directory = tempfile.TemporaryDirectory(); self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "incomplete.jsonl"
        path.write_text(json.dumps(_event("trial_started", 0)) + "\n" + json.dumps(_event("active_pose_sample", 1, pose=(20, 0, 0))), encoding="utf-8")
        self.assertEqual(analyze_log(path), [])

    def test_success_threshold_boundaries_and_csv_columns(self) -> None:
        row = self._analyze([_event("trial_started", 0, target=(0, 0, 0)), _event("trial_completed", 1, pose=(8, 0, 5), target=(0, 0, 0))])
        self.assertTrue(row["success"])
        outside = self._analyze([_event("trial_started", 0, target=(0, 0, 0)), _event("trial_completed", 1, pose=(8.01, 0, 5), target=(0, 0, 0))])
        self.assertFalse(outside["success"])
        with tempfile.TemporaryDirectory() as directory:
            csv_path = write_metrics_csv([row], Path(directory) / "metrics.csv")
            self.assertIn("final_position_error_cm", csv_path.read_text(encoding="utf-8"))
