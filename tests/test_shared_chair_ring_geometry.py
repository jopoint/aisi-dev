from pathlib import Path
import runpy
from types import SimpleNamespace
import unittest


inspect_ring_geometry = runpy.run_path(str(Path(__file__).resolve().parents[1] /
                                         'td_builders/inspect_shared_chair_ring_geometry.py'))['inspect_ring_geometry']


def fixture(stale=False):
    instances = {}
    for index in range(15):
        requested = .13 if index < 10 else 0.
        actual = .001 if stale and index == 9 else requested
        ring = SimpleNamespace(points=[SimpleNamespace(P=(actual, 0., 0.))], errors=lambda: '')
        instances[f'item{index + 1}'] = SimpleNamespace(
            name=f'item{index + 1}',
            par=SimpleNamespace(Radius=SimpleNamespace(eval=lambda value=requested: value)),
            op=lambda path, value=ring: value,
        )
    chairs = SimpleNamespace(op=lambda name: instances.get(name))
    return lambda path: chairs


class SharedChairRingGeometryTests(unittest.TestCase):
    def test_matching_and_hidden_rings_without_force_cook_api(self):
        result = inspect_ring_geometry(fixture(), 'test.toe')
        self.assertEqual(result['active_mismatch_indices'], [])
        self.assertEqual(len(result['rings']), 15)

    def test_stale_zero_radius_geometry_at_active_tenth_chair(self):
        result = inspect_ring_geometry(fixture(stale=True), 'test.toe')
        self.assertEqual(result['active_mismatch_indices'], [9])
        self.assertEqual(result['rings'][9]['requested_radius_td'], .13)
        self.assertEqual(result['rings'][9]['actual_outer_radius_td'], .001)


if __name__ == '__main__':
    unittest.main()
