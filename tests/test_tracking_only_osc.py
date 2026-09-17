from __future__ import annotations

import unittest
from unittest.mock import patch

from aisi.app.sim_scene_to_osc import (
    TrackingOnlyRotationUnwrapper,
    prepare_scene_output,
    send_live_rect_tables,
    send_study_tracked_tables,
    send_tables,
    source_pose_targets,
    vision_frame_perf,
    is_fresh_empty_live_scene,
    is_current_live_scene,
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
    def test_new_vision_frame_perf_uses_capture_and_scene_ready_timestamps(self) -> None:
        scene = {"vision_live": {"frame_id": 12, "perf": {
            "capture_wall_ns": 1_000_000_000,
            "scene_ready_wall_ns": 1_020_000_000,
        }}}
        self.assertEqual(vision_frame_perf(scene, 1_075_000_000), (12, 75.0, 55.0))
        self.assertIsNone(vision_frame_perf({"vision_live": {"frame_id": 12}}, 1_075_000_000))

    def test_fresh_live_scene_gate_rejects_old_frame_and_perf_metadata(self) -> None:
        self.assertTrue(is_fresh_empty_live_scene({"tables": [], "vision_live": {"mode": "tables_only"}}))
        self.assertFalse(is_fresh_empty_live_scene({"tables": [], "vision_live": {
            "mode": "tables_only", "frame_id": 99, "perf": {"capture_wall_ns": 1},
        }}))
        old = {"tables": [{"id": "stale"}], "vision_live": {"mode": "tables_only", "frame_id": 99}}
        self.assertFalse(is_current_live_scene(old, 1_000, 2_000))
        self.assertTrue(is_current_live_scene(old, 3_000, 2_000))

    def test_live_rect_mask_stream_is_binding_independent_and_sorted_by_track_id(self) -> None:
        client = _RecordingOscClient()
        scene = {"tables": [
            {"id": "table_03", "type": "rect", "x_cm": 30, "y_cm": 31, "rotation_deg": 32},
            {"id": "ignore", "type": "sprint", "x_cm": 99, "y_cm": 99, "rotation_deg": 99},
            {"id": "table_01", "type": "rect", "x_cm": 10, "y_cm": 11, "rotation_deg": 12},
            {"id": "table_02", "type": "rect", "x_cm": 20, "y_cm": 21, "rotation_deg": 22},
        ]}
        send_live_rect_tables(client, scene)
        sent = dict(client.messages)
        self.assertEqual(sent["/vision/table/count"], 3)
        self.assertEqual((sent["/vision/table/0/x"], sent["/vision/table/1/x"], sent["/vision/table/2/x"]), (10.0, 20.0, 30.0))

    def test_live_rect_mask_stream_uses_current_scene_and_count_drops_on_disappearance(self) -> None:
        client = _RecordingOscClient()
        send_live_rect_tables(client, {"tables": [{"id": "table_00", "type": "rect", "x_cm": 10, "y_cm": 20, "rotation_deg": 30}]})
        send_live_rect_tables(client, {"tables": [{"id": "table_00", "type": "rect", "x_cm": 110, "y_cm": 120, "rotation_deg": 130}]})
        latest = dict(client.messages[-5:])
        self.assertEqual(latest["/vision/table/0/x"], 110.0)
        send_live_rect_tables(client, {"tables": []})
        self.assertEqual(client.messages[-1], ("/vision/table/count", 0))

    def test_study_bound_tracks_publish_current_poses_at_stable_setup_indices(self) -> None:
        client = _RecordingOscClient()
        scene = {"tables": [
            {"id": "table_03", "x_cm": 30, "y_cm": 31, "rotation_deg": 32},
            {"id": "table_01", "x_cm": 10, "y_cm": 11, "rotation_deg": 12},
            {"id": "table_02", "x_cm": 20, "y_cm": 21, "rotation_deg": 22},
        ]}
        send_study_tracked_tables(client, scene, {0: "table_02", 1: "table_01", 2: "table_03", 3: "table_missing"})
        sent = dict(client.messages)
        self.assertEqual(sent["/study/tracked_table/count"], 4)
        self.assertEqual((sent["/study/tracked_table/0/available"], sent["/study/tracked_table/0/x"]), (1, 20.0))
        self.assertEqual((sent["/study/tracked_table/1/available"], sent["/study/tracked_table/1/x"]), (1, 10.0))
        self.assertEqual((sent["/study/tracked_table/3/available"], sent["/study/tracked_table/3/x"]), (0, 0.0))

    def test_study_bound_track_uses_newest_scene_pose_without_substitution(self) -> None:
        client = _RecordingOscClient()
        bindings = {0: "table_02"}
        send_study_tracked_tables(client, {"tables": [{"id": "table_02", "x_cm": 100, "y_cm": 200, "rotation_deg": 30}]}, bindings)
        send_study_tracked_tables(client, {"tables": [{"id": "table_99", "x_cm": 1, "y_cm": 2, "rotation_deg": 3}]}, bindings)
        latest = dict(client.messages[-5:])
        self.assertEqual(latest["/study/tracked_table/0/available"], 0)
        self.assertEqual(latest["/study/tracked_table/0/x"], 0.0)

    def test_bound_index_zero_matches_the_current_tracking_only_table_zero_pose(self) -> None:
        client = _RecordingOscClient()
        table = {"id": "table_02", "x_cm": 123, "y_cm": 234, "rotation_deg": 45, "type": "rect"}
        send_tables(client, [table], source_pose_targets([table]))
        send_study_tracked_tables(client, {"tables": [table]}, {0: "table_02"})
        sent = dict(client.messages)
        self.assertEqual(sent["/table/0/source_x"], sent["/study/tracked_table/0/x"])
        self.assertEqual(sent["/table/0/source_y"], sent["/study/tracked_table/0/y"])
        self.assertEqual(-sent["/table/0/source_rot"], sent["/study/tracked_table/0/rot"])

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

    def test_tracking_only_selects_requested_id_and_ignores_other_detected_tables(self) -> None:
        desired = _rect_table(0.0)
        ignored = {**_rect_table(45.0), "id": "table_01"}

        selected, _persons, _chairs, targets, reason = prepare_scene_output(
            {"tables": [desired, ignored]}, "input", transformation_strength=0.5, tracking_only=True
        )

        self.assertIsNone(reason)
        self.assertEqual(selected, [desired])
        self.assertEqual(targets, [{"x_cm": 312.5, "y_cm": 187.25, "rotation_deg": 0.0}])

    def test_tracking_only_rejects_missing_requested_table_with_clear_reason(self) -> None:
        selected, _persons, _chairs, targets, reason = prepare_scene_output(
            {"tables": [{**_rect_table(0.0), "id": "table_01"}]},
            "input",
            transformation_strength=0.5,
            tracking_only=True,
            tracking_table_id="table_00",
        )

        self.assertEqual(selected, [])
        self.assertEqual(targets, [])
        self.assertEqual(reason, "requested tracking table 'table_00' not found")

    def test_study_binding_routes_only_the_latched_track_to_table_zero(self) -> None:
        desired = {**_rect_table(0.0), "id": "table_03"}
        ignored = _rect_table(45.0)
        selected, _persons, _chairs, _targets, reason = prepare_scene_output(
            {"tables": [ignored, desired]}, "input", transformation_strength=0.5,
            tracking_only=True, tracking_table_id="table_00",
            study_active_binding_present=True, study_active_track_id="table_03",
        )
        self.assertIsNone(reason)
        self.assertEqual(selected, [desired])

    def test_study_binding_selects_the_current_scene_pose_on_every_call(self) -> None:
        first = {**_rect_table(10.0), "id": "table_02", "x_cm": 100.0}
        second = {**_rect_table(55.0), "id": "table_02", "x_cm": 300.0, "y_cm": 400.0}
        first_selected, *_ = prepare_scene_output(
            {"tables": [first]}, "input", transformation_strength=0.5,
            tracking_only=True, study_active_binding_present=True,
            study_active_track_id="table_02",
        )
        second_selected, *_ = prepare_scene_output(
            {"tables": [second]}, "input", transformation_strength=0.5,
            tracking_only=True, study_active_binding_present=True,
            study_active_track_id="table_02",
        )
        self.assertEqual((first_selected[0]["x_cm"], first_selected[0]["rotation_deg"]), (100.0, 10.0))
        self.assertEqual((second_selected[0]["x_cm"], second_selected[0]["y_cm"], second_selected[0]["rotation_deg"]), (300.0, 400.0, 55.0))

    def test_unresolved_study_binding_emits_no_table_instead_of_falling_back(self) -> None:
        selected, _persons, _chairs, targets, reason = prepare_scene_output(
            {"tables": [_rect_table(0.0)]}, "input", transformation_strength=0.5,
            tracking_only=True, study_active_binding_present=True,
        )
        self.assertEqual(selected, [])
        self.assertEqual(targets, [])
        self.assertEqual(reason, "Study active table is unresolved")

    def test_tracking_only_rejects_missing_or_non_rect_requested_table(self) -> None:
        for tables in ([], [{**_rect_table(0.0), "type": "summit"}]):
            selected, _persons, _chairs, targets, reason = prepare_scene_output(
                {"tables": tables}, "input", transformation_strength=0.5, tracking_only=True
            )
            self.assertEqual(selected, [])
            self.assertEqual(targets, [])
        self.assertIsNotNone(reason)

    def test_standard_layout_mode_preserves_multiple_tables(self) -> None:
        tables = [_rect_table(0.0), {**_rect_table(45.0), "id": "table_01"}]
        generated = [
            {"x_cm": 10.0, "y_cm": 20.0, "rotation_deg": 0.0},
            {"x_cm": 30.0, "y_cm": 40.0, "rotation_deg": 45.0},
        ]
        with patch("aisi.app.sim_scene_to_osc.compute_target_layout", return_value=generated):
            selected, _persons, _chairs, targets, reason = prepare_scene_output(
                {"tables": tables}, "input", transformation_strength=0.5, tracking_only=False
            )

        self.assertEqual(selected, tables)
        self.assertEqual(targets, generated)
        self.assertIsNone(reason)

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
