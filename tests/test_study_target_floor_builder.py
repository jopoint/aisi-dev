"""Focused non-TouchDesigner checks for the Study floor target helper."""

import unittest

from td_builders.study_target_floor import (
    RECT_DEPTH_CM,
    RECT_WIDTH_CM,
    TABLETOP_INNER_DEPTH_CM,
    TABLETOP_INNER_WIDTH_CM,
    TD_UNITS_PER_CM,
    STUDY_OVERLAP_CALLBACKS_DAT_SOURCE,
    _overlap_visibility_expression,
    _target_transform_expressions,
    study_tabletop_target_visible,
    study_pose_callbacks_dat_source,
    target_world_to_td,
    rect_target_floor_dash_segments,
    rect_target_tabletop_dash_segments,
)


class StudyTargetFloorBuilderTests(unittest.TestCase):
    def test_tabletop_target_gate_hides_tracking_with_overlap(self) -> None:
        self.assertFalse(study_tabletop_target_visible(0, 1, 1.0))

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

    def test_pose_script_callback_outputs_source_tx_ty_rz(self) -> None:
        callback_source = study_pose_callbacks_dat_source(
            "study_source_pose", "/source_geo", "study_target_pose", "/target_geo"
        )
        namespace: dict[str, object] = {}

        class Value:
            def __init__(self, value: float) -> None:
                self.value = value

            def eval(self) -> float:
                return self.value

        class Parameters:
            tx, ty, rz = Value(1.25), Value(-0.5), Value(37.0)

            def __getitem__(self, name: str) -> Value:
                return getattr(self, name)

        class Geo:
            par = Parameters()

        namespace["op"] = lambda path: Geo() if path == "/source_geo" else None
        exec(callback_source, namespace)

        class Channel:
            def __init__(self) -> None:
                self.value = None

            def __setitem__(self, index: int, value: float) -> None:
                self.assertEqual(index, 0)
                self.value = value

            def assertEqual(self, actual: int, expected: int) -> None:
                if actual != expected:
                    raise AssertionError("unexpected sample index")

        class ScriptOp:
            name = "study_source_pose"

            def __init__(self) -> None:
                self.channels: dict[str, Channel] = {}

            def clear(self) -> None:
                self.channels.clear()

            def appendChan(self, name: str) -> Channel:
                channel = Channel()
                self.channels[name] = channel
                return channel

        script_op = ScriptOp()
        namespace["onCook"](script_op)
        self.assertEqual(tuple(script_op.channels), ("tx", "ty", "rz"))
        self.assertEqual([channel.value for channel in script_op.channels.values()], [1.25, -0.5, 37.0])

    def test_pose_script_callback_outputs_zeroes_when_target_geo_is_missing(self) -> None:
        callback_source = study_pose_callbacks_dat_source(
            "study_source_pose", "/source_geo", "study_target_pose", "/target_geo"
        )
        namespace: dict[str, object] = {"op": lambda _path: None}
        exec(callback_source, namespace)

        class Channel:
            def __init__(self) -> None:
                self.value = None

            def __setitem__(self, index: int, value: float) -> None:
                if index != 0:
                    raise AssertionError("unexpected sample index")
                self.value = value

        class ScriptOp:
            name = "study_target_pose"

            def __init__(self) -> None:
                self.channels: dict[str, Channel] = {}

            def clear(self) -> None:
                self.channels.clear()

            def appendChan(self, name: str) -> Channel:
                channel = Channel()
                self.channels[name] = channel
                return channel

        script_op = ScriptOp()
        namespace["onCook"](script_op)
        self.assertEqual(tuple(script_op.channels), ("tx", "ty", "rz"))
        self.assertEqual([channel.value for channel in script_op.channels.values()], [0.0, 0.0, 0.0])

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
