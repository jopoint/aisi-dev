from copy import deepcopy
from dataclasses import replace
import unittest

from aisi.analysis.synthetic_input_validation import validate_synthetic_input
from aisi.app.sim_layout_rules import compute_synthetic_layout
from aisi.app.sim_room_editor import make_default_tables, scene_payload


class InputOfflineValidationTests(unittest.TestCase):
    def test_zero_strength_preserves_active_and_parked_source_poses(self):
        scene = scene_payload(make_default_tables(), [], [])
        for count in (1, 7, 15):
            with self.subTest(count=count):
                output = compute_synthetic_layout(scene, "input", 0.0, {
                    "participants": count, "presentation_side": "east", "adaptive_layout_preview": True,
                })
                self.assertEqual(output.table_targets, [
                    {key: float(table[key]) for key in ("x_cm", "y_cm", "rotation_deg")}
                    for table in scene["tables"]
                ])

    def test_independent_checker_detects_capacity_and_chair_displacement(self):
        scene = scene_payload(make_default_tables(), [], [])
        output = compute_synthetic_layout(scene, "input", 1.0, {
            "participants": 15, "adaptive_layout_preview": True,
        })
        self.assertEqual(validate_synthetic_input(scene, output, 15), [])
        self.assertIn("capacity/count", validate_synthetic_input(scene, replace(output, chairs=output.chairs[:-1]), 15))
        chairs = deepcopy(output.chairs)
        chairs[0]["x_cm"] = -30
        errors = validate_synthetic_input(scene, replace(output, chairs=chairs), 15)
        self.assertIn("chair ROI/radius: 0", errors)
        self.assertIn("chair outside seat surface: 0", errors)


if __name__ == "__main__":
    unittest.main()
