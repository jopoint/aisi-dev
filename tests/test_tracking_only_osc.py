from __future__ import annotations

import unittest
from unittest.mock import patch

from aisi.app.sim_scene_to_osc import (
    TrackingOnlyRotationUnwrapper,
    prepare_scene_output,
    send_tables,
    source_pose_targets,
)


class _RecordingOscClient:
    def __init__(self) -> None:
        self.messages: list[tuple[str, object]] = []

    def send_message(self, address: str, value: object) -> None:
        self.messages.append((address, value))


def _rect_table(rotation_deg: float) -> dict:
    return {
        "id": "table_00",
        "x_cm": 312.5,
        "y_cm": 187.25,
        "rotation_deg": rotation_deg,
        "width_cm": 160.0,
        "height_cm": 80.0,
        "type": "rect",
    }


class TrackingOnlyOscTests(unittest.TestCase):
    def test_unwraps_positive_to_negative_boundary(self) -> None:
        unwrapper = TrackingOnlyRotationUnwrapper()
        tables = [unwrapper.unwrap_tables([_rect_table(rotation)]) for rotation in (178.0, 179.0, -179.0, -178.0)]
        emitted = [table[0]["rotation_deg"] for table in tables]
        self.assertEqual(emitted, [178.0, 179.0, 181.0, 182.0])
        client = _RecordingOscClient()
        send_tables(client, tables[2], source_pose_targets(tables[2]))
        sent = dict(client.messages)
        self.assertEqual(sent["/table/0/source_rot"], -181.0)
        self.assertEqual(sent["/table/0/target_rot"], -181.0)

    def test_unwraps_negative_to_positive_boundary(self) -> None:
        unwrapper = TrackingOnlyRotationUnwrapper()
        emitted = [
            unwrapper.unwrap_tables([_rect_table(rotation)])[0]["rotation_deg"]
            for rotation in (-178.0, -179.0, 179.0, 178.0)
        ]
        self.assertEqual(emitted, [-178.0, -179.0, -181.0, -182.0])

    def test_unwraps_rect_180_degree_equivalence(self) -> None:
        unwrapper = TrackingOnlyRotationUnwrapper()
        emitted = [
            unwrapper.unwrap_tables([_rect_table(rotation)])[0]["rotation_deg"]
            for rotation in (88.0, 89.0, 270.0, 271.0)
        ]
        self.assertEqual(emitted, [88.0, 89.0, 90.0, 91.0])

    def test_270_then_91_and_alternating_equivalent_axes_stay_continuous(self) -> None:
        unwrapper = TrackingOnlyRotationUnwrapper()
        emitted = [
            unwrapper.unwrap_tables([_rect_table(rotation)])[0]["rotation_deg"]
            for rotation in (270.0, 91.0, 271.0, 91.0, 271.0)
        ]
        self.assertEqual(emitted, [270.0, 271.0, 271.0, 271.0, 271.0])

    def test_ordinary_rotation_and_mirrored_target_stay_identical(self) -> None:
        unwrapper = TrackingOnlyRotationUnwrapper()
        emitted = [
            unwrapper.unwrap_tables([_rect_table(rotation)])[0]
            for rotation in (0.0, 45.0, 90.0)
        ]
        self.assertEqual([table["rotation_deg"] for table in emitted], [0.0, 45.0, 90.0])
        self.assertEqual(source_pose_targets([emitted[-1]])[0]["rotation_deg"], 90.0)

    def test_disappearance_resets_continuity(self) -> None:
        unwrapper = TrackingOnlyRotationUnwrapper()
        self.assertEqual(unwrapper.unwrap_tables([_rect_table(179.0)])[0]["rotation_deg"], 179.0)
        self.assertEqual(unwrapper.unwrap_tables([]), [])
        self.assertEqual(unwrapper.unwrap_tables([_rect_table(-179.0)])[0]["rotation_deg"], -179.0)

    def test_tracking_only_bypasses_layout_and_mirrors_source_pose(self) -> None:
        scene = {"tables": [_rect_table(45.0)], "persons": [{"id": "ignored"}], "chairs": [{"id": "ignored"}]}
        with patch("aisi.app.sim_scene_to_osc.compute_target_layout") as generate_layout:
            tables, persons, chairs, targets, reason = prepare_scene_output(
                scene, "groupwork", transformation_strength=1.0, tracking_only=True
            )

        generate_layout.assert_not_called()
        self.assertIsNone(reason)
        self.assertEqual(persons, [])
        self.assertEqual(chairs, [])
        self.assertEqual(tables, [scene["tables"][0]])
        self.assertEqual(targets, [{"x_cm": 312.5, "y_cm": 187.25, "rotation_deg": 45.0}])

    def test_tracking_only_keeps_fixed_center_for_all_source_rotations(self) -> None:
        for rotation_deg in (0.0, 45.0, 90.0):
            table = _rect_table(rotation_deg)
            tables, _persons, _chairs, targets, reason = prepare_scene_output(
                {"tables": [table]}, "input", transformation_strength=0.5, tracking_only=True
            )
            self.assertIsNone(reason)
            self.assertEqual((tables[0]["x_cm"], tables[0]["y_cm"]), (312.5, 187.25))
            self.assertEqual(targets[0], {
                "x_cm": 312.5,
                "y_cm": 187.25,
                "rotation_deg": rotation_deg,
            })

    def test_tracking_only_osc_is_single_rect_at_index_zero(self) -> None:
        table = _rect_table(90.0)
        client = _RecordingOscClient()
        send_tables(client, [table], [{"x_cm": 312.5, "y_cm": 187.25, "rotation_deg": 90.0}])
        sent = dict(client.messages)

        self.assertEqual(sent["/table/0/source_x"], 312.5)
        self.assertEqual(sent["/table/0/source_y"], 187.25)
        self.assertEqual(sent["/table/0/source_rot"], -90.0)
        self.assertEqual(sent["/table/0/target_x"], 312.5)
        self.assertEqual(sent["/table/0/target_y"], 187.25)
        self.assertEqual(sent["/table/0/target_rot"], -90.0)
        self.assertEqual(sent["/table/0/type"], "rect")
        self.assertEqual(sent["/table/0/type_id"], 2)

    def test_tracking_only_rejects_missing_non_rect_or_multiple_tables(self) -> None:
        for tables in ([], [{**_rect_table(0.0), "type": "summit"}], [_rect_table(0.0), _rect_table(0.0)]):
            selected, _persons, _chairs, targets, reason = prepare_scene_output(
                {"tables": tables}, "input", transformation_strength=0.5, tracking_only=True
            )
            self.assertEqual(selected, [])
            self.assertEqual(targets, [])
            self.assertIsNotNone(reason)

    def test_standard_layout_mode_does_not_apply_tracking_unwrap(self) -> None:
        generated = [{"x_cm": 1.0, "y_cm": 2.0, "rotation_deg": -179.0}]
        with patch("aisi.app.sim_scene_to_osc.compute_target_layout", return_value=generated) as generate_layout:
            tables, _persons, _chairs, targets, reason = prepare_scene_output(
                {"tables": [_rect_table(179.0)]}, "input", transformation_strength=0.5, tracking_only=False
            )
        generate_layout.assert_called_once()
        self.assertEqual(tables[0]["rotation_deg"], 179.0)
        self.assertEqual(targets, generated)
        self.assertIsNone(reason)


if __name__ == "__main__":
    unittest.main()
