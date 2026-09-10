"""Focused non-TouchDesigner checks for the Study HOME/READY start helper."""

import unittest
import inspect

from td_builders.study_start_pose import (
    RECT_DEPTH_CM,
    RECT_WIDTH_CM,
    TD_UNITS_PER_CM,
    _create_setup_table_geo,
    _marker_value_expression,
    _home_ready_visibility_expression,
    _setup_table_transform_expressions,
    rect_start_floor_solid_segments,
)


class StudyStartPoseBuilderTests(unittest.TestCase):
    def test_start_contour_uses_the_canonical_outer_rect_dimensions(self) -> None:
        segments = rect_start_floor_solid_segments()
        self.assertEqual(len(segments), 4)
        self.assertAlmostEqual(max(segment.x_td + segment.width_td / 2 for segment in segments), RECT_WIDTH_CM * TD_UNITS_PER_CM / 2)
        self.assertAlmostEqual(min(segment.y_td - segment.depth_td / 2 for segment in segments), -RECT_DEPTH_CM * TD_UNITS_PER_CM / 2)

    def test_every_setup_table_uses_the_same_neutral_list_contract(self) -> None:
        expressions = " ".join(_setup_table_transform_expressions("/project1/comp_io/null_osc_raw", 0))
        self.assertIn("study/setup_table/0/x", expressions)
        self.assertIn("study/setup_table/0/y", expressions)
        self.assertIn("study/setup_table/0/rot", expressions)
        self.assertNotIn("study/source", expressions)
        self.assertNotIn("table/0/source", expressions)
        self.assertIn("250.0 - raw", expressions)

    def test_index_three_reads_its_own_slash_named_setup_table_channels(self) -> None:
        expressions = _setup_table_transform_expressions("/project1/comp_io/null_osc_raw", 3)
        self.assertIn("study/setup_table/3/x", expressions[0])
        self.assertIn("study/setup_table/3/y", expressions[1])
        self.assertIn("study/setup_table/3/rot", expressions[2])

    def test_additional_setup_table_poses_never_reference_index_zero_or_fallback_channels(self) -> None:
        for index in (1, 2):
            expressions = " ".join(_setup_table_transform_expressions("/project1/comp_io/null_osc_raw", index))
            self.assertIn(f"study/setup_table/{index}/x", expressions)
            self.assertIn(f"study/setup_table/{index}/y", expressions)
            self.assertIn(f"study/setup_table/{index}/rot", expressions)
            self.assertNotIn("study/setup_table/0/", expressions)
            self.assertIn("else 0.0", expressions)

    def test_visibility_gate_is_home_or_ready_in_study_only(self) -> None:
        expression = _home_ready_visibility_expression(
            "/project1/comp_io/null_osc_raw", "study/setup_table_count", 2
        )
        self.assertIn("study/mode", expression)
        self.assertIn("study/phase", expression)
        self.assertNotIn("study_mode", expression)
        self.assertNotIn("study_phase", expression)
        self.assertIn("in (0, 1)", expression)
        self.assertIn("study/setup_table_count", expression)
        self.assertIn("> 2", expression)

    def test_visibility_expression_has_the_expected_count_boundary_for_all_setup_indices(self) -> None:
        expressions = [
            _home_ready_visibility_expression(
                "/project1/comp_io/null_osc_raw", "study/setup_table_count", index
            )
            for index in range(6)
        ]
        for index, expression in enumerate(expressions):
            self.assertIn(f"> {index}", expression)
            self.assertIn("study/setup_table_count", expression)

    def test_participant_marker_uses_only_the_neutral_marker_contract(self) -> None:
        expression = _marker_value_expression(
            "/project1/comp_io/null_osc_raw", 1, "radius", cm_to_td=True,
            clamp_positive=True,
        )
        self.assertIn("study/participant_start/1/radius", expression)
        self.assertIn("max(", expression)
        self.assertIn(str(TD_UNITS_PER_CM), expression)

    def test_participant_marker_position_uses_the_study_world_to_td_axes(self) -> None:
        x_expression = _marker_value_expression(
            "/project1/comp_io/null_osc_raw", 0, "x", world_axis="x"
        )
        y_expression = _marker_value_expression(
            "/project1/comp_io/null_osc_raw", 0, "y", world_axis="y"
        )
        self.assertIn("250.0 -", x_expression)
        self.assertIn("- 250.0", y_expression)

    def test_table_setup_builder_has_no_index_zero_style_branch(self) -> None:
        """Index zero may have a legacy name, never a distinct visual style."""

        implementation = inspect.getsource(_create_setup_table_geo)
        self.assertNotIn("index == 0", implementation)
        self.assertIn("rect_start_floor_solid_segments()", implementation)
        self.assertIn("material_path", implementation)

    def test_factory_keeps_operator_suffixes_coupled_to_osc_indices(self) -> None:
        from td_builders import study_start_pose

        implementation = inspect.getsource(study_start_pose.create_study_home_setup_geos)
        self.assertIn("rect_setup_floor_geo_{index:02d}", implementation)
        self.assertIn("for name, index in table_specs", implementation)
