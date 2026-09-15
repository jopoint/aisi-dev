"""Focused non-TouchDesigner checks for Study HOME setup table masks."""

import unittest
from unittest.mock import patch

from td_builders import study_setup_masks
from td_builders.study_setup_masks import (
    DEFAULT_TABLE_SURFACE_PATH,
    SETUP_MASK_COUNT,
    create_study_setup_mask_geos,
    setup_mask_geometry_names,
    _setup_mask_transform_expressions,
    _setup_mask_visibility_expression,
    study_setup_mask_render_geometry_expression,
)
class StudySetupMasksBuilderTests(unittest.TestCase):
    def test_builder_creates_six_filled_setup_mask_geometries(self) -> None:
        class Parameter:
            def __init__(self) -> None:
                self.expr = ""

        class GeometryParameters:
            def __init__(self) -> None:
                self.tx = Parameter()
                self.ty = Parameter()
                self.rz = Parameter()
                self.sx = Parameter()

        class SelectParameters:
            sops = None

        class Node:
            def __init__(self, kind) -> None:
                self.kind = kind
                self.par = SelectParameters() if kind is select_sop_kind else GeometryParameters()
                self.display = False
                self.render = False
                self.nodeX = 0
                self.nodeY = 0
                self.children = []

            def create(self, kind, _name):
                child = Node(kind)
                self.children.append(child)
                return child

        geometry_kind = object()
        select_sop_kind = object()

        class Parent(Node):
            def __init__(self) -> None:
                super().__init__(geometry_kind)
                self.nodeX = 10
                self.nodeY = 20
                self.by_name = {}

            def create(self, kind, name):
                child = Node(kind)
                self.by_name[name] = child
                return child

            def op(self, name):
                return self.by_name.get(name)

        parent = Parent()
        with patch.object(study_setup_masks, "op", lambda _path: parent, create=True), patch.object(
            study_setup_masks, "geometryCOMP", geometry_kind, create=True
        ), patch.object(study_setup_masks, "selectSOP", select_sop_kind, create=True):
            geos = create_study_setup_mask_geos("/project1/comp_study_visualization")

        self.assertEqual(len(geos), 6)
        self.assertEqual(tuple(parent.by_name), setup_mask_geometry_names())
        self.assertTrue(all(geo.children[0].par.sops == DEFAULT_TABLE_SURFACE_PATH for geo in geos))

    def test_six_fixed_capacity_setup_mask_geometries_are_named_by_index(self) -> None:
        names = setup_mask_geometry_names()
        self.assertEqual(len(names), SETUP_MASK_COUNT)
        self.assertEqual(names[0], "rect_setup_mask_geo_00")
        self.assertEqual(names[-1], "rect_setup_mask_geo_05")
        self.assertEqual(DEFAULT_TABLE_SURFACE_PATH, "../rect_tabletop_inner_geo/table_surface")

    def test_setup_mask_pose_uses_mirrored_world_to_td_axes_and_rotation(self) -> None:
        x_expr, y_expr, rz_expr = _setup_mask_transform_expressions(
            "/project1/comp_io/null_osc_raw", 4
        )
        self.assertIn("study/setup_table/4/x", x_expr)
        self.assertIn("250.0 - channel.eval()", x_expr)
        self.assertIn("study/setup_table/4/y", y_expr)
        self.assertIn("channel.eval() - 250.0", y_expr)
        self.assertIn("study/setup_table/4/rot", rz_expr)
        self.assertIn("-(channel.eval())", rz_expr)
        self.assertIn("study/tracked_table/4/x", x_expr)
        self.assertIn("study/tracked_table/4/y", y_expr)
        self.assertIn("study/tracked_table/4/rot", rz_expr)

    def test_unused_setup_mask_channels_default_to_safe_zero_transforms(self) -> None:
        class MissingChannels:
            def __getitem__(self, _channel_name):
                return None

        for expression in _setup_mask_transform_expressions(
            "/project1/comp_io/null_osc_raw", 5
        ):
            self.assertEqual(eval(expression, {"op": lambda _path: MissingChannels()}), 0.0)

    def test_setup_mask_visibility_is_study_home_ready_and_count_gated(self) -> None:
        expression = _setup_mask_visibility_expression("/project1/comp_io/null_osc_raw", 5)
        self.assertIn("study/mode", expression)
        self.assertIn("study/phase", expression)
        self.assertIn("in (0, 1)", expression)
        self.assertIn("study/setup_table_count", expression)
        self.assertIn("> 5", expression)
        self.assertIn("study/tracked_table/count", expression)
        self.assertIn("study/tracked_table/5/available", expression)

    def test_mask_render_uses_all_study_setup_masks_for_all_study_phases(self) -> None:
        expression = study_setup_mask_render_geometry_expression()
        for name in setup_mask_geometry_names():
            self.assertIn(f"/project1/comp_study_visualization/{name}", expression)
        self.assertIn("study/mode", expression)
        self.assertNotIn("study/phase", expression)

    def test_mask_render_keeps_tracking_mask_for_active_and_non_study(self) -> None:
        expression = study_setup_mask_render_geometry_expression()
        self.assertIn("/project1/comp_tracking_only/rect_table_mask_geo", expression)


if __name__ == "__main__":
    unittest.main()
