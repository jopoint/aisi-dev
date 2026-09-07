from __future__ import annotations

import math
import unittest

from aisi.core.models import ROI, SceneState, TableState, TargetStructure, choose_facing_normal_toward_target
from aisi.core.table_geometry import required_table_center_separation
from aisi.generation.layout_constraints import evaluate_hard_constraints
from aisi.generation.layout_synthesizer import (
    _layout_rect_discussion_templates,
    _layout_rect_groupwork_templates,
    _layout_rect_input_templates,
    _uses_rect_template_layout,
    synthesize_layout,
)


SOURCE_IDS = ("table_10", "table_2", "table_7", "table_1", "table_5", "table_3")
SOURCE_POSITIONS = ((90.0, 140.0), (250.0, 140.0), (410.0, 140.0), (90.0, 360.0), (250.0, 360.0), (410.0, 360.0))


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
    def test_input_occupancy_and_historical_two_column_spacing(self) -> None:
        expected_occupancy = {1: [1], 2: [2], 3: [2, 1], 4: [2, 2], 5: [3, 2], 6: [3, 3]}
        for count, occupancy in expected_occupancy.items():
            with self.subTest(count=count):
                scene = _rect_scene(count, "input")
                targets, notes = _layout_rect_input_templates(scene, sorted(scene.tables, key=lambda table: table.table_id))
                self.assertIn(f"rect_input_occupancy={occupancy}", notes)
                rows = {}
                for target in targets:
                    rows.setdefault(round(target.target_y, 6), []).append(target)
                    self.assertEqual(target.target_rot_deg, 0.0)
                self.assertEqual(sorted(len(row) for row in rows.values()), sorted(occupancy))
                if 2 <= count <= 5:
                    two_table_row = next(row for row in rows.values() if len(row) == 2)
                    self.assertAlmostEqual(
                        abs(two_table_row[1].target_x - two_table_row[0].target_x), 220.0
                    )
                if count >= 3:
                    self.assertAlmostEqual(abs(max(rows) - min(rows)), 190.0)

    def test_groupwork_pair_separation_and_metadata_are_geometry_derived(self) -> None:
        scene = _rect_scene(4, "groupwork")
        ordered = sorted(scene.tables, key=lambda table: table.table_id)
        targets, notes = _layout_rect_groupwork_templates(scene, ordered)
        expected = required_table_center_separation(
            ordered[0], 0.0, ordered[1], 0.0, (0.0, 1.0), gap=4.0
        )
        self.assertAlmostEqual(expected, 84.0)
        self.assertIn("groupwork_assignments=table_1->pair0, table_10->pair0, table_2->pair1, table_7->pair1", notes)
        self.assertIn("groupwork_pair_geometry=pair0", notes[3])
        by_id = {target.table_id: target for target in targets}
        self.assertAlmostEqual(abs(by_id["table_10"].target_y - by_id["table_1"].target_y), expected)
        self.assertAlmostEqual(abs(by_id["table_7"].target_y - by_id["table_2"].target_y), expected)

    def test_discussion_templates_form_an_inward_facing_common_center_ring(self) -> None:
        for count in range(2, 7):
            with self.subTest(count=count):
                scene = _rect_scene(count, "discussion")
                targets, _ = _layout_rect_discussion_templates(scene, sorted(scene.tables, key=lambda table: table.table_id))
                radii = [math.hypot(target.target_x - 250.0, target.target_y - 250.0) for target in targets]
                self.assertTrue(all(abs(radius - radii[0]) < 1e-6 for radius in radii))
                for target in targets:
                    facing = choose_facing_normal_toward_target(
                        (target.target_x, target.target_y), (250.0, 250.0), target.target_rot_deg
                    )
                    inward = (250.0 - target.target_x, 250.0 - target.target_y)
                    self.assertGreater(facing[0] * inward[0] + facing[1] * inward[1], 0.0)

    def test_rect_templates_preserve_ids_scene_order_and_geometry_across_strengths(self) -> None:
        for learning_format in ("input", "groupwork", "discussion"):
            for count in range(1, 7):
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
        scene = _rect_scene(4, "discussion")
        proposal = _proposal(scene, 0.0)
        self.assertIn("transformation_strength_zero=exact_source_no_repair", proposal.generation_notes)
        self.assertEqual(
            [(target.target_x, target.target_y, target.target_rot_deg) for target in proposal.table_targets],
            [(table.x, table.y, table.rot_deg) for table in scene.tables],
        )

    def test_mixed_and_large_scenes_stay_on_the_generic_path(self) -> None:
        mixed = _rect_scene(2, "input")
        mixed.tables[1].table_type = "summit"
        large = _rect_scene(6, "input")
        large.tables.append(TableState("table_99", 250.0, 250.0, 0.0, 160.0, 80.0, table_type="rect"))
        self.assertFalse(_uses_rect_template_layout(mixed.tables))
        self.assertFalse(_uses_rect_template_layout(large.tables))


if __name__ == "__main__":
    unittest.main()
