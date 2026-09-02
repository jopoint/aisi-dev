import math
import unittest

from aisi.app.sim_room_editor import cycle_table_type, make_default_tables, scene_payload
from aisi.core.table_geometry import (
    TABLE_GEOMETRIES,
    TABLE_TYPE_IDS,
    allowed_table_center_bounds,
    clamp_table_center_to_roi,
    convex_polygons_intersect,
    get_table_geometry,
    polygon_inside_roi,
    project_polygon_onto_axis,
    rectangle_footprint,
    support_distance,
    transform_local_footprint,
    world_footprint,
)
from aisi.generation.layout_constraints import _obb_intersects


EXPECTED_FOOTPRINTS = {
    "summit": ((-80.0, -35.0), (80.0, -35.0), (51.0, 35.0), (-51.0, 35.0)),
    "sprint": ((-44.0, -30.0), (44.0, -30.0), (19.0, 30.0), (-19.0, 30.0)),
    "rect": ((-80.0, -40.0), (80.0, -40.0), (80.0, 40.0), (-80.0, 40.0)),
}


class TableGeometryTests(unittest.TestCase):
    def assert_points_close(self, actual, expected):
        self.assertEqual(len(actual), len(expected))
        for actual_point, expected_point in zip(actual, expected):
            self.assertAlmostEqual(actual_point[0], expected_point[0])
            self.assertAlmostEqual(actual_point[1], expected_point[1])

    def test_canonical_footprints_and_type_ids(self):
        self.assertEqual(TABLE_TYPE_IDS, {"summit": 0, "sprint": 1, "rect": 2})
        self.assertEqual(set(TABLE_GEOMETRIES), set(EXPECTED_FOOTPRINTS))
        for table_type, expected in EXPECTED_FOOTPRINTS.items():
            with self.subTest(table_type=table_type):
                self.assertEqual(get_table_geometry(table_type).local_footprint, expected)

    def test_footprint_transform_at_zero_ninety_and_one_eighty_degrees(self):
        for table_type, local in EXPECTED_FOOTPRINTS.items():
            with self.subTest(table_type=table_type, rotation_deg=0):
                self.assert_points_close(
                    transform_local_footprint(local, 10.0, 20.0, 0.0),
                    tuple((x + 10.0, y + 20.0) for x, y in local),
                )
            with self.subTest(table_type=table_type, rotation_deg=90):
                self.assert_points_close(
                    transform_local_footprint(local, 0.0, 0.0, 90.0),
                    tuple((-y, x) for x, y in local),
                )
            with self.subTest(table_type=table_type, rotation_deg=180):
                self.assert_points_close(
                    transform_local_footprint(local, 0.0, 0.0, 180.0),
                    tuple((-x, -y) for x, y in local),
                )

    def test_trapezoid_narrow_side_points_toward_positive_world_y_at_zero_degrees(self):
        for table_type in ("summit", "sprint"):
            with self.subTest(table_type=table_type):
                footprint = world_footprint(table_type, 0.0, 0.0, 0.0)
                negative_y_width = max(x for x, y in footprint if y < 0) - min(
                    x for x, y in footprint if y < 0
                )
                positive_y_width = max(x for x, y in footprint if y > 0) - min(
                    x for x, y in footprint if y > 0
                )
                self.assertLess(positive_y_width, negative_y_width)

    def test_projection_normalizes_axis(self):
        footprint = rectangle_footprint(10.0, 4.0)
        self.assertEqual(project_polygon_onto_axis(footprint, (2.0, 0.0)), (-5.0, 5.0))

    def test_trapezoid_support_reflects_narrow_and_wide_sides(self):
        diagonal_to_positive_y = (1.0, 1.0)
        diagonal_to_negative_y = (1.0, -1.0)
        for table_type in ("summit", "sprint"):
            with self.subTest(table_type=table_type):
                footprint = get_table_geometry(table_type).local_footprint
                self.assertEqual(
                    support_distance(footprint, (0.0, 1.0)),
                    support_distance(footprint, (0.0, -1.0)),
                )
                self.assertLess(
                    support_distance(footprint, diagonal_to_positive_y),
                    support_distance(footprint, diagonal_to_negative_y),
                )

    def test_rect_support_is_symmetric(self):
        footprint = get_table_geometry("rect").local_footprint
        for direction in ((1.0, 0.0), (0.0, 1.0), (1.0, 1.0)):
            with self.subTest(direction=direction):
                opposite = (-direction[0], -direction[1])
                self.assertAlmostEqual(
                    support_distance(footprint, direction),
                    support_distance(footprint, opposite),
                )

    def test_sat_distinguishes_separation_touching_and_overlap(self):
        first = rectangle_footprint(10.0, 4.0)
        separated = transform_local_footprint(first, 10.01, 0.0, 0.0)
        touching = transform_local_footprint(first, 10.0, 0.0, 0.0)
        overlapping = transform_local_footprint(first, 9.99, 0.0, 0.0)

        self.assertFalse(convex_polygons_intersect(first, separated))
        self.assertTrue(convex_polygons_intersect(first, touching))
        self.assertTrue(convex_polygons_intersect(first, overlapping))

    def test_sat_handles_different_rotations(self):
        first = world_footprint("rect", 100.0, 100.0, 0.0)
        rotated_overlap = world_footprint("rect", 180.0, 100.0, 45.0)
        rotated_separate = world_footprint("rect", 300.0, 100.0, 45.0)

        self.assertTrue(convex_polygons_intersect(first, rotated_overlap))
        self.assertFalse(convex_polygons_intersect(first, rotated_separate))

    def test_rect_sat_matches_existing_obb_semantics(self):
        cases = (
            ((0.0, 0.0), 0.0, (160.0, 0.0), 0.0),
            ((0.0, 0.0), 0.0, (160.01, 0.0), 0.0),
            ((0.0, 0.0), 30.0, (90.0, 25.0), -20.0),
            ((0.0, 0.0), 30.0, (300.0, 25.0), -20.0),
        )
        for center_a, rotation_a, center_b, rotation_b in cases:
            with self.subTest(
                center_a=center_a,
                rotation_a=rotation_a,
                center_b=center_b,
                rotation_b=rotation_b,
            ):
                polygon_result = convex_polygons_intersect(
                    world_footprint("rect", *center_a, rotation_a),
                    world_footprint("rect", *center_b, rotation_b),
                )
                obb_result = _obb_intersects(
                    center_a,
                    160.0,
                    80.0,
                    rotation_a,
                    center_b,
                    160.0,
                    80.0,
                    rotation_b,
                    0.0,
                )
                self.assertEqual(polygon_result, obb_result)

    def test_polygon_inside_roi_interior_boundary_and_outside(self):
        interior = rectangle_footprint(100.0, 50.0)
        interior = transform_local_footprint(interior, 250.0, 250.0, 0.0)
        on_boundary = world_footprint("rect", 80.0, 40.0, 0.0)
        outside = world_footprint("rect", 79.0, 40.0, 0.0)

        self.assertTrue(polygon_inside_roi(interior))
        self.assertTrue(polygon_inside_roi(on_boundary))
        self.assertFalse(polygon_inside_roi(outside))

    def test_allowed_center_bounds_for_rotated_rect(self):
        footprint = get_table_geometry("rect").local_footprint
        self.assertEqual(
            allowed_table_center_bounds(footprint, 0.0),
            (80.0, 40.0, 420.0, 460.0),
        )
        bounds_90 = allowed_table_center_bounds(footprint, 90.0)
        for actual, expected in zip(bounds_90, (40.0, 80.0, 460.0, 420.0)):
            self.assertAlmostEqual(actual, expected)

    def test_legacy_rectangle_footprint(self):
        self.assertEqual(
            rectangle_footprint(120.0, 50.0),
            ((-60.0, -25.0), (60.0, -25.0), (60.0, 25.0), (-60.0, 25.0)),
        )
        self.assertAlmostEqual(support_distance(rectangle_footprint(120.0, 50.0), (1.0, 1.0)), 85.0 / math.sqrt(2.0))

    def test_roi_clamping_keeps_complete_rotated_footprint_inside_room(self):
        for table_type in EXPECTED_FOOTPRINTS:
            for rotation_deg in (0.0, 45.0, 90.0, 180.0):
                with self.subTest(table_type=table_type, rotation_deg=rotation_deg):
                    x, y = clamp_table_center_to_roi(table_type, -100.0, 700.0, rotation_deg)
                    footprint = world_footprint(table_type, x, y, rotation_deg)
                    self.assertTrue(all(-1e-9 <= px <= 500.0 + 1e-9 for px, _ in footprint))
                    self.assertTrue(all(-1e-9 <= py <= 500.0 + 1e-9 for _, py in footprint))

    def test_room_editor_serializes_dimensions_from_canonical_geometry(self):
        tables = make_default_tables()
        tables[0]["width_cm"] = 133.0
        tables[0]["height_cm"] = 67.0

        serialized = scene_payload(tables, chairs=[], persons=[])["tables"]
        for table in serialized:
            geometry = get_table_geometry(table["type"])
            self.assertEqual(table["width_cm"], geometry.nominal_width)
            self.assertEqual(table["height_cm"], geometry.nominal_depth)

    def test_room_editor_type_change_preserves_id_and_rotation(self):
        table = make_default_tables()[0]
        table["x_cm"] = 250.0
        table["y_cm"] = 250.0
        table["rotation_deg"] = 37.0

        new_type = cycle_table_type(table)

        self.assertEqual(new_type, "sprint")
        self.assertEqual(table["id"], "table_0")
        self.assertEqual(table["rotation_deg"], 37.0)
        self.assertEqual((table["x_cm"], table["y_cm"]), (250.0, 250.0))


if __name__ == "__main__":
    unittest.main()
