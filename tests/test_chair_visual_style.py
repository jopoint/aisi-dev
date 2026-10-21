import unittest
from td_builders.repair_chair_visual_style import corrected_ring_source


SOURCE = '''THICKNESS = 0.0078   # ca. 1.5 cm
def radii(r_outer):
    r_inner = max(r_outer - THICKNESS, 0.001)
    return r_outer, r_inner
'''


class ChairVisualStyleTests(unittest.TestCase):
    def test_matches_target_thickness_preserves_outer_radius(self):
        text = corrected_ring_source(SOURCE, 2.5 * .0052)
        env = {}
        exec(text, env)
        outer, inner = env['radii'](.13)
        self.assertEqual(outer, .13)
        self.assertAlmostEqual(outer - inner, .013)
        self.assertEqual(corrected_ring_source(text, .013), text)

    def test_rejects_unknown_geometry_and_invalid_thickness(self):
        with self.assertRaises(ValueError):
            corrected_ring_source('pass', .013)
        with self.assertRaises(ValueError):
            corrected_ring_source(SOURCE, 0)


if __name__ == '__main__':
    unittest.main()
