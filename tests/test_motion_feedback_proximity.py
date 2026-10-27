import ast
from pathlib import Path
import unittest
from td_builders import update_motion_feedback_proximity as proximity
from td_builders import update_motion_target_dashes as dashes


class FeedbackProximityTests(unittest.TestCase):
    def test_only_radius_changes_in_both_target_styles(self):
        solid = Path('td_builders/motion_design.frag').read_text(encoding='utf-8')
        for old in (solid, dashes.patch_shader(solid)):
            new = proximity.patch_shader(old)
            self.assertEqual(new.replace(proximity.NEW_RADIUS, proximity.OLD_RADIUS), old)
            self.assertIn('*targetMask', new)
            with self.assertRaises(RuntimeError):
                proximity.patch_shader(new)

    def test_unknown_radius_rejected(self):
        with self.assertRaises(RuntimeError):
            proximity.patch_shader('custom shader')

    def test_python39_compatible(self):
        ast.parse(Path(proximity.__file__).read_text(encoding='utf-8'), feature_version=(3, 9))
