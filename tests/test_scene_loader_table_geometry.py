from __future__ import annotations

import math
import unittest

from aisi.app.sim_layout_rules import _normalize_scene_for_aisi
from aisi.core.table_geometry import TABLE_GEOMETRIES, resolve_table_state_geometry
from aisi.input.scene_loader import build_scene_state_from_dict


def _scene_with_tables(tables: list[dict[str, object]]) -> dict[str, object]:
    return {
        "roi": {"x_min": 0.0, "y_min": 0.0, "x_max": 500.0, "y_max": 500.0},
        "tables": tables,
    }


class SceneLoaderTableGeometryTests(unittest.TestCase):
    def test_known_types_use_canonical_geometry_and_preserve_pose(self) -> None:
        raw_tables = [
            {
                "id": f"table_{index}",
                "type": f" {table_type.upper()} ",
                "x": 10.0 + index,
                "y": 20.0 + index,
                "rot_deg": 30.0 + index,
                "width": 1.0,
                "height": 2.0,
            }
            for index, table_type in enumerate(("summit", "sprint", "rect"))
        ]

        scene = build_scene_state_from_dict(_scene_with_tables(raw_tables), "input")

        for index, table in enumerate(scene.tables):
            expected_type = ("summit", "sprint", "rect")[index]
            expected_geometry = TABLE_GEOMETRIES[expected_type]
            resolved = resolve_table_state_geometry(table)
            self.assertEqual(table.table_id, f"table_{index}")
            self.assertEqual(table.table_type, expected_type)
            self.assertEqual((table.x, table.y, table.rot_deg), (10.0 + index, 20.0 + index, 30.0 + index))
            self.assertEqual(table.width, expected_geometry.nominal_width)
            self.assertEqual(table.height, expected_geometry.nominal_depth)
            self.assertEqual(resolved.local_footprint, expected_geometry.local_footprint)
            self.assertAlmostEqual(
                resolved.characteristic_diagonal,
                math.hypot(expected_geometry.nominal_width, expected_geometry.nominal_depth),
            )

    def test_type_free_legacy_table_uses_explicit_dimensions_as_rectangle(self) -> None:
        scene = build_scene_state_from_dict(
            _scene_with_tables([{"id": "legacy", "x": 5.0, "y": 6.0, "width": 120.0, "height": 50.0}]),
            "input",
        )

        table = scene.tables[0]
        resolved = resolve_table_state_geometry(table)
        self.assertIsNone(table.table_type)
        self.assertEqual((table.width, table.height), (120.0, 50.0))
        self.assertEqual(
            resolved.local_footprint,
            ((-60.0, -25.0), (60.0, -25.0), (60.0, 25.0), (-60.0, 25.0)),
        )
        self.assertEqual((resolved.nominal_width, resolved.nominal_depth), (120.0, 50.0))
        self.assertAlmostEqual(resolved.characteristic_diagonal, math.hypot(120.0, 50.0))

    def test_unknown_type_remains_identifiable_and_uses_legacy_rectangle(self) -> None:
        scene = build_scene_state_from_dict(
            _scene_with_tables([{"type": " Custom ", "width": 90.0, "depth": 40.0}]),
            "input",
        )

        table = scene.tables[0]
        resolved = resolve_table_state_geometry(table)
        self.assertEqual(table.table_type, "custom")
        self.assertEqual((resolved.nominal_width, resolved.nominal_depth), (90.0, 40.0))

    def test_fully_missing_legacy_geometry_preserves_existing_default(self) -> None:
        scene = build_scene_state_from_dict(_scene_with_tables([{"id": "old"}]), "input")

        table = scene.tables[0]
        self.assertIsNone(table.table_type)
        self.assertEqual((table.width, table.height), (110.0, 70.0))

    def test_sim_normalization_preserves_type_id_order_and_maps_fields(self) -> None:
        source = _scene_with_tables(
            [
                {
                    "id": "b",
                    "type": "sprint",
                    "x_cm": 12.0,
                    "y_cm": 34.0,
                    "rotation_deg": 56.0,
                    "width_cm": 999.0,
                    "height_cm": 998.0,
                },
                {"id": "a", "type": "rect", "x_cm": 78.0, "y_cm": 90.0},
            ]
        )

        normalized = _normalize_scene_for_aisi(source)
        tables = normalized["tables"]

        self.assertEqual([table["id"] for table in tables], ["b", "a"])
        self.assertEqual([table["type"] for table in tables], ["sprint", "rect"])
        self.assertEqual((tables[0]["x"], tables[0]["y"], tables[0]["rot_deg"]), (12.0, 34.0, 56.0))

        loaded = build_scene_state_from_dict(normalized, "input")
        self.assertEqual([table.table_id for table in loaded.tables], ["b", "a"])
        self.assertEqual([table.table_type for table in loaded.tables], ["sprint", "rect"])
        self.assertEqual((loaded.tables[0].x, loaded.tables[0].y, loaded.tables[0].rot_deg), (12.0, 34.0, 56.0))
        self.assertEqual((loaded.tables[0].width, loaded.tables[0].height), (88.0, 60.0))


if __name__ == "__main__":
    unittest.main()
