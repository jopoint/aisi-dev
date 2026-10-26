import math
from types import SimpleNamespace
import unittest

from aisi.core.table_geometry import get_table_geometry
from td_builders.aisi_study_visual_style import shared_callback_source
from td_builders.clip_aisi_tabletop_targets import corrected_callback, clip_polygon, transform_polygon, original_callback


class Channel:
    def __init__(self, value): self.value = value
    def eval(self): return self.value


class Raw(dict):
    def __getitem__(self, name): return self.get(name)


class Polygon:
    def __init__(self, count):
        self._vertices = [SimpleNamespace(point=SimpleNamespace(P=(0, 0, 0))) for _ in range(count)]
    def __getitem__(self, index): return self._vertices[index]
    def __iter__(self): return iter(self._vertices)


class Sop:
    def __init__(self, target): self.target, self.prims = target, []
    def parent(self): return self.target
    def clear(self): self.prims = []
    def appendPoly(self, count, **kwargs):
        polygon = Polygon(count)
        self.prims.append(polygon)
        return polygon


def fixture(mode=2, available=1, source_pose=(0, 0, 0, 1, 1), target_pose=(0, 0, 0, 1, 1)):
    def pars(pose): return {name: Channel(value) for name, value in zip(('tx', 'ty', 'rz', 'sx', 'sy'), pose)}
    footprint = [(x * .0052, y * .0052) for x, y in get_table_geometry('rect').local_footprint]
    surface_polygon = Polygon(len(footprint))
    for vertex, (x, y) in zip(surface_polygon, footprint):
        vertex.point.P = (x, y, 0)
    # Reales TD-Script-SOP: vier Flächenpunkte plus unreferenzierte Defaultpunkte.
    orphaned = [(1, 0), (0, 1), (-1, 0), (0, -1)]
    surface = SimpleNamespace(points=[SimpleNamespace(P=(x, y, 0)) for x, y in footprint + orphaned],
                              prims=[surface_polygon])
    source = SimpleNamespace(par=pars(source_pose), op=lambda _: surface)
    item = SimpleNamespace(name='item1', op=lambda _: source)
    target = SimpleNamespace(par=pars(target_pose), parent=lambda: item)
    raw = Raw({'study/mode': Channel(mode), 'table/0/source_available': Channel(available)})
    style = {}
    exec(shared_callback_source(), style)
    scope = {'op': lambda _: raw, 'paint': lambda sop: style['paint'](sop, 'target_tabletop')}
    callback = corrected_callback('def onCook(scriptOp):\n    paint(scriptOp)\n')
    exec(callback, scope)
    return Sop(target), scope, footprint


class PolygonClipTests(unittest.TestCase):
    def test_clockwise_and_counterclockwise_boundaries_produce_same_clip(self):
        boundary = [(-1, -1), (1, -1), (1, 1), (-1, 1)]
        subject = [(-2, -.5), (2, -.5), (2, .5), (-2, .5)]
        for polygon in (boundary, list(reversed(boundary))):
            result = clip_polygon(subject, polygon)
            self.assertEqual({(round(x, 8), round(y, 8)) for x, y in result},
                             {(-1, -.5), (1, -.5), (1, .5), (-1, .5)})

    def test_disjoint_target_is_empty_and_degenerate_source_is_rejected(self):
        self.assertEqual(clip_polygon([(2, 2), (3, 2), (3, 3)], [(0, 0), (1, 0), (1, 1), (0, 1)]), [])
        with self.assertRaises(ValueError): clip_polygon([(0, 0)], [(0, 0)] * 4)

    def test_source_to_target_transform_roundtrips_with_rotation_and_scale(self):
        points = [(-.4, -.2), (.4, .2)]
        a, b = (1, 2, 37, 1.2, .8), (-.3, .2, -54, .9, 1.1)
        result = transform_polygon(transform_polygon(points, a, b), b, a)
        for p, q in zip(points, result):
            self.assertAlmostEqual(p[0], q[0]); self.assertAlmostEqual(p[1], q[1])

    def test_callback_preserves_tracking_and_study_and_hides_absent_source(self):
        for mode in (0, 1):
            sop, scope, _ = fixture(mode=mode, target_pose=(3, 0, 0, 1, 1))
            scope['onCook'](sop)
            self.assertGreater(len(sop.prims), 0)
        sop, scope, _ = fixture(available=0)
        scope['onCook'](sop)
        self.assertEqual(sop.prims, [])

    def test_other_table_cannot_make_disjoint_own_target_visible(self):
        sop, scope, _ = fixture(target_pose=(3, 0, 0, 1, 1))
        scope['onCook'](sop)
        self.assertEqual(sop.prims, [])

    def test_target_dash_vertices_stay_inside_own_source_for_rotated_partial_overlap(self):
        source_pose = (.2, -.1, 33, 1, 1)
        for angle in (-160, -45, 0, 22, 90, 160):
            target_pose = (.3, -.05, angle, 1, 1)
            sop, scope, _ = fixture(source_pose=source_pose, target_pose=target_pose)
            scope['onCook'](sop)
            self.assertGreater(len(sop.prims), 0)
            for prim in sop.prims:
                source_local = transform_polygon([v.point.P[:2] for v in prim], target_pose, source_pose)
                for x, y in source_local:
                    self.assertLessEqual(abs(x), .416 + 1e-9)
                    self.assertLessEqual(abs(y), .208 + 1e-9)

    def test_callback_is_self_contained_and_idempotent(self):
        callback = corrected_callback('def onCook(scriptOp):\n    scriptOp.clear()\n')
        self.assertEqual(corrected_callback(callback), callback)
        scope = {}
        exec(callback, scope)
        self.assertTrue(callable(scope['onCook']))

    def test_unreferenced_source_points_do_not_clip_away_aligned_target(self):
        sop, scope, _ = fixture()
        surface = sop.parent().parent().op('table_source_geo').op('table_surface')
        self.assertEqual(len(surface.points), 8)
        self.assertEqual(len(tuple(surface.prims[0])), 4)
        scope['onCook'](sop)
        self.assertEqual(len(sop.prims), 12)

    def test_upgrade_and_restore_preserve_original_callback(self):
        original = 'def onCook(scriptOp):\n    scriptOp.clear()\n'
        current = corrected_callback(original)
        # Vorherige Variante hat denselben Wrapper, aber einen alten Marker.
        old = current.replace('# aisi_target_polygon_clip_v2', '# aisi_target_polygon_clip_v1')
        upgraded = corrected_callback(old)
        self.assertEqual(upgraded.count('def _unclipped_target_onCook(scriptOp):'), 1)
        self.assertEqual(original_callback(upgraded), original)
        self.assertEqual(original_callback(old), original)


if __name__ == '__main__': unittest.main()
