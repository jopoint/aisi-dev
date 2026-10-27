import ast
from pathlib import Path
import unittest
from td_builders import update_motion_feedback_size_cutouts as update
from td_builders import update_motion_feedback_proximity as proximity
from td_builders import update_motion_target_dashes as dashes


class FeedbackSizeCutoutTests(unittest.TestCase):
    def test_supports_both_radius_versions_and_both_target_styles(self):
        original = Path('td_builders/motion_design.frag').read_text(encoding='utf-8')
        for style in (original, dashes.patch_shader(original)):
            for old in (style, proximity.patch_shader(style)):
                new = update.patch_shader(old)
                self.assertIn(update.RADIUS, new)
                self.assertIn(update.NEW_GUIDES, new)
                self.assertIn(update.NEW_SOURCE, new)
                self.assertNotIn(update.OLD_GUIDES, new)
                self.assertNotIn(update.OLD_SOURCE, new)
                self.assertEqual(old.count('targetDashes('), new.count('targetDashes('))
                for anchor in ('*smoothstep(0.0,1.0,state.y)*targetMask;', 'float navRadius=',
                               'float checkScale=', 'float guides=', 'floorColor=over('):
                    self.assertEqual(old.split(anchor)[1].split('\n')[0], new.split(anchor)[1].split('\n')[0])
                with self.assertRaises(RuntimeError):
                    update.patch_shader(new)

    def test_radius_is_80_percent_at_20cm_and_monotonic(self):
        self.assertAlmostEqual(update.radius_cm(20), .8*81.4)
        self.assertEqual(update.radius_cm(80), 35)
        self.assertAlmostEqual(update.radius_cm(8), 81.4)
        values = [update.radius_cm(d) for d in range(121)]
        self.assertTrue(all(a >= b for a, b in zip(values, values[1:])))

    def test_unknown_code_rejected(self):
        with self.assertRaises(RuntimeError):
            update.patch_shader('custom shader')

    def test_antialiased_edge_is_not_a_fully_transparent_core(self):
        import numpy as np
        coverage = np.ones((3, 3), dtype=np.float32)
        coverage[0, 0] = .999967873
        image = np.zeros((3, 3, 4), dtype=np.float32)
        image[0, 0] = 1-coverage[0, 0]
        report = update.check_cutout(image, coverage)
        self.assertEqual(report['core_pixels'], 8)
        self.assertEqual(report['core_max_rgba'], 0)
        self.assertEqual(report['edge_pixels'], 1)
        image[1, 1] = .001
        with self.assertRaises(RuntimeError):
            update.check_cutout(image, coverage)
        image[1, 1] = 0
        image[0, 0] = 1
        with self.assertRaises(RuntimeError):
            update.check_cutout(image, coverage)

    def test_python39(self):
        ast.parse(Path(update.__file__).read_text(encoding='utf-8'), feature_version=(3, 9))
