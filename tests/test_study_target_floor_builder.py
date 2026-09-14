"""Focused non-TouchDesigner checks for the Study floor target helper."""

import unittest

from td_builders.study_target_floor import (
    RECT_DEPTH_CM,
    RECT_WIDTH_CM,
    TABLETOP_INNER_DEPTH_CM,
    TABLETOP_INNER_WIDTH_CM,
    TD_UNITS_PER_CM,
    STUDY_OVERLAP_CALLBACKS_DAT_SOURCE,
    STUDY_TABLETOP_VISIBILITY_CALLBACKS_DAT_SOURCE,
    _configure_pose_object_chop,
    _configure_visibility_export_chop,
    _configure_visibility_state_select_chop,
    _active_study_visibility_expression,
    _overlap_visibility_expression,
    _target_transform_expressions,
    study_tabletop_target_visible,
    target_world_to_td,
    rect_target_floor_dash_segments,
    rect_target_tabletop_dash_segments,
)


class StudyTargetFloorBuilderTests(unittest.TestCase):
    def test_tabletop_target_gate_hides_tracking_with_overlap(self) -> None:
        self.assertFalse(study_tabletop_target_visible(0, 1, 1.0))

    def test_tabletop_target_gate_hides_home_and_ready(self) -> None:
        self.assertFalse(study_tabletop_target_visible(1, 1, 1.0, 0))
        self.assertFalse(study_tabletop_target_visible(1, 1, 1.0, 1))

    def test_tabletop_target_gate_hides_study_floor_only_with_overlap(self) -> None:
        self.assertFalse(study_tabletop_target_visible(1, 0, 1.0))

    def test_tabletop_target_gate_hides_dual_surface_without_overlap(self) -> None:
        self.assertFalse(study_tabletop_target_visible(1, 1, 0.0))

    def test_tabletop_target_gate_shows_study_dual_surface_overlap(self) -> None:
        self.assertTrue(study_tabletop_target_visible(1, 1, 1.0))

    def test_tabletop_target_gate_hides_aisi_with_overlap(self) -> None:
        self.assertFalse(study_tabletop_target_visible(2, 1, 1.0))

    def test_tabletop_target_visibility_expression_reads_all_three_gate_inputs(self) -> None:
        expression = _overlap_visibility_expression(
            "/project1/comp_study_visualization/study_overlap_state",
            "/project1/comp_io/null_osc_raw",
        )

        self.assertIn("study_overlap_state", expression)
        self.assertIn("study_mode", expression)
        self.assertIn("study_condition", expression)
        self.assertIn("study_phase", expression)

    def test_floor_target_active_gate_requires_study_active(self) -> None:
        expression = _active_study_visibility_expression("/project1/comp_io/null_osc_raw")
        self.assertIn("study_mode", expression)
        self.assertIn("study_phase", expression)
        self.assertIn("== 2", expression)

    def test_target_transform_uses_the_same_td_axis_signs_as_source_geometry(self) -> None:
        source_x, source_y = 187.5914, 241.9824
        target_x, target_y = 187.5924, 241.9527

        source_td_x = (250.0 - source_x) * TD_UNITS_PER_CM
        source_td_y = (source_y - 250.0) * TD_UNITS_PER_CM
        target_td_x, target_td_y = target_world_to_td(target_x, target_y)

        self.assertAlmostEqual(target_td_x, source_td_x, delta=0.0002)
        self.assertAlmostEqual(target_td_y, source_td_y, delta=0.0002)
        self.assertGreater(target_td_x, 0.0)
        self.assertLess(target_td_y, 0.0)

    def test_target_transform_expressions_use_source_axis_signs(self) -> None:
        x_expr, y_expr, _ = _target_transform_expressions("/project1/comp_io/null_osc_raw")

        self.assertIn("250.0 - raw", x_expr)
        self.assertIn("raw['study/target_y'].eval() - 250.0", y_expr)
        self.assertNotIn("-((raw", y_expr)

    def test_target_transform_references_only_study_target_osc_channels(self) -> None:
        x_expr, y_expr, rot_expr = _target_transform_expressions("/project1/comp_io/null_osc_raw")
        expressions = " ".join((x_expr, y_expr, rot_expr))

        self.assertIn("study/target_x", expressions)
        self.assertIn("study/target_y", expressions)
        self.assertIn("study/target_rot", expressions)
        self.assertNotIn("table/0/target_", expressions)

    def test_pose_object_chop_has_native_geo_transform_dependencies(self) -> None:
        class Parameters:
            target = None
            reference = None
            compute = None
            nameformat = None
            outputrange = None

        class ObjectChop:
            path = "/study/study_source_pose"
            par = Parameters()

        chop = ObjectChop()
        _configure_pose_object_chop(chop, "/study/rect_floor_outer_geo", "/study")

        self.assertEqual(chop.par.target, "/study/rect_floor_outer_geo")
        self.assertEqual(chop.par.reference, "/study")
        self.assertEqual(chop.par.compute, "transform")
        self.assertEqual(chop.par.nameformat, "channel")
        self.assertEqual(chop.par.outputrange, "currentframe")

    def test_pose_object_chop_fails_clearly_when_the_td_api_is_incomplete(self) -> None:
        class ObjectChop:
            path = "/study/study_source_pose"

            class par:
                target = None

        with self.assertRaisesRegex(ValueError, "missing parameter\\(s\\): reference"):
            _configure_pose_object_chop(ObjectChop(), "/study/source", "/study")

    def test_visibility_callback_requires_active_study_dual_surface_and_overlap(self) -> None:
        namespace: dict[str, object] = {}
        exec(STUDY_TABLETOP_VISIBILITY_CALLBACKS_DAT_SOURCE, namespace)

        class Channel:
            def __init__(self, value: float) -> None:
                self.value = value

            def __len__(self) -> int:
                return 1

            def __getitem__(self, index: int) -> float:
                if index != 0:
                    raise AssertionError("unexpected sample index")
                return self.value

        class Input:
            def __init__(self, values: dict[str, float]) -> None:
                self.values = values

            def __getitem__(self, name: str):
                return Channel(self.values[name]) if name in self.values else None

        class Output:
            value = None

            def __setitem__(self, index: int, value: float) -> None:
                if index != 0:
                    raise AssertionError("unexpected sample index")
                self.value = value

        class ScriptOp:
            def __init__(self, values: dict[str, float]) -> None:
                self.inputs = [Input(values)]
                self.output = Output()

            def clear(self) -> None:
                return None

            def appendChan(self, name: str) -> Output:
                if name != "rect_target_tabletop_geo:sx":
                    raise AssertionError(f"unexpected output channel: {name}")
                return self.output

        on_cook = namespace["onCook"]
        for values, expected in (
            ({"study_mode": 0, "study_condition": 1, "study_phase": 2, "overlap": 1}, 0.0),
            ({"study_mode": 1, "study_condition": 0, "study_phase": 2, "overlap": 1}, 0.0),
            ({"study_mode": 1, "study_condition": 1, "study_phase": 1, "overlap": 1}, 0.0),
            ({"study_mode": 1, "study_condition": 1, "study_phase": 2, "overlap": 0}, 0.0),
            ({"study/mode": 1, "study/condition": 1, "study/phase": 2, "overlap": 1}, 1.0),
        ):
            script_op = ScriptOp(values)
            on_cook(script_op)
            self.assertEqual(script_op.output.value, expected)

    def test_visibility_export_uses_the_geo_parameter_channel_name(self) -> None:
        class Parameters:
            exportmethod = None
            autoexportroot = None

        class ExportChop:
            par = Parameters()
            export = False

        chop = ExportChop()
        _configure_visibility_export_chop(chop, "/project1/comp_study_visualization")
        self.assertEqual(chop.par.exportmethod, "autoname")
        self.assertEqual(chop.par.autoexportroot, "/project1/comp_study_visualization")
        self.assertTrue(chop.export)

    def test_visibility_state_select_reads_exactly_the_three_study_channels(self) -> None:
        class Parameters:
            chop = None
            channames = None

        class SelectChop:
            par = Parameters()

        chop = SelectChop()
        _configure_visibility_state_select_chop(chop, "/project1/comp_io/null_osc_raw")
        self.assertEqual(chop.par.chop, "/project1/comp_io/null_osc_raw")
        self.assertEqual(chop.par.channames, "study/mode study/condition study/phase")

    def test_overlap_state_callback_handles_missing_pose_channels(self) -> None:
        namespace: dict[str, object] = {}
        exec(STUDY_OVERLAP_CALLBACKS_DAT_SOURCE, namespace)

        class EmptyChop:
            def __getitem__(self, _name: str):
                return None

        class Parent:
            def op(self, name: str):
                return EmptyChop() if name in {"study_source_pose", "study_target_pose"} else None

        class OutputChannel:
            def __init__(self) -> None:
                self.value = None

            def __setitem__(self, index: int, value: float) -> None:
                self.assert_index(index)
                self.value = value

            @staticmethod
            def assert_index(index: int) -> None:
                if index != 0:
                    raise AssertionError("unexpected CHOP sample index")

        class ScriptOp:
            def __init__(self) -> None:
                self.output = OutputChannel()

            @staticmethod
            def parent() -> Parent:
                return Parent()

            @staticmethod
            def clear() -> None:
                return None

            def appendChan(self, name: str) -> OutputChannel:
                self.assertEqual(name, "overlap")
                return self.output

            def assertEqual(self, actual: str, expected: str) -> None:
                if actual != expected:
                    raise AssertionError(f"{actual!r} != {expected!r}")

        script_op = ScriptOp()
        namespace["onCook"](script_op)
        self.assertEqual(script_op.output.value, 0.0)

    def test_dashes_form_the_established_rect_footprint(self) -> None:
        segments = rect_target_floor_dash_segments()

        self.assertEqual(len(segments), 12)
        half_width = RECT_WIDTH_CM * TD_UNITS_PER_CM / 2.0
        half_depth = RECT_DEPTH_CM * TD_UNITS_PER_CM / 2.0
        for segment in segments:
            self.assertLessEqual(abs(segment.x_td) + segment.width_td / 2.0, half_width)
            self.assertLessEqual(abs(segment.y_td) + segment.depth_td / 2.0, half_depth)

    def test_dashes_cover_all_four_rect_sides(self) -> None:
        segments = rect_target_floor_dash_segments()
        half_width = RECT_WIDTH_CM * TD_UNITS_PER_CM / 2.0
        half_depth = RECT_DEPTH_CM * TD_UNITS_PER_CM / 2.0

        self.assertTrue(any(segment.y_td < -half_depth * 0.8 for segment in segments))
        self.assertTrue(any(segment.y_td > half_depth * 0.8 for segment in segments))
        self.assertTrue(any(segment.x_td < -half_width * 0.8 for segment in segments))
        self.assertTrue(any(segment.x_td > half_width * 0.8 for segment in segments))

    def test_tabletop_target_dashes_match_the_inner_contour_dimensions(self) -> None:
        segments = rect_target_tabletop_dash_segments()

        self.assertEqual(len(segments), 12)
        half_width = TABLETOP_INNER_WIDTH_CM * TD_UNITS_PER_CM / 2.0
        half_depth = TABLETOP_INNER_DEPTH_CM * TD_UNITS_PER_CM / 2.0
        for segment in segments:
            self.assertLessEqual(abs(segment.x_td) + segment.width_td / 2.0, half_width)
            self.assertLessEqual(abs(segment.y_td) + segment.depth_td / 2.0, half_depth)

    def test_overlap_state_callback_reuses_study_motion_overlap(self) -> None:
        self.assertIn("motion_math.module.rect_motion_segments", STUDY_OVERLAP_CALLBACKS_DAT_SOURCE)
        self.assertIn("values['overlap']", STUDY_OVERLAP_CALLBACKS_DAT_SOURCE)
        self.assertIn("scriptOp.appendChan('overlap')", STUDY_OVERLAP_CALLBACKS_DAT_SOURCE)
