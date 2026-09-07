import unittest

from aisi.app.sim_room_editor import (
    CHAIR_RADIUS_CM,
    PERSON_RADIUS_CM,
    SimRoomEditor,
    make_added_circle_item,
    make_added_table,
    make_default_chairs,
    make_default_persons,
    make_default_tables,
    scene_payload,
)
from aisi.core.table_geometry import get_table_geometry, polygon_inside_roi, world_footprint


class SimRoomEditorAuthoringTests(unittest.TestCase):
    def test_added_table_is_rect_with_canonical_geometry_and_valid_footprint(self):
        tables = make_default_tables()

        table = make_added_table(tables)

        geometry = get_table_geometry("rect")
        self.assertEqual(table["id"], "table_4")
        self.assertEqual(table["type"], "rect")
        self.assertEqual(table["width_cm"], geometry.nominal_width)
        self.assertEqual(table["height_cm"], geometry.nominal_depth)
        self.assertTrue(polygon_inside_roi(world_footprint("rect", table["x_cm"], table["y_cm"], 0.0)))

    def test_added_objects_use_monotonic_ids_after_removal(self):
        tables = make_default_tables()
        chairs = make_default_chairs()
        persons = make_default_persons()
        del tables[1]
        del chairs[1]
        del persons[1]

        self.assertEqual(make_added_table(tables)["id"], "table_4")
        self.assertEqual(make_added_circle_item(chairs, "chair", CHAIR_RADIUS_CM)["id"], "chair_4")
        self.assertEqual(make_added_circle_item(persons, "person", PERSON_RADIUS_CM)["id"], "person_4")

    def test_additions_append_and_serialization_preserves_remaining_order(self):
        tables = make_default_tables()
        chairs = make_default_chairs()
        persons = make_default_persons()
        del tables[1]
        del chairs[1]
        del persons[1]
        tables.append(make_added_table(tables))
        chairs.append(make_added_circle_item(chairs, "chair", CHAIR_RADIUS_CM))
        persons.append(make_added_circle_item(persons, "person", PERSON_RADIUS_CM))

        payload = scene_payload(tables, chairs, persons)

        self.assertEqual([item["id"] for item in payload["tables"]], ["table_0", "table_2", "table_3", "table_4"])
        self.assertEqual([item["id"] for item in payload["chairs"]], ["chair_0", "chair_2", "chair_3", "chair_4"])
        self.assertEqual([item["id"] for item in payload["persons"]], ["person_0", "person_2", "person_3", "person_4"])

    def test_remove_selected_only_deletes_the_selected_object(self):
        for kind, selected_id in (("table", "table_1"), ("chair", "chair_1"), ("person", "person_1")):
            with self.subTest(kind=kind):
                editor = object.__new__(SimRoomEditor)
                editor.tables = make_default_tables()
                editor.chairs = make_default_chairs()
                editor.persons = make_default_persons()
                editor.selected_kind = kind
                editor.selected_id = selected_id
                editor.dragging = True
                editor.save_now = lambda: None
                editor.redraw = lambda: None

                editor.remove_selected()

                expected_ids = [f"{kind}_{index}" for index in (0, 2, 3)]
                items = getattr(editor, f"{kind}s" if kind != "person" else "persons")
                self.assertEqual([item["id"] for item in items], expected_ids)
                self.assertIsNone(editor.selected_kind)
                self.assertIsNone(editor.selected_id)
                self.assertFalse(editor.dragging)

    def test_editor_add_remove_cycles_do_not_reuse_ids(self):
        for kind, add_method, next_number_attr in (
            ("table", "add_table", "next_table_number"),
            ("chair", "add_chair", "next_chair_number"),
            ("person", "add_person", "next_person_number"),
        ):
            with self.subTest(kind=kind):
                editor = object.__new__(SimRoomEditor)
                editor.tables = make_default_tables()
                editor.chairs = make_default_chairs()
                editor.persons = make_default_persons()
                editor.next_table_number = 4
                editor.next_chair_number = 4
                editor.next_person_number = 4
                editor.selected_kind = None
                editor.selected_id = None
                editor.dragging = False
                editor.save_now = lambda: None
                editor.redraw = lambda: None

                getattr(editor, add_method)()
                items = getattr(editor, f"{kind}s" if kind != "person" else "persons")
                self.assertEqual(items[-1]["id"], f"{kind}_4")
                editor.remove_selected()
                getattr(editor, add_method)()

                self.assertEqual(items[-1]["id"], f"{kind}_5")
                self.assertEqual(getattr(editor, next_number_attr), 6)


if __name__ == "__main__":
    unittest.main()
