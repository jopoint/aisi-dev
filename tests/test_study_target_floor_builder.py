"""Focused non-TouchDesigner checks for the Study floor target helper."""

import unittest

from td_builders.study_target_floor import (
    RECT_DEPTH_CM,
    RECT_WIDTH_CM,
    TD_UNITS_PER_CM,
    rect_target_floor_dash_segments,
)


class StudyTargetFloorBuilderTests(unittest.TestCase):
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
