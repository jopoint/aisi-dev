import unittest

from td_builders.create_floor_tabletop_control import geometry_paths, geometry_expression
from td_builders.repair_layout_control_selection import geometry_paths as repair_paths


class LayoutControlSelectionTests(unittest.TestCase):
    def test_native_selection_includes_five_slots_and_only_existing_roles(self):
        paths = geometry_paths().split()
        self.assertEqual(len(paths), 10)
        self.assertEqual(len(set(paths)), 10)
        for index in range(1, 6):
            for role in ('table_source_geo', 'table_motion_line_tabletop_geo'):
                self.assertIn('/project1/comp_layout_proposal/item%d/%s' % (index, role), paths)
        self.assertNotIn('target', geometry_paths())
        self.assertNotIn('mask', geometry_paths())

    def test_compatibility_expression_and_manual_repair_have_same_native_paths(self):
        self.assertEqual(eval(geometry_expression(), {}), geometry_paths())
        self.assertEqual(repair_paths(), geometry_paths())
        self.assertNotIn('op(', geometry_expression())


if __name__ == '__main__':
    unittest.main()
