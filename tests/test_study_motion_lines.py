"""Focused geometry checks for isolated Study motion-line math."""

import unittest
import math

from td_builders.study_motion_lines import (
    ARRIVAL_TRANSLATION_TOLERANCE_CM,
    ARRIVAL_TRANSLATION_TOLERANCE_TD,
    MIN_VISIBLE_LENGTH_TD,
    MOTION_MATH_DAT_SOURCE,
    RECT_DEPTH_TD,
    RECT_WIDTH_TD,
    TABLETOP_INNER_DEPTH_TD,
    TABLETOP_INNER_WIDTH_TD,
    _active_study_visibility_expression,
    rect_motion_segments,
)


class StudyMotionLineTests(unittest.TestCase):
    def test_motion_visibility_gate_requires_study_active_phase(self) -> None:
        expression = _active_study_visibility_expression("/project1/comp_io/null_osc_raw")
        self.assertIn("study_mode", expression)
        self.assertIn("study_phase", expression)
        self.assertIn("== 2", expression)

    def test_arrival_translation_tolerance_is_eight_cm(self) -> None:
        self.assertEqual(ARRIVAL_TRANSLATION_TOLERANCE_CM, 8.0)

    def test_floor_motion_connects_unrotated_rect_edges(self) -> None:
        values = rect_motion_segments(0.0, 0.0, 0.0, 2.0, 0.0, 0.0)

        half_width = RECT_WIDTH_TD / 2.0
        self.assertAlmostEqual(values["floor_start_x"], half_width)
        self.assertAlmostEqual(values["floor_start_y"], 0.0)
        self.assertAlmostEqual(values["floor_length"], 2.0 - 2.0 * half_width)
        self.assertAlmostEqual(
            values["floor_start_x"] + values["floor_length"], 2.0 - half_width
        )
        self.assertEqual(values["floor_visible"], 1.0)
        self.assertEqual(values["floor_arrow_visible"], 1.0)
        self.assertEqual(values["tabletop_arrow_visible"], 1.0)
        self.assertAlmostEqual(values["floor_arrow_tip_x"], 2.0 - half_width)
        self.assertAlmostEqual(values["floor_arrow_tip_y"], 0.0)
        self.assertAlmostEqual(values["tabletop_arrow_tip_x"], TABLETOP_INNER_WIDTH_TD / 2.0)
        self.assertAlmostEqual(values["tabletop_arrow_tip_y"], 0.0)
        self.assertAlmostEqual(values["angle_deg"], 0.0)
        self.assertAlmostEqual(values["tabletop_length"], TABLETOP_INNER_WIDTH_TD / 2.0)
        self.assertEqual(values["tabletop_visible"], 1.0)

    def test_rotation_uses_actual_short_rect_side_for_edge(self) -> None:
        values = rect_motion_segments(0.0, 0.0, 90.0, 2.0, 0.0, 0.0)

        self.assertAlmostEqual(values["floor_start_x"], RECT_DEPTH_TD / 2.0)
        self.assertAlmostEqual(values["tabletop_length"], TABLETOP_INNER_DEPTH_TD / 2.0)

    def test_target_inside_inner_contour_ends_at_target_center(self) -> None:
        values = rect_motion_segments(0.0, 0.0, 0.0, 0.2, 0.0, 0.0)

        self.assertEqual(values["floor_length"], 0.0)
        self.assertEqual(values["floor_visible"], 0.0)
        self.assertEqual(values["overlap"], 1.0)
        self.assertEqual(values["tabletop_visible"], 1.0)
        self.assertEqual(values["floor_arrow_visible"], 0.0)
        self.assertEqual(values["tabletop_arrow_visible"], 1.0)
        self.assertAlmostEqual(values["tabletop_length"], 0.2)
        self.assertAlmostEqual(values["tabletop_arrow_tip_x"], 0.2)
        self.assertAlmostEqual(values["tabletop_arrow_tip_y"], 0.0)
        self.assertAlmostEqual(values["angle_deg"], 0.0)

    def test_target_outside_inner_contour_ends_at_inner_support(self) -> None:
        values = rect_motion_segments(0.0, 0.0, 0.0, 2.0, 0.0, 0.0)

        self.assertEqual(values["overlap"], 0.0)
        self.assertAlmostEqual(values["tabletop_length"], TABLETOP_INNER_WIDTH_TD / 2.0)
        self.assertAlmostEqual(values["tabletop_arrow_tip_x"], TABLETOP_INNER_WIDTH_TD / 2.0)

    def test_zero_translation_hides_both_segments(self) -> None:
        values = rect_motion_segments(1.0, 2.0, 33.0, 1.0, 2.0, 33.0)

        self.assertEqual(values["floor_visible"], 0.0)
        self.assertEqual(values["tabletop_visible"], 0.0)
        self.assertEqual(values["floor_arrow_visible"], 0.0)
        self.assertEqual(values["tabletop_arrow_visible"], 0.0)
        self.assertEqual(values["arrived"], 1.0)
        self.assertEqual(values["overlap"], 1.0)
        self.assertLessEqual(values["floor_length"], MIN_VISIBLE_LENGTH_TD)

    def test_almost_arrived_pose_hides_all_motion(self) -> None:
        values = rect_motion_segments(
            0.0, 0.0, 0.0, ARRIVAL_TRANSLATION_TOLERANCE_TD * 0.9, 0.0, 4.0
        )

        self.assertEqual(values["arrived"], 1.0)
        self.assertEqual(values["floor_visible"], 0.0)
        self.assertEqual(values["tabletop_visible"], 0.0)
        self.assertEqual(values["floor_arrow_visible"], 0.0)
        self.assertEqual(values["tabletop_arrow_visible"], 0.0)

    def test_translation_just_outside_arrival_tolerance_shows_motion(self) -> None:
        values = rect_motion_segments(
            0.0, 0.0, 0.0, ARRIVAL_TRANSLATION_TOLERANCE_TD + 0.001, 0.0, 0.0
        )

        self.assertEqual(values["arrived"], 0.0)
        self.assertEqual(values["overlap"], 1.0)
        self.assertEqual(values["tabletop_visible"], 1.0)
        self.assertEqual(values["tabletop_arrow_visible"], 1.0)

    def test_rotation_just_outside_arrival_tolerance_shows_motion(self) -> None:
        values = rect_motion_segments(0.0, 0.0, 0.0, 0.02, 0.0, 6.0)

        self.assertEqual(values["arrived"], 0.0)
        self.assertEqual(values["tabletop_visible"], 1.0)
        self.assertEqual(values["tabletop_arrow_visible"], 1.0)

    def test_rotated_overlapping_tabletop_arrow_uses_target_center_direction(self) -> None:
        source_x, source_y, source_rotation = 0.0, 0.0, 35.0
        target_x, target_y = 0.30, 0.20
        values = rect_motion_segments(
            source_x, source_y, source_rotation, target_x, target_y, -20.0
        )

        direction_x = target_x - source_x
        direction_y = target_y - source_y
        direction_length = math.hypot(direction_x, direction_y)
        direction_x /= direction_length
        direction_y /= direction_length
        endpoint_x = values["tabletop_arrow_tip_x"] - source_x
        endpoint_y = values["tabletop_arrow_tip_y"] - source_y

        self.assertEqual(values["overlap"], 1.0)
        self.assertEqual(values["floor_visible"], 0.0)
        self.assertEqual(values["tabletop_arrow_visible"], 1.0)
        self.assertAlmostEqual(endpoint_x * direction_y - endpoint_y * direction_x, 0.0)
        self.assertGreater(endpoint_x * direction_x + endpoint_y * direction_y, 0.0)
        self.assertAlmostEqual(values["tabletop_arrow_tip_x"], target_x)
        self.assertAlmostEqual(values["tabletop_arrow_tip_y"], target_y)
        self.assertAlmostEqual(values["tabletop_angle_deg"], math.degrees(math.atan2(direction_y, direction_x)))

    def test_source_local_td_composition_restores_world_target_direction(self) -> None:
        source_x, source_y, source_rotation = 0.0, 0.0, 60.0
        target_x, target_y = 0.28, 0.22
        values = rect_motion_segments(
            source_x, source_y, source_rotation, target_x, target_y, -15.0
        )

        world_direction_x = target_x - source_x
        world_direction_y = target_y - source_y
        world_direction_length = math.hypot(world_direction_x, world_direction_y)
        world_direction_x /= world_direction_length
        world_direction_y /= world_direction_length
        local_angle = math.radians(values["tabletop_local_angle_deg"])
        comp_rotation = math.radians(values["tabletop_comp_rotation_deg"])
        final_world_x = (
            math.cos(comp_rotation) * math.cos(local_angle)
            - math.sin(comp_rotation) * math.sin(local_angle)
        )
        final_world_y = (
            math.sin(comp_rotation) * math.cos(local_angle)
            + math.cos(comp_rotation) * math.sin(local_angle)
        )

        self.assertEqual(values["overlap"], 1.0)
        self.assertAlmostEqual(final_world_x * world_direction_y - final_world_y * world_direction_x, 0.0)
        self.assertGreater(final_world_x * world_direction_x + final_world_y * world_direction_y, 0.0)

    def test_arrow_direction_tracks_diagonal_source_to_target_motion(self) -> None:
        values = rect_motion_segments(0.0, 0.0, 0.0, 2.0, 2.0, 90.0)

        self.assertEqual(values["floor_arrow_visible"], 1.0)
        self.assertEqual(values["tabletop_arrow_visible"], 1.0)
        self.assertAlmostEqual(values["angle_deg"], 45.0)
        self.assertGreater(values["floor_arrow_tip_x"], values["floor_start_x"])
        self.assertGreater(values["floor_arrow_tip_y"], values["floor_start_y"])

    def test_embedded_td_math_matches_arrow_selection(self) -> None:
        namespace: dict[str, object] = {}
        exec(MOTION_MATH_DAT_SOURCE, namespace)
        td_values = namespace["rect_motion_segments"](0.0, 0.0, 0.0, 0.2, 0.0, 0.0)

        self.assertEqual(td_values["floor_arrow_visible"], 0.0)
        self.assertEqual(td_values["tabletop_arrow_visible"], 1.0)

    def test_embedded_td_math_reports_overlap_at_arrival_for_target_visibility(self) -> None:
        namespace: dict[str, object] = {}
        exec(MOTION_MATH_DAT_SOURCE, namespace)
        td_values = namespace["rect_motion_segments"](0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

        self.assertEqual(td_values["arrived"], 1.0)
        self.assertEqual(td_values["overlap"], 1.0)
        self.assertEqual(td_values["tabletop_visible"], 0.0)
