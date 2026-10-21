import unittest

from td_builders.repair_aisi_floor_arrow_endpoint import OLD, NEW, OLD_VISIBILITY, NEW_VISIBILITY, corrected_source


SOURCE = '''import math
def points():
    tx, ty = target
    ux, uy = 1, 0
    target_poly = None
    overlap = True
    start_x, start_y = _ray_polygon_hit(0, 0, 1, 0, None)
''' + OLD + '''
    return {'start': (start_x, start_y), 'end': (end_x, end_y),
        'visible': not overlap
    }
'''


class AisiFloorArrowEndpointTests(unittest.TestCase):
    def test_keeps_source_edge_and_ends_at_target_center(self):
        for target in ((2, 0), (-2, 1), (.3, -.4)):
            calls = []
            def hit(*args):
                calls.append(args)
                return .4, .1
            env = {'target': target, '_ray_polygon_hit': hit}
            exec(corrected_source(SOURCE), env)
            result = env['points']()
            self.assertEqual(result['start'], (.4, .1))
            self.assertEqual(result['end'], target)
            self.assertEqual(len(calls), 1)

    def test_preserves_arrival_wrapper_and_upgrades_old_endpoint_patch(self):
        text = SOURCE + "\n# arrival wrapper\n"
        result = corrected_source(text)
        self.assertTrue(result.endswith("# arrival wrapper\n"))
        self.assertIn(NEW, result)
        self.assertIn(NEW_VISIBILITY, result)
        self.assertNotIn(OLD_VISIBILITY, result)
        self.assertEqual(corrected_source(text.replace(OLD, NEW)), result)
        self.assertEqual(corrected_source(result), result)
        with self.assertRaises(ValueError):
            corrected_source('pass')

    def test_partial_overlap_visible_only_if_target_center_beyond_source_edge(self):
        for x, expected in ((.2, False), (.4, False), (.401, False), (.403, True), (1, True)):
            env = {'target': (x, 0), '_ray_polygon_hit': lambda *args: (.4, 0)}
            exec(corrected_source(SOURCE), env)
            self.assertEqual(env['points']()['visible'], expected)


if __name__ == '__main__':
    unittest.main()
