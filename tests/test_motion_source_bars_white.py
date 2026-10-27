import ast
from pathlib import Path
import unittest
from td_builders import update_motion_source_bars_white as update
from td_builders import update_motion_feedback_size_cutouts as cutouts
from td_builders import update_motion_target_dashes as dashes
from td_builders import update_motion_group_success as group


class SourceBarsWhiteTests(unittest.TestCase):
    def test_only_one_compositing_line_changes_in_actual_accepted_stack(self):
        solid = Path('td_builders/motion_design.frag').read_text(encoding='utf-8')
        for style in (solid, dashes.patch_shader(solid)):
            old = group.patch_shader(cutouts.patch_shader(style))
            new = update.patch_shader(old)
            self.assertEqual(new.replace(cutouts.OLD_SOURCE, cutouts.NEW_SOURCE, 1)
                             .replace(update.NEW_COMMENT, update.OLD_COMMENT, 1), old)
            self.assertIn(cutouts.NEW_GUIDES, new)
            self.assertIn(cutouts.RADIUS, new)
            self.assertIn(group.OVERLAY, new)
            with self.assertRaises(RuntimeError):
                update.patch_shader(new)

    def test_unknown_target_compositing_is_rejected(self):
        with self.assertRaises(RuntimeError):
            update.patch_shader(cutouts.NEW_SOURCE)

    def test_python39(self):
        ast.parse(Path(update.__file__).read_text(encoding='utf-8'), feature_version=(3,9))
