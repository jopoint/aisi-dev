from __future__ import annotations

import json
import math
from pathlib import Path
import unittest

from aisi.app.sim_layout_rules import compute_target_layout
from aisi.core.models import ROI, SceneState, TableState, TableTarget
from aisi.core.table_geometry import TABLE_GEOMETRIES, polygon_inside_roi, transform_local_footprint
from aisi.generation.layout_constraints import (
    _SeatClearanceZone,
    _clamp_table_center_to_roi,
    _clearance_zone_intersects_table,
    _obb_intersects,
    _required_table_separation_along_axis,
    _table_footprints_intersect,
    _table_world_footprint,
    evaluate_hard_constraints,
    repair_layout_hard_constraints,
)


def _table(table_id: str, table_type: str) -> TableState:
    geometry = TABLE_GEOMETRIES[table_type]
    return TableState(
        table_id=table_id,
        x=250.0,
        y=250.0,
        width=geometry.nominal_width,
        height=geometry.nominal_depth,
        table_type=table_type,
    )


class LayoutConstraintFootprintTests(unittest.TestCase):
    def test_known_type_pairs_separated_touching_and_overlapping(self) -> None:
        cases = (("summit", "summit", 70.0), ("sprint", "sprint", 60.0), ("summit", "sprint", 65.0))
        for type_a, type_b, touching_distance in cases:
            state_a = _table("a", type_a)
            state_b = _table("b", type_b)
            for rotation_deg in (0.0, 90.0, 180.0, 35.0):
                angle = math.radians(rotation_deg)
                direction = (-math.sin(angle), math.cos(angle))

                def center_at(distance: float) -> tuple[float, float]:
                    return direction[0] * distance, direction[1] * distance

                with self.subTest(types=(type_a, type_b), rotation_deg=rotation_deg):
                    self.assertFalse(
                        _table_footprints_intersect(
                            state_a, (0.0, 0.0), rotation_deg,
                            state_b, center_at(touching_distance + 0.01), rotation_deg, 0.0,
                        )
                    )
                    self.assertTrue(
                        _table_footprints_intersect(
                            state_a, (0.0, 0.0), rotation_deg,
                            state_b, center_at(touching_distance), rotation_deg, 0.0,
                        )
                    )
                    self.assertTrue(
                        _table_footprints_intersect(
                            state_a, (0.0, 0.0), rotation_deg,
                            state_b, center_at(touching_distance - 0.01), rotation_deg, 0.0,
                        )
                    )

    def test_minimum_gap_uses_real_directional_support(self) -> None:
        summit = _table("summit", "summit")
        sprint = _table("sprint", "sprint")
        axis = (1.0, -1.0)
        required = _required_table_separation_along_axis(
            summit, (0.0, 0.0), 0.0,
            sprint, (200.0, -200.0), 0.0,
            axis, 6.0,
        )
        expected = (
            115.0 / math.sqrt(2.0)
            + 49.0 / math.sqrt(2.0)
            + 6.0
        )
        self.assertAlmostEqual(required, expected)
        self.assertTrue(
            _table_footprints_intersect(
                summit, (0.0, 0.0), 0.0,
                sprint, (0.0, 70.0), 0.0, 5.0,
            )
        )
        self.assertFalse(
            _table_footprints_intersect(
                summit, (0.0, 0.0), 0.0,
                sprint, (0.0, 70.0), 0.0, 4.99,
            )
        )

    def test_trapezoids_can_be_separate_when_their_obbs_touch(self) -> None:
        first = _table("a", "summit")
        second = _table("b", "summit")
        self.assertTrue(_obb_intersects((0.0, 0.0), 160.0, 70.0, 0.0, (135.0, -70.0), 160.0, 70.0, 0.0, 0.0))
        self.assertFalse(_table_footprints_intersect(first, (0.0, 0.0), 0.0, second, (135.0, -70.0), 0.0, 0.0))

    def test_rect_matches_existing_obb_for_rotated_cases(self) -> None:
        first = _table("a", "rect")
        second = _table("b", "rect")
        cases = (
            ((0.0, 0.0), 0.0, (160.0, 0.0), 0.0),
            ((0.0, 0.0), 90.0, (0.0, 160.01), 90.0),
            ((0.0, 0.0), 30.0, (90.0, 25.0), -20.0),
            ((0.0, 0.0), 30.0, (300.0, 25.0), -20.0),
        )
        for center_a, rotation_a, center_b, rotation_b in cases:
            with self.subTest(case=(center_a, rotation_a, center_b, rotation_b)):
                polygon_result = _table_footprints_intersect(
                    first, center_a, rotation_a, second, center_b, rotation_b, 0.0
                )
                obb_result = _obb_intersects(
                    center_a, 160.0, 80.0, rotation_a,
                    center_b, 160.0, 80.0, rotation_b, 0.0,
                )
                self.assertEqual(polygon_result, obb_result)

    def test_roi_clamping_keeps_every_known_footprint_inside(self) -> None:
        roi = ROI(0.0, 0.0, 500.0, 500.0)
        for table_type in TABLE_GEOMETRIES:
            state = _table(table_type, table_type)
            for rotation_deg in (0.0, 45.0, 90.0, 180.0):
                with self.subTest(table_type=table_type, rotation_deg=rotation_deg):
                    center = _clamp_table_center_to_roi((-100.0, 700.0), state, rotation_deg, roi)
                    polygon = _table_world_footprint(state, center, rotation_deg)
                    self.assertTrue(polygon_inside_roi(polygon))

    def test_clearance_uses_narrow_wide_and_rotated_trapezoid_sides(self) -> None:
        summit = _table("summit", "summit")

        def zone_at(center: tuple[float, float], rotation_deg: float = 0.0) -> _SeatClearanceZone:
            return _SeatClearanceZone(
                cx=center[0], cy=center[1], width=10.0, height=10.0,
                rot_deg=rotation_deg, seat_direction=(0.0, -1.0),
                seat_side="test", opposite_side="test",
            )

        self.assertFalse(_clearance_zone_intersects_table(zone_at((75.0, 30.0)), summit, (0.0, 0.0), 0.0))
        self.assertTrue(_clearance_zone_intersects_table(zone_at((75.0, -30.0)), summit, (0.0, 0.0), 0.0))

        diagonal_wide_point = transform_local_footprint(((75.0, -30.0),), 0.0, 0.0, 45.0)[0]
        self.assertTrue(
            _clearance_zone_intersects_table(
                zone_at(diagonal_wide_point, 45.0), summit, (0.0, 0.0), 45.0
            )
        )

    def test_legacy_rectangle_uses_width_and_height(self) -> None:
        legacy = TableState("legacy", 0.0, 0.0, width=120.0, height=50.0)
        other = TableState("other", 0.0, 0.0, width=20.0, height=20.0)
        self.assertTrue(_table_footprints_intersect(legacy, (0.0, 0.0), 0.0, other, (70.0, 0.0), 0.0, 0.0))
        self.assertFalse(_table_footprints_intersect(legacy, (0.0, 0.0), 0.0, other, (70.01, 0.0), 0.0, 0.0))

    def test_repair_preserves_ids_and_resolves_overlap_with_gap(self) -> None:
        tables = [_table("summit", "summit"), _table("sprint", "sprint")]
        scene = SceneState(ROI(0.0, 0.0, 500.0, 500.0), tables, "discussion")
        targets = [
            TableTarget("summit", 200.0, 250.0, target_rot_deg=0.0),
            TableTarget("sprint", 250.0, 250.0, target_rot_deg=0.0),
        ]

        outcome = repair_layout_hard_constraints(
            scene, targets, overlap_gap=6.0, clearance_depth_factor=0.0
        )

        self.assertEqual([target.table_id for target in outcome.table_targets], ["summit", "sprint"])
        self.assertTrue(outcome.repair_applied)
        self.assertEqual(outcome.after.overlap_violations, 0)
        self.assertGreaterEqual(
            outcome.table_targets[1].target_x - outcome.table_targets[0].target_x,
            130.0,
        )

    def test_groupwork_pair_overlap_repair_uses_real_footprints(self) -> None:
        tables = [_table("a", "summit"), _table("b", "summit")]
        scene = SceneState(ROI(0.0, 0.0, 500.0, 500.0), tables, "groupwork")
        targets = [TableTarget("a", 250.0, 250.0), TableTarget("b", 250.0, 250.0)]
        notes = [
            "groupwork_assignments=a->pair0, b->pair0",
            "groupwork_pair_geometry=pair0|center=250,250|normal=0,1|gap_cm=74",
        ]

        outcome = repair_layout_hard_constraints(
            scene, targets, generation_notes=notes, clearance_depth_factor=0.0
        )

        self.assertEqual([target.table_id for target in outcome.table_targets], ["a", "b"])
        self.assertEqual(outcome.after.overlap_violations, 0)

    def test_current_live_scene_completes_with_four_targets(self) -> None:
        repository_root = Path(__file__).resolve().parents[1]
        scene = json.loads(
            (repository_root / "data/aisi/scenes/simulated/live_scene.json").read_text(encoding="utf-8")
        )
        targets = compute_target_layout(scene, "input")
        self.assertEqual(len(targets), len(scene["tables"]))
        self.assertTrue(all(set(target) == {"x_cm", "y_cm", "rotation_deg"} for target in targets))

    def test_evaluation_counts_real_polygon_overlap(self) -> None:
        tables = [_table("a", "summit"), _table("b", "summit")]
        scene = SceneState(ROI(-500.0, -500.0, 500.0, 500.0), tables, "groupwork")
        targets = [TableTarget("a", 0.0, 0.0), TableTarget("b", 135.0, -70.0)]
        stats = evaluate_hard_constraints(scene, targets, clearance_depth_factor=0.0)
        self.assertEqual(stats.overlap_violations, 0)


if __name__ == "__main__":
    unittest.main()
