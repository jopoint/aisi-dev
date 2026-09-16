import unittest

from td_builders.study_tabletop_brackets import (
    DEFAULT_OUTLINE_THICKNESS_CM,
    FLOOR_BRACKET_DEPTH_CM,
    FLOOR_BRACKET_WIDTH_CM,
    FLOOR_SOURCE_PADDING_CM,
    TD_UNITS_PER_CM,
    remove_default_primitives,
    rect_continuous_outline_segments,
    replace_geometry_path_once,
)


class StudySourceOutlineTests(unittest.TestCase):
    def test_tabletop_is_a_four_bar_continuous_150_by_70_cm_outline(self):
        segments = rect_continuous_outline_segments(150.0, 70.0)
        self.assertEqual(len(segments), 4)
        self.assertEqual({segment.side for segment in segments}, {"top", "bottom", "left", "right"})
        width_td, depth_td = 150.0 * TD_UNITS_PER_CM, 70.0 * TD_UNITS_PER_CM
        self.assertEqual(max(abs(segment.x_td) + segment.width_td / 2.0 for segment in segments), width_td / 2.0)
        self.assertEqual(max(abs(segment.y_td) + segment.depth_td / 2.0 for segment in segments), depth_td / 2.0)

    def test_outline_stroke_is_exactly_the_current_2p5_cm_bracket_stroke(self):
        self.assertEqual(DEFAULT_OUTLINE_THICKNESS_CM, 2.5)
        self.assertAlmostEqual(DEFAULT_OUTLINE_THICKNESS_CM * TD_UNITS_PER_CM, 0.013)
        for segment in rect_continuous_outline_segments(150.0, 70.0):
            thickness = min(segment.width_td, segment.depth_td)
            self.assertAlmostEqual(thickness, 0.013)

    def test_floor_source_outline_has_five_cm_padding_per_side(self):
        self.assertEqual(FLOOR_SOURCE_PADDING_CM, 5.0)
        self.assertEqual(FLOOR_BRACKET_WIDTH_CM, 170.0)
        self.assertEqual(FLOOR_BRACKET_DEPTH_CM, 90.0)
        segments = rect_continuous_outline_segments(FLOOR_BRACKET_WIDTH_CM, FLOOR_BRACKET_DEPTH_CM)
        self.assertEqual(len(segments), 4)

    def test_default_primitives_are_removed_before_authored_sops_render(self):
        class Primitive:
            def __init__(self, name):
                self.name = name
                self.destroyed = False

            def destroy(self):
                self.destroyed = True

        class Geo:
            def __init__(self, children):
                self.children = children

        torus, donut, sphere, intended = (Primitive(name) for name in ("torus1", "donut_debug", "sphere1", "merge_authored"))
        remove_default_primitives(Geo([torus, donut, sphere, intended]))
        self.assertTrue(torus.destroyed)
        self.assertTrue(donut.destroyed)
        self.assertTrue(sphere.destroyed)
        self.assertFalse(intended.destroyed)

    def test_render_path_replacement_refuses_duplicate_outline_paths(self):
        old = "/study/rect_floor_outer_brackets_geo"
        new = "/study/rect_floor_outer_outline_geo"
        updated = replace_geometry_path_once(f"'{old} /study/rect_target_floor_geo'", old, new)
        self.assertEqual(updated.count(new), 1)
        with self.assertRaises(ValueError):
            replace_geometry_path_once(updated, old, new)
