from __future__ import annotations

import json
import math
from pathlib import Path
import tempfile
import unittest

from aisi.app.vision_live_to_aisi_scene import (
    VisionSceneAdapter,
    atomic_write_scene,
    load_last_frame,
)
from aisi_sensing.core.types import DetectedEntity, FrameEvent, Pose2D


def _frame(frame_id: int, tables: list[tuple[str, float, float, float]]) -> FrameEvent:
    return FrameEvent(
        timestamp_iso=f"2026-09-08T12:00:{frame_id:02d}Z",
        frame_id=frame_id,
        furniture=[
            DetectedEntity(table_id, "table", Pose2D(x, y, theta), confidence=0.9)
            for table_id, x, y, theta in tables
        ],
        people=[],
        world={
            "homography_applied": True,
            "calibration_id": "rect_tabletop_v1",
            "calibration_plane": "rect_tabletop",
            "plane_height_cm": 74.0,
        },
    )


class VisionLiveToAisiSceneTests(unittest.TestCase):
    def test_world_coordinates_and_angle_are_preserved_in_scene_units(self) -> None:
        adapter = VisionSceneAdapter()
        theta = -2.281257696612159
        adapter.apply_frame(_frame(1, [("table_00", 290.7609333045584, 342.9816751174564, theta)]))

        table = adapter.scene()["tables"][0]
        self.assertEqual(table["id"], "table_00")
        self.assertEqual(table["x_cm"], 290.7609333045584)
        self.assertEqual(table["y_cm"], 342.9816751174564)
        self.assertAlmostEqual(table["rotation_deg"], math.degrees(theta))
        self.assertEqual(table["type"], "rect")
        self.assertEqual((table["width_cm"], table["height_cm"]), (160.0, 80.0))

    def test_stable_order_is_independent_of_detection_order(self) -> None:
        adapter = VisionSceneAdapter(missing_frames=2)
        adapter.apply_frame(_frame(1, [
            ("table_02", 300.0, 300.0, 0.0),
            ("table_01", 100.0, 100.0, 0.0),
        ]))
        self.assertEqual([item["id"] for item in adapter.scene()["tables"]], ["table_01", "table_02"])

        adapter.apply_frame(_frame(2, [
            ("table_01", 101.0, 100.0, 0.0),
            ("table_02", 301.0, 300.0, 0.0),
        ]))
        tables = adapter.scene()["tables"]
        self.assertEqual([item["id"] for item in tables], ["table_01", "table_02"])
        self.assertEqual(tables[0]["x_cm"], 101.0)

    def test_missing_table_has_bounded_grace_then_is_removed(self) -> None:
        adapter = VisionSceneAdapter(missing_frames=2)
        adapter.apply_frame(_frame(1, [("table_00", 100.0, 100.0, 0.0)]))
        adapter.apply_frame(_frame(2, []))
        self.assertEqual([item["id"] for item in adapter.scene()["tables"]], ["table_00"])
        adapter.apply_frame(_frame(3, []))
        self.assertEqual(adapter.scene()["tables"], [])

    def test_stale_stream_clear_is_explicit(self) -> None:
        adapter = VisionSceneAdapter()
        adapter.apply_frame(_frame(1, [("table_00", 100.0, 100.0, 0.0)]))
        self.assertTrue(adapter.clear_stale())
        self.assertEqual(adapter.scene()["tables"], [])
        self.assertFalse(adapter.clear_stale())

    def test_atomic_scene_write_and_offline_jsonl_last_frame(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            events = root / "events.jsonl"
            events.write_text(
                "\n".join(json.dumps(_frame(index, [("table_00", float(index), 10.0, 0.0)]).to_dict()) for index in (1, 2))
                + "\n",
                encoding="utf-8",
            )
            last = load_last_frame(events)
            self.assertEqual(last.frame_id, 2)

            adapter = VisionSceneAdapter()
            adapter.apply_frame(last)
            scene_path = root / "scene" / "vision_live_scene.json"
            atomic_write_scene(scene_path, adapter.scene())
            payload = json.loads(scene_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["tables"][0]["x_cm"], 2.0)
            self.assertEqual(list(scene_path.parent.glob("*.tmp")), [])

    def test_rejects_frame_without_tabletop_calibration(self) -> None:
        invalid = _frame(1, [("table_00", 100.0, 100.0, 0.0)])
        invalid.world["homography_applied"] = False
        with self.assertRaisesRegex(ValueError, "homography_applied"):
            VisionSceneAdapter().apply_frame(invalid)


if __name__ == "__main__":
    unittest.main()
