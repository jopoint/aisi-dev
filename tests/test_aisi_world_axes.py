import unittest
from types import SimpleNamespace

from td_builders.repair_aisi_world_axes import (
    ROOT, TABLE_CALLBACK, CHAIR_CALLBACK, corrected_callbacks,
    repair_aisi_world_axes, restore_aisi_world_axes,
)


TABLE = '''def pose(values):
    ROI_CENTER_CM = 250.0
    TD_SCALE = 0.0052
    source_x_td = (
        values['source_x'] - ROI_CENTER_CM
    ) * TD_SCALE
    source_y_td = -(
        values['source_y'] - ROI_CENTER_CM
    ) * TD_SCALE
    target_x_td = (
        values['target_x'] - ROI_CENTER_CM
    ) * TD_SCALE
    target_y_td = -(
        values['target_y'] - ROI_CENTER_CM
    ) * TD_SCALE
    return source_x_td, source_y_td, values['source_rot'], target_x_td, target_y_td, values['target_rot']
'''
CHAIR = '''def pose(x, y, radius):
    return (x - 250.0) * 0.0052, -(y - 250.0) * 0.0052, radius * 0.0052
'''


class AisiWorldAxesTests(unittest.TestCase):
    def test_matches_tracking_positions_preserves_rotations_and_radius(self):
        table, chair = corrected_callbacks(TABLE, CHAIR)
        namespace = {}
        exec(table, namespace)
        values = dict(source_x=100, source_y=350, source_rot=-37,
                      target_x=400, target_y=150, target_rot=82)
        for actual, expected in zip(namespace['pose'](values), (.78, .52, -37, -.78, -.52, 82)):
            self.assertAlmostEqual(actual, expected)
        exec(chair, namespace)
        for actual, expected in zip(namespace['pose'](100, 350, 25), (.78, .52, .13)):
            self.assertAlmostEqual(actual, expected)
        self.assertEqual(corrected_callbacks(table, chair), (table, chair))

    def test_rejects_unknown_callback_before_any_mutation(self):
        nodes, resolve = self.nodes()
        nodes[CHAIR_CALLBACK].text = 'pass'
        with self.assertRaises(ValueError):
            repair_aisi_world_axes(resolve)
        self.assertEqual(nodes[TABLE_CALLBACK].text, TABLE)
        self.assertEqual(nodes[ROOT].backup, {})

    def test_restore_after_repeated_application(self):
        nodes, resolve = self.nodes()
        self.assertEqual(repair_aisi_world_axes(resolve)['changed_callbacks'], 2)
        self.assertEqual(repair_aisi_world_axes(resolve)['changed_callbacks'], 0)
        restore_aisi_world_axes(resolve)
        self.assertEqual(nodes[TABLE_CALLBACK].text, TABLE)
        self.assertEqual(nodes[CHAIR_CALLBACK].text, CHAIR)

    def nodes(self):
        backup = {}
        root = SimpleNamespace(backup=backup, fetch=lambda k, d: backup.get(k, d),
                               store=lambda k, v: backup.__setitem__(k, v))
        nodes = {ROOT: root, TABLE_CALLBACK: SimpleNamespace(text=TABLE),
                 CHAIR_CALLBACK: SimpleNamespace(text=CHAIR)}
        return nodes, nodes.get


if __name__ == '__main__':
    unittest.main()
