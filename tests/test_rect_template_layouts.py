from __future__ import annotations

import math
import unittest
from unittest import mock

from aisi.core.models import ROI, SceneState, TableState, TargetStructure, choose_facing_normal_toward_target
from aisi.analysis.rect_groupwork_adaptive_prototype import singleton_long_side_clearance_regions
from aisi.core.table_geometry import polygon_inside_roi
from aisi.analysis.rect_groupwork_adaptive_prototype import solve_rect_groupwork_prototype
from aisi.generation.layout_constraints import _primary_seat_clearance_zone, evaluate_hard_constraints
from aisi.generation.layout_synthesizer import (
    _layout_rect_discussion_templates,
    _layout_rect_groupwork_templates,
    _rect_discussion_singleton_clearances_valid,
    _uses_rect_template_layout,
    synthesize_layout,
)


SOURCE_IDS = ("table_10", "table_2", "table_7", "table_1", "table_5", "table_3")
SOURCE_POSITIONS = ((90.0, 140.0), (250.0, 140.0), (410.0, 140.0), (90.0, 360.0), (250.0, 360.0), (410.0, 360.0))
INPUT_TEMPLATE_POSITIONS = {
    1: ((250.0, 250.0),),
    2: ((140.0, 250.0), (360.0, 250.0)),
    3: ((122.0, 150.0), (250.0, 250.0), (378.0, 350.0)),
    4: ((140.0, 155.0), (360.0, 155.0), (140.0, 345.0), (360.0, 345.0)),
    5: ((110.0, 150.0), (250.0, 250.0), (390.0, 150.0), (110.0, 350.0), (390.0, 350.0)),
}


def _rect_scene(table_count: int, learning_format: str) -> SceneState:
    ids = SOURCE_IDS[:table_count]
    positions_by_id = {
        table_id: SOURCE_POSITIONS[index]
        for index, table_id in enumerate(sorted(ids))
    }
    return SceneState(
        ROI(0.0, 0.0, 500.0, 500.0),
        [
            TableState(table_id, x, y, 0.0, 160.0, 80.0, table_type="rect")
            for table_id in ids
            for x, y in (positions_by_id[table_id],)
        ],
        learning_format,
    )


def _proposal(scene: SceneState, strength: float):
    return synthesize_layout(
        scene,
        scene_features=None,
        target_profile=None,
        target_structure=TargetStructure(structure_type="rect_template_test"),
        transformation_strength=strength,
    )


class RectTemplateLayoutTests(unittest.TestCase):
    def test_input_templates_use_exact_slots_rotation_and_full_clearance(self) -> None:
        for count, slots in INPUT_TEMPLATE_POSITIONS.items():
            with self.subTest(count=count):
                scene = _rect_scene(count, "input")
                proposal = _proposal(scene, 1.0)
                expected_by_id = {
                    table.table_id: slot
                    for table, slot in zip(sorted(scene.tables, key=lambda table: table.table_id), slots)
                }
                self.assertEqual(
                    [(target.target_x, target.target_y) for target in proposal.table_targets],
                    [expected_by_id[table.table_id] for table in scene.tables],
                )

                for target in proposal.table_targets:
                    self.assertEqual(target.target_rot_deg, 0.0)
                    self.assertEqual(target.facing_target_x, target.target_x)
                    self.assertEqual(target.facing_target_y, target.target_y - 100.0)

                stats = evaluate_hard_constraints(
                    scene,
                    proposal.table_targets,
                    clearance_depth_factor=0.65,
                    generation_notes=proposal.generation_notes,
                )
                self.assertEqual(stats.overlap_violations, 0)
                self.assertEqual(stats.roi_violations, 0)
                self.assertEqual(stats.clearance_violations, 0)

                tables_by_id = {table.table_id: table for table in scene.tables}
                for target in proposal.table_targets:
                    zone = _primary_seat_clearance_zone(target, tables_by_id[target.table_id], 0.65)
                    self.assertGreaterEqual(zone.cx - zone.width * 0.5, scene.roi.x_min)
                    self.assertGreaterEqual(zone.cy - zone.height * 0.5, scene.roi.y_min)
                    self.assertLessEqual(zone.cx + zone.width * 0.5, scene.roi.x_max)
                    self.assertLessEqual(zone.cy + zone.height * 0.5, scene.roi.y_max)

    def test_groupwork_pair_separation_and_metadata_are_geometry_derived(self) -> None:
        scene = _rect_scene(4, "groupwork")
        ordered = sorted(scene.tables, key=lambda table: table.table_id)
        targets, notes = _layout_rect_groupwork_templates(scene, ordered)
        expected = solve_rect_groupwork_prototype(scene, selection="clearance")
        self.assertIn("rect_groupwork=adaptive_local_clearance", notes)
        self.assertIn("groupwork_pair_seam_gap_cm=8.0", notes)
        self.assertEqual(
            [(target.table_id, target.target_x, target.target_y, target.target_rot_deg) for target in targets],
            [
                (target.table_id, target.target_x, target.target_y, target.target_rot_deg)
                for target in expected.table_targets
            ],
        )
        self.assertEqual({target.target_rot_deg for target in targets}, {0.0})

    def test_discussion_templates_form_an_inward_facing_common_center_ring(self) -> None:
        for count in range(2, 6):
            with self.subTest(count=count):
                scene = _rect_scene(count, "discussion")
                targets, _ = _layout_rect_discussion_templates(scene, sorted(scene.tables, key=lambda table: table.table_id))
                center = (targets[0].facing_target_x, targets[0].facing_target_y)
                self.assertIsNotNone(center[0])
                self.assertIsNotNone(center[1])
                radii = [math.hypot(target.target_x - center[0], target.target_y - center[1]) for target in targets]
                self.assertTrue(all(abs(radius - radii[0]) < 1e-6 for radius in radii))
                for target in targets:
                    facing = choose_facing_normal_toward_target(
                        (target.target_x, target.target_y), center, target.target_rot_deg
                    )
                    inward = (center[0] - target.target_x, center[1] - target.target_y)
                    self.assertGreater(facing[0] * inward[0] + facing[1] * inward[1], 0.0)

    def test_discussion_uses_complete_fifty_cm_singleton_clearance_for_all_counts(self) -> None:
        for count in range(1, 6):
            with self.subTest(count=count):
                scene = _rect_scene(count, "discussion")
                proposal = _proposal(scene, 1.0)
                self.assertIn("rect_discussion_singleton_clearance_depth_cm=50.0", proposal.generation_notes)
                self.assertTrue(_rect_discussion_singleton_clearances_valid(scene, proposal.table_targets))
                for target in proposal.table_targets:
                    table = next(table for table in scene.tables if table.table_id == target.table_id)
                    for region in singleton_long_side_clearance_regions(
                        target,
                        table,
                        clearance_depth_cm=50.0,
                    ):
                        self.assertTrue(
                            polygon_inside_roi(
                                region,
                                x_min=scene.roi.x_min,
                                y_min=scene.roi.y_min,
                                x_max=scene.roi.x_max,
                                y_max=scene.roi.y_max,
                            )
                        )

    def test_discussion_strength_remains_visibly_interpolated_before_the_final_target(self) -> None:
        scene = _rect_scene(5, "discussion")
        partial = _proposal(scene, 0.25)
        completed = _proposal(scene, 1.0)

        self.assertNotEqual(
            [(target.target_x, target.target_y, target.target_rot_deg) for target in partial.table_targets],
            [(target.target_x, target.target_y, target.target_rot_deg) for target in completed.table_targets],
        )
        self.assertIn("transformation_strength=0.250", partial.generation_notes)
        self.assertIn("repair_skipped=rect_discussion_target_clearance_valid", completed.generation_notes)

    def test_discussion_continuously_rotates_the_ring_to_reduce_local_motion(self) -> None:
        scene = SceneState(
            ROI(0.0, 0.0, 500.0, 500.0),
            [
                TableState("table_0", 374.286, 190.714, 40.0, 160.0, 80.0, table_type="rect"),
                TableState("table_3", 225.0, 266.429, 125.0, 160.0, 80.0, table_type="rect"),
                TableState("table_5", 113.571, 165.0, 25.0, 160.0, 80.0, table_type="rect"),
                TableState("table_6", 338.571, 416.037, 5.0, 160.0, 80.0, table_type="rect"),
                TableState("table_7", 100.714, 429.286, -15.0, 160.0, 80.0, table_type="rect"),
            ],
            "discussion",
        )

        targets, notes = _layout_rect_discussion_templates(scene, sorted(scene.tables, key=lambda table: table.table_id))
        source_by_id = {table.table_id: table for table in scene.tables}
        distances = [
            math.hypot(source_by_id[target.table_id].x - target.target_x, source_by_id[target.table_id].y - target.target_y)
            for target in targets
        ]

        self.assertIn("rect_discussion_ring_phase=clearance_constrained_minimax_motion", notes)
        self.assertLess(max(distances), 140.0)
        self.assertLess(sum(distances), 540.0)

        reversed_scene = SceneState(scene.roi, list(reversed(scene.tables)), "discussion")
        reversed_targets, _ = _layout_rect_discussion_templates(
            reversed_scene,
            sorted(reversed_scene.tables, key=lambda table: table.table_id),
        )
        self.assertEqual(
            {
                target.table_id: (target.target_x, target.target_y, target.target_rot_deg)
                for target in targets
            },
            {
                target.table_id: (target.target_x, target.target_y, target.target_rot_deg)
                for target in reversed_targets
            },
        )

    def test_rect_templates_preserve_ids_scene_order_and_geometry_across_strengths(self) -> None:
        for learning_format in ("input", "groupwork", "discussion"):
            for count in range(1, 6):
                scene = _rect_scene(count, learning_format)
                expected_ids = [table.table_id for table in scene.tables]
                for strength in (0.25, 0.5, 1.0):
                    with self.subTest(learning_format=learning_format, count=count, strength=strength):
                        proposal = _proposal(scene, strength)
                        self.assertIn(f"rect_template={learning_format}", proposal.generation_notes)
                        self.assertEqual([target.table_id for target in proposal.table_targets], expected_ids)
                        stats = evaluate_hard_constraints(scene, proposal.table_targets, overlap_gap=0.0)
                        self.assertEqual(stats.overlap_violations, 0)
                        self.assertEqual(stats.roi_violations, 0)

    def test_strength_zero_keeps_exact_source_targets(self) -> None:
        for learning_format in ("input", "groupwork", "discussion"):
            with self.subTest(learning_format=learning_format):
                scene = _rect_scene(4, learning_format)
                proposal = _proposal(scene, 0.0)
                self.assertIn("transformation_strength_zero=exact_source_no_repair", proposal.generation_notes)
                self.assertEqual(
                    [(target.target_x, target.target_y, target.target_rot_deg) for target in proposal.table_targets],
                    [(table.x, table.y, table.rot_deg) for table in scene.tables],
                )

    def test_mixed_and_six_table_scenes_do_not_use_rect_templates(self) -> None:
        mixed = _rect_scene(2, "input")
        mixed.tables[1].table_type = "summit"
        six_rect_tables = _rect_scene(6, "input")
        self.assertFalse(_uses_rect_template_layout(mixed.tables))
        self.assertFalse(_uses_rect_template_layout(six_rect_tables.tables))

    def test_layout_capacity_rejects_six_tables_before_synthesis(self) -> None:
        six_rect_tables = _rect_scene(6, "input")
        six_mixed_tables = _rect_scene(6, "input")
        six_mixed_tables.tables[-1].table_type = "summit"

        for scene in (six_rect_tables, six_mixed_tables):
            with self.subTest(table_types=[table.table_type for table in scene.tables]):
                with mock.patch(
                    "aisi.generation.layout_synthesizer._layout_input_adaptive",
                    side_effect=AssertionError("layout synthesis must not run"),
                ) as layout_synthesis, mock.patch(
                    "aisi.generation.layout_synthesizer.repair_layout_hard_constraints",
                    side_effect=AssertionError("layout repair must not run"),
                ) as layout_repair:
                    with self.assertRaisesRegex(
                        ValueError,
                        "AISI layout generation supports at most 5 tables in the current 500x500 cm ROI; received 6.",
                    ):
                        _proposal(scene, 1.0)
                layout_synthesis.assert_not_called()
                layout_repair.assert_not_called()


if __name__ == "__main__":
    unittest.main()
