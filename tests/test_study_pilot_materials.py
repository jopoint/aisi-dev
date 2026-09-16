import unittest

from td_builders.study_pilot_materials import (
    SOURCE_OUTLINE_GEOMETRIES,
    SOURCE_MATERIAL_NAME,
    TARGET_MATERIAL_NAME,
)


class StudyPilotMaterialTests(unittest.TestCase):
    def test_source_outlines_keep_the_existing_source_material_contract(self):
        self.assertEqual(SOURCE_MATERIAL_NAME, "mat_study_source")
        self.assertEqual(TARGET_MATERIAL_NAME, "mat_study_target")
        self.assertEqual(
            SOURCE_OUTLINE_GEOMETRIES,
            ("rect_tabletop_inner_outline_geo", "rect_floor_outer_outline_geo"),
        )
