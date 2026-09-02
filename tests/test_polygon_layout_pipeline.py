from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from aisi.app.sim_layout_rules import _normalize_scene_for_aisi, compute_target_layout
from aisi.core.models import ROI, SceneState, TableState, TableTarget
from aisi.core.table_geometry import required_table_center_separation
from aisi.generation.assignment_utils import score_format_bound_targets
from aisi.generation.layout_constraints import evaluate_hard_constraints
from aisi.projection.debug_plotter import plot_layout_proposal
from aisi.core.models import LayoutProposal
from aisi.input.scene_loader import build_scene_state_from_dict


def _typed_table(table_id: str, table_type: str, x: float, y: float, rotation: float = 0.0) -> TableState:
    dimensions = {"summit": (160.0, 70.0), "sprint": (88.0, 60.0), "rect": (160.0, 80.0)}
    width, height = dimensions[table_type]
    return TableState(table_id, x, y, rotation, width, height, table_type=table_type)


class PolygonLayoutPipelineTests(unittest.TestCase):
    def test_groupwork_reference_separations_are_derived_not_constants(self) -> None:
        cases = (("summit", "summit", 74.0), ("sprint", "sprint", 64.0), ("summit", "sprint", 69.0), ("rect", "rect", 84.0))
        for first_type, second_type, expected in cases:
            with self.subTest(types=(first_type, second_type)):
                first = _typed_table("a", first_type, 0.0, 0.0)
                second = _typed_table("b", second_type, 0.0, 0.0)
                self.assertAlmostEqual(
                    required_table_center_separation(first, 0.0, second, 0.0, (0.0, 1.0), gap=4.0),
                    expected,
                )

    def test_support_separation_handles_relative_rotations_and_legacy_rectangles(self) -> None:
        summit = _typed_table("summit", "summit", 0.0, 0.0)
        sprint = _typed_table("sprint", "sprint", 0.0, 0.0)
        diagonal = required_table_center_separation(
            summit, 30.0, sprint, -25.0, (1.0, 1.0), gap=4.0
        )
        aligned = required_table_center_separation(
            summit, 0.0, sprint, 0.0, (0.0, 1.0), gap=4.0
        )
        self.assertGreater(diagonal, 4.0)
        self.assertNotAlmostEqual(diagonal, aligned)

        legacy = TableState("legacy", 0.0, 0.0, 0.0, 120.0, 50.0)
        self.assertAlmostEqual(
            required_table_center_separation(legacy, 0.0, legacy, 0.0, (1.0, 0.0), gap=4.0),
            124.0,
        )

    def test_format_bound_assignment_preserves_target_ids(self) -> None:
        scene = SceneState(
            ROI(0.0, 0.0, 500.0, 500.0),
            [_typed_table("table_10", "summit", 20.0, 20.0), _typed_table("table_2", "sprint", 300.0, 300.0)],
            "input",
        )
        targets = [
            TableTarget("table_2", 100.0, 100.0),
            TableTarget("table_10", 400.0, 400.0),
        ]
        result = score_format_bound_targets(scene, targets)
        self.assertEqual([target.table_id for target in result.table_targets], ["table_2", "table_10"])
        self.assertIn("assignment_strategy=format_bound", result.notes)

    def test_strength_zero_and_output_order_follow_source_scene_order(self) -> None:
        scene = {
            "roi": {"x_min": 0, "y_min": 0, "x_max": 500, "y_max": 500},
            "tables": [
                {"id": "table_10", "type": "summit", "x_cm": 100, "y_cm": 120, "rotation_deg": 10},
                {"id": "table_2", "type": "sprint", "x_cm": 300, "y_cm": 320, "rotation_deg": -20},
            ],
        }
        targets = compute_target_layout(scene, "discussion", 0.0)
        self.assertEqual(targets, [
            {"x_cm": 100.0, "y_cm": 120.0, "rotation_deg": 10.0},
            {"x_cm": 300.0, "y_cm": 320.0, "rotation_deg": -20.0},
        ])

    def test_live_scene_strengths_never_return_table_overlap_or_roi_failure(self) -> None:
        scene_path = Path("data/aisi/scenes/simulated/live_scene.json")
        if not scene_path.exists():
            self.skipTest("live_scene.json is unavailable")
        raw_scene = json.loads(scene_path.read_text(encoding="utf-8"))
        for learning_format in ("input", "groupwork", "discussion"):
            state = build_scene_state_from_dict(
                _normalize_scene_for_aisi(raw_scene), learning_format=learning_format
            )
            for strength in (0.25, 0.5, 1.0):
                with self.subTest(learning_format=learning_format, strength=strength):
                    output = compute_target_layout(raw_scene, learning_format, strength)
                    targets = [
                        TableTarget(
                            table_id=table.table_id,
                            target_x=item["x_cm"],
                            target_y=item["y_cm"],
                            target_rot_deg=item["rotation_deg"],
                        )
                        for table, item in zip(state.tables, output)
                    ]
                    stats = evaluate_hard_constraints(state, targets, overlap_gap=0.0)
                    self.assertEqual(stats.overlap_violations, 0)
                    self.assertEqual(stats.roi_violations, 0)

    def test_debug_plot_uses_real_polygon_geometry(self) -> None:
        scene = SceneState(
            ROI(0.0, 0.0, 500.0, 500.0),
            [_typed_table("s", "summit", 250.0, 250.0, 0.0)],
            "input",
        )
        proposal = LayoutProposal([TableTarget("s", 250.0, 250.0, target_rot_deg=35.0)])
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "polygon-debug.png"
            plot_layout_proposal(scene, proposal, save_path=destination)
            self.assertTrue(destination.exists())


if __name__ == "__main__":
    unittest.main()
