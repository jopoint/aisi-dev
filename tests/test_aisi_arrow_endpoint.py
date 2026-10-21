import math
import unittest

from td_builders.repair_aisi_arrow_endpoint import corrected_source


SOURCE = '''import math
def points():
    sx, sy, tx, ty = pose
    dist = math.hypot(tx - sx, ty - sy)
    source_inner_poly = None
    end_x, end_y = _ray_polygon_hit(sx, sy, tx, ty, source_inner_poly)
    seg_dx = end_x - sx
    seg_dy = end_y - sy
    return end_x, end_y, math.hypot(seg_dx, seg_dy), math.atan2(seg_dy, seg_dx)
'''


class AisiArrowEndpointTests(unittest.TestCase):
    def test_near_target_stops_at_center_in_all_directions(self):
        for angle in range(0, 360, 15):
            ux, uy = math.cos(math.radians(angle)), math.sin(math.radians(angle))
            result = self.evaluate(.03, ux, uy)
            self.assertAlmostEqual(result[0], 1.2 + .03 * ux)
            self.assertAlmostEqual(result[1], -.7 + .03 * uy)
            self.assertAlmostEqual(result[2], .03)

    def test_far_target_retains_source_boundary(self):
        result = self.evaluate(.8, .6, .8)
        self.assertAlmostEqual(result[0], 1.2 + .4 * .6)
        self.assertAlmostEqual(result[1], -.7 + .4 * .8)
        self.assertAlmostEqual(result[2], .4)

    def test_continuous_at_boundary_and_no_overshoot(self):
        lengths = [self.evaluate(d, .6, .8)[2] for d in (.399999, .4, .400001)]
        for length, expected in zip(lengths, (.399999, .4, .4)):
            self.assertAlmostEqual(length, expected)
        for distance in (.01, .05, .2, .5):
            self.assertLessEqual(self.evaluate(distance, .6, .8)[2], distance + 1e-12)

    def test_idempotent_and_unknown_source_rejected(self):
        patched = corrected_source(SOURCE)
        self.assertEqual(corrected_source(patched), patched)
        with self.assertRaises(ValueError):
            corrected_source('def points():\n    return {}\n')

    def evaluate(self, distance, ux, uy):
        namespace = {'pose': (1.2, -.7, 1.2 + distance * ux, -.7 + distance * uy),
                     '_ray_polygon_hit': lambda *args: (1.2 + .4 * ux, -.7 + .4 * uy)}
        exec(corrected_source(SOURCE), namespace)
        return namespace['points']()


if __name__ == '__main__':
    unittest.main()
