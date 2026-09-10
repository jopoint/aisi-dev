from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from aisi.app.study_logging import JsonlEventLogger, LiveSceneSourcePoseProvider


class StudyLoggingTests(unittest.TestCase):
    def test_jsonl_event_is_serialized_and_flushed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            logger = JsonlEventLogger(directory, session_name="test_session")
            logger.log({"event_type": "trial_loaded", "task_id": "T1"})
            logger.close()
            records = [json.loads(line) for line in Path(logger.path).read_text(encoding="utf-8").splitlines()]
        self.assertEqual(records[0]["event_type"], "trial_loaded")
        self.assertIn("timestamp_iso", records[0])
        self.assertIn("elapsed_s", records[0])

    def test_missing_source_scene_is_safe(self) -> None:
        self.assertIsNone(LiveSceneSourcePoseProvider("not-a-scene.json")())

    def test_source_scene_pose_uses_requested_table(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "scene.json"
            path.write_text(json.dumps({"tables": [{"id": "table_01", "x_cm": 1, "y_cm": 2, "rotation_deg": 3}]}), encoding="utf-8")
            pose = LiveSceneSourcePoseProvider(path, "table_01")()
        self.assertEqual(pose, {"id": "table_01", "x_cm": 1.0, "y_cm": 2.0, "rotation_deg": 3.0})
