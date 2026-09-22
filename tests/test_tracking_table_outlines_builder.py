"""Focused non-TouchDesigner checks for live multi-table tracking outlines."""

import unittest
from unittest.mock import patch

from td_builders.tracking_table_outlines import (
    DEFAULT_TRACKING_MATERIAL_PATH,
    FLOOR_BRACKET_DEPTH_CM,
    FLOOR_BRACKET_WIDTH_CM,
    TABLETOP_DEPTH_CM,
    TABLETOP_WIDTH_CM,
    TRACKING_RENDER_SENTINEL,
    TRACKING_TABLE_CAPACITY,
    _live_tracking_transform_expressions,
    _tracking_visibility_expression,
    configure_tracking_mode_render_paths,
    apply_tracking_table_material,
    create_tracking_table_material,
    create_tracking_table_outline_geos,
    tracking_floor_geometry_names,
    tracking_mode_render_expression,
    tracking_render_geometry_list,
    tracking_tabletop_geometry_names,
)
from td_builders.study_tabletop_brackets import TD_UNITS_PER_CM, rect_continuous_outline_segments


class TrackingTableOutlinesBuilderTests(unittest.TestCase):
    def test_builder_creates_each_live_slot_with_its_own_geometry(self):
        class Parameter:
            def __init__(self): self.expr = ""

        class Parameters:
            def __init__(self):
                self.tx, self.ty, self.rz, self.sx = (Parameter() for _ in range(4))
                self.material = None

        geometry_kind, merge_kind, rectangle_kind = object(), object(), object()

        class Connector:
            def connect(self, _node): pass

        class Node:
            def __init__(self, kind, name):
                self.kind, self.name, self.par = kind, name, Parameters()
                self.children, self.display, self.render = [], False, False
                self.nodeX = self.nodeY = 0
                self.inputConnectors = [Connector() for _ in range(8)]

            def op(self, name):
                return next((child for child in self.children if child.name == name), None)

            def create(self, kind, name):
                child = Node(kind, name)
                self.children.append(child)
                return child

        class Parent(Node):
            def __init__(self):
                super().__init__(geometry_kind, "parent")
                self.by_name = {}

            def op(self, name): return self.by_name.get(name)

            def create(self, kind, name):
                child = Node(kind, name)
                self.by_name[name] = child
                return child

        parent = Parent()
        from td_builders import tracking_table_outlines
        from td_builders import study_tabletop_brackets
        with patch.object(tracking_table_outlines, "op", lambda _path: parent, create=True), patch.object(
            tracking_table_outlines, "geometryCOMP", geometry_kind, create=True
        ), patch.object(study_tabletop_brackets, "mergeSOP", merge_kind, create=True), patch.object(
            study_tabletop_brackets, "rectangleSOP", rectangle_kind, create=True
        ):
            floor_geos, tabletop_geos = create_tracking_table_outline_geos()

        self.assertEqual(len(floor_geos), TRACKING_TABLE_CAPACITY)
        self.assertEqual(len(tabletop_geos), TRACKING_TABLE_CAPACITY)
        self.assertIn("vision/table/0/x", floor_geos[0].par.tx.expr)
        self.assertIn("vision/table/5/x", tabletop_geos[5].par.tx.expr)
        self.assertEqual(floor_geos[0].par.material, DEFAULT_TRACKING_MATERIAL_PATH)
        self.assertEqual(len(floor_geos[0].children), 5)  # merge plus four bars
        self.assertTrue(floor_geos[0].children[0].display)
        self.assertTrue(floor_geos[0].children[0].render)
        self.assertTrue(all(not child.render for child in floor_geos[0].children[1:]))

    def test_six_floor_and_tabletop_slots_have_index_coupled_names(self):
        self.assertEqual(TRACKING_TABLE_CAPACITY, 6)
        self.assertEqual(tracking_floor_geometry_names()[0], "rect_tracking_floor_geo_00")
        self.assertEqual(tracking_floor_geometry_names()[-1], "rect_tracking_floor_geo_05")
        self.assertEqual(tracking_tabletop_geometry_names()[0], "rect_tracking_tabletop_geo_00")
        self.assertEqual(tracking_tabletop_geometry_names()[-1], "rect_tracking_tabletop_geo_05")

    def test_outlines_reuse_source_footprints_and_four_bar_stroke(self):
        self.assertEqual((FLOOR_BRACKET_WIDTH_CM, FLOOR_BRACKET_DEPTH_CM), (170.0, 90.0))
        self.assertEqual((TABLETOP_WIDTH_CM, TABLETOP_DEPTH_CM), (150.0, 70.0))
        for width, depth in ((FLOOR_BRACKET_WIDTH_CM, FLOOR_BRACKET_DEPTH_CM), (TABLETOP_WIDTH_CM, TABLETOP_DEPTH_CM)):
            segments = rect_continuous_outline_segments(width, depth)
            self.assertEqual(len(segments), 4)
            self.assertTrue(all(min(item.width_td, item.depth_td) == 2.5 * TD_UNITS_PER_CM for item in segments))
        self.assertEqual(DEFAULT_TRACKING_MATERIAL_PATH, "/project1/comp_study_visualization/mat_tracking_table")

    def test_dedicated_tracking_material_is_white_without_mutating_study_material(self):
        phong_kind = object()

        class Parameters:
            def __init__(self): self.diffr = self.diffg = self.diffb = 0.0

        class Material:
            def __init__(self, name):
                self.name, self.path, self.par = name, f"/study/{name}", Parameters()
                self.nodeX = self.nodeY = 0

        class Parent:
            nodeX = nodeY = 0
            def __init__(self): self.by_name = {"mat_study_source": Material("mat_study_source")}
            def op(self, name): return self.by_name.get(name)
            def create(self, kind, name):
                self.assert_kind = kind
                material = Material(name)
                self.by_name[name] = material
                return material

        parent = Parent()
        from td_builders import tracking_table_outlines
        with patch.object(tracking_table_outlines, "op", lambda _path: parent, create=True), patch.object(
            tracking_table_outlines, "phongMAT", phong_kind, create=True
        ):
            material = create_tracking_table_material()
        self.assertEqual(material.name, "mat_tracking_table")
        self.assertEqual((material.par.diffr, material.par.diffg, material.par.diffb), (1.0, 1.0, 1.0))
        self.assertEqual(
            (parent.by_name["mat_study_source"].par.diffr, parent.by_name["mat_study_source"].par.diffg, parent.by_name["mat_study_source"].par.diffb),
            (0.0, 0.0, 0.0),
        )

    def test_existing_tracking_geometries_are_all_reassigned_to_dedicated_material(self):
        class Geometry:
            def __init__(self, name):
                self.path = f"/study/{name}"
                self.par = type("Parameters", (), {"material": "mat_study_source"})()

        class Parent:
            def __init__(self):
                self.by_name = {
                    name: Geometry(name)
                    for name in (*tracking_floor_geometry_names(), *tracking_tabletop_geometry_names())
                }
            def op(self, name): return self.by_name.get(name)

        parent = Parent()
        from td_builders import tracking_table_outlines
        with patch.object(tracking_table_outlines, "op", lambda _path: parent, create=True):
            geos = apply_tracking_table_material()
        self.assertEqual(len(geos), 12)
        self.assertTrue(all(geo.par.material == DEFAULT_TRACKING_MATERIAL_PATH for geo in geos))

    def test_transforms_use_safe_live_occupancy_channels_and_mirrored_rotation(self):
        tx, ty, rz = _live_tracking_transform_expressions("/raw", 3)
        self.assertIn("vision/table/3/x", tx)
        self.assertIn("250.0 - value.eval()", tx)
        self.assertIn("vision/table/3/y", ty)
        self.assertIn("value.eval() - 250.0", ty)
        self.assertIn("vision/table/3/rot", rz)
        self.assertIn("-(value.eval())", rz)

        class Missing:
            def __getitem__(self, _name): return None

        for expression in (tx, ty, rz):
            self.assertEqual(eval(expression, {"op": lambda _path: Missing()}), 0.0)

    def test_visibility_is_tracking_mode_count_and_availability_gated(self):
        expression = _tracking_visibility_expression("/raw", 4)
        self.assertIn("study/mode", expression)
        self.assertIn("== 0", expression)
        self.assertIn("vision/table/count", expression)
        self.assertIn("> 4", expression)
        self.assertIn("vision/table/4/available", expression)
        self.assertNotIn("study/phase", expression)
        self.assertNotIn("study/setup", expression)
        self.assertNotIn("study/tracked", expression)

    def test_render_mode_wrapper_replaces_only_tracking_mode_without_duplicate_paths(self):
        original = "old_study_and_aisi_expression()"
        paths = tracking_render_geometry_list(tabletop=False)
        expression = tracking_mode_render_expression(original, tracking_geometry_list=paths)
        self.assertIn(TRACKING_RENDER_SENTINEL, expression)
        self.assertIn("study/mode", expression)
        self.assertIn("== 0", expression)
        self.assertIn(original, expression)
        for name in tracking_floor_geometry_names():
            self.assertEqual(expression.count(name), 1)
        with self.assertRaises(ValueError):
            tracking_mode_render_expression(expression, tracking_geometry_list=paths)

    def test_render_configuration_routes_mode_zero_to_all_live_slots(self):
        class GeometryParameter:
            def __init__(self, expression): self.expr = expression
            def eval(self): return self.expr

        class Render:
            def __init__(self, path):
                self.path = path
                self.par = type("Parameters", (), {"geometry": GeometryParameter("legacy_mode_router()")})()

        floor, tabletop = Render("/floor"), Render("/tabletop")
        from td_builders import tracking_table_outlines
        with patch.object(
            tracking_table_outlines,
            "op",
            lambda path: {"/floor": floor, "/tabletop": tabletop}.get(path),
            create=True,
        ):
            configure_tracking_mode_render_paths(
                floor_render_path="/floor", tabletop_render_path="/tabletop"
            )
        for name in tracking_floor_geometry_names():
            self.assertEqual(floor.par.geometry.expr.count(name), 1)
        for name in tracking_tabletop_geometry_names():
            self.assertEqual(tabletop.par.geometry.expr.count(name), 1)
        self.assertIn("legacy_mode_router()", floor.par.geometry.expr)
        self.assertIn("legacy_mode_router()", tabletop.par.geometry.expr)


if __name__ == "__main__":
    unittest.main()
