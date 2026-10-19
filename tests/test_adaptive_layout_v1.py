from __future__ import annotations

import unittest

from aisi.core.models import ROI, SceneState, TableState, TableTarget
from aisi.generation.adaptive_layout_v1 import (
    ActivityParameters,
    LayoutConstraintError,
    choose_active_tables,
    evenly_distribute,
    input_seats,
    plan_adaptive_input,
    required_active_table_count,
    seats_are_valid,
)


def _scene() -> SceneState:
    return SceneState(
        ROI(0.0, 0.0, 500.0, 500.0),
        [TableState(f"table_{index}", 100.0 + index * 80.0, 250.0, 0.0, 160.0, 80.0, table_type="rect") for index in range(5)],
        "input",
    )


class AdaptiveLayoutV1Tests(unittest.TestCase):
    def test_group_distribution_is_even_and_exact(self) -> None:
        self.assertEqual(evenly_distribute(10, 3), (4, 3, 3))
        self.assertEqual(evenly_distribute(7, 1), (7,))

    def test_active_table_selection_reuses_previous_functional_tables(self) -> None:
        selected = choose_active_tables(_scene(), 2, ("table_3", "table_1"))
        self.assertEqual([table.table_id for table in selected], ["table_1", "table_3"])

    def test_requested_capacity_and_invalid_group_counts_are_explicit(self) -> None:
        self.assertEqual(required_active_table_count("input", ActivityParameters(7)), 3)
        self.assertEqual(required_active_table_count("groupwork", ActivityParameters(10, number_of_groups=3)), 3)
        with self.assertRaises(LayoutConstraintError):
            required_active_table_count("groupwork", ActivityParameters(2, number_of_groups=3))

    def test_input_generates_exact_regular_and_dense_seats(self) -> None:
        scene = _scene()
        table = scene.tables[0]
        target = TableTarget(table.table_id, 250.0, 150.0, target_rot_deg=0.0)
        seats = input_seats(table, target, 3, (0.0, -1.0))
        self.assertEqual(len(seats), 3)
        self.assertEqual(sum(seat.density == "dense" for seat in seats), 1)
        self.assertTrue(seats_are_valid(scene, [target], seats))

    def test_input_plan_keeps_every_table_visible_and_parks_inactive_tables(self) -> None:
        scene = _scene()
        plan = plan_adaptive_input(scene, ActivityParameters(3, presentation_side="north"))
        self.assertEqual(len(plan.seats), 3)
        self.assertEqual(len(plan.active_table_ids), 1)
        self.assertEqual(len(plan.parked_table_ids), 4)
        self.assertEqual({target.table_id for target in plan.table_targets}, {table.table_id for table in scene.tables})
        self.assertTrue(seats_are_valid(scene, plan.table_targets, plan.seats))
