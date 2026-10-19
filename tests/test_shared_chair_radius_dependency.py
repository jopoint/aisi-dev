from pathlib import Path
import runpy
from types import SimpleNamespace
import unittest

scope = runpy.run_path(str(Path(__file__).resolve().parents[1] /
                           'td_builders/repair_shared_chair_radius_dependency.py'))


class Parameter:
    mode = 'ParMode.CONSTANT'
    expr = ''
    val = 0.

    def __init__(self, instance):
        self.instance = instance

    def eval(self):
        return self.instance.par.Radius.eval() if self.expr else self.val


def fixture():
    nodes, storage, instances = {}, {}, {}
    for name in ['chairs_template'] + [f'item{i}' for i in range(1, 16)]:
        instance = SimpleNamespace(name=name, par=SimpleNamespace(Radius=SimpleNamespace(eval=lambda: .13)))
        ring = SimpleNamespace(path=scope['ROOT'] + '/' + name + '/chair_geo/chair_ring', par=SimpleNamespace(Valuea=Parameter(instance)))
        callback = SimpleNamespace(path=ring.path + '_callbacks', text='THICKNESS = 0.0078\n' + scope['OLD_RADIUS'])
        children = {'chair_geo/chair_ring': ring, 'chair_geo/chair_ring_callbacks': callback}
        instance.op = lambda path, children=children: children.get(path)
        nodes[ring.path], nodes[callback.path], instances[name] = ring, callback, instance
    chairs = SimpleNamespace(op=instances.get, fetch=lambda key, default: storage.get(key, default), store=lambda key, value: storage.__setitem__(key, value))
    nodes[scope['ROOT']] = chairs
    return nodes.get, instances, storage


class SharedChairRadiusDependencyTests(unittest.TestCase):
    def test_all_rings_and_template_bound_without_changing_ring_style(self):
        resolve, instances, _ = fixture()
        result = scope['repair_radius_dependency'](resolve, 'test.toe')
        self.assertEqual(result['bound_rings'], 16)
        for instance in instances.values():
            ring = instance.op('chair_geo/chair_ring')
            self.assertEqual(ring.par.Valuea.eval(), .13)
            text = instance.op('chair_geo/chair_ring_callbacks').text
            self.assertIn('THICKNESS = 0.0078', text)
            self.assertIn(scope['NEW_RADIUS'], text)
        instances['item10'].par.Radius.eval = lambda: 0.
        self.assertEqual(instances['item10'].op('chair_geo/chair_ring').par.Valuea.eval(), 0.)
        instances['item10'].par.Radius.eval = lambda: .13
        self.assertEqual(instances['item10'].op('chair_geo/chair_ring').par.Valuea.eval(), .13)

    def test_repeated_repair_preserves_original_backup_and_rollback(self):
        resolve, instances, storage = fixture()
        scope['repair_radius_dependency'](resolve, 'test.toe')
        original = storage[scope['BACKUP_KEY']]
        scope['repair_radius_dependency'](resolve, 'test.toe')
        self.assertIs(storage[scope['BACKUP_KEY']], original)
        self.assertEqual(scope['restore_radius_dependency'](resolve)['restored_rings'], 16)
        for instance in instances.values():
            self.assertEqual(instance.op('chair_geo/chair_ring').par.Valuea.expr, '')
            self.assertIn(scope['OLD_RADIUS'], instance.op('chair_geo/chair_ring_callbacks').text)

    def test_unknown_callback_aborts_before_any_changes(self):
        resolve, instances, storage = fixture()
        instances['item10'].op('chair_geo/chair_ring_callbacks').text = 'other callback'
        with self.assertRaises(ValueError):
            scope['repair_radius_dependency'](resolve, 'test.toe')
        self.assertEqual(storage, {})
        self.assertEqual(instances['item1'].op('chair_geo/chair_ring').par.Valuea.expr, '')


if __name__ == '__main__':
    unittest.main()
