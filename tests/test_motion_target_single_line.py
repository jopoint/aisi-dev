"""Guard the single-line follow-up without losing local shader adjustments."""
import ast
from pathlib import Path
import unittest
from unittest.mock import patch

from td_builders import update_motion_target_single_line as single_line
from td_builders import update_motion_target_surface_lines as surface_lines
from td_builders import update_motion_target_frame_strip as frame_strip
from td_builders import update_motion_target_equal_bands as equal_bands
from td_builders import update_motion_target_inner_divider as inner_divider
from td_builders import compare_motion_target_divider as divider_compare


class TargetSingleLineTests(unittest.TestCase):
    def original(self):
        return (Path('td_builders/motion_design.frag').read_text(encoding='utf-8')
                .replace(divider_compare.DEFAULT,divider_compare.VISIBLE)
                .replace(inner_divider.HELPER,inner_divider.bands.HELPER).replace(inner_divider.FLOOR,inner_divider.bands.FLOOR)
                .replace(equal_bands.HELPER,frame_strip.HELPER).replace(equal_bands.FLOOR,frame_strip.FLOOR)
                .replace(frame_strip.HELPER,surface_lines.NEW_HELPER).replace(frame_strip.FLOOR,surface_lines.FLOOR_NEW)
                .replace(surface_lines.NEW_HELPER,single_line.NEW).replace(surface_lines.FLOOR_NEW,surface_lines.FLOOR_OLD)
                .replace(single_line.NEW,single_line.OLD))

    def test_only_line_helper_changes_and_local_edits_survive(self):
        old=self.original()+'\n// local note\n'
        new=single_line.patch_shader(old)
        self.assertEqual(new.replace(single_line.NEW,single_line.OLD),old)
        self.assertEqual(single_line.patch_shader(new),new)

    def test_unknown_or_duplicate_local_helper_is_rejected(self):
        old=self.original()
        for text in (old.replace(single_line.OLD,''),old+single_line.OLD,
                     old.replace('j<=3','j<=2')):
            with self.subTest(text=text[-30:]):
                with self.assertRaises(RuntimeError): single_line.patch_shader(text)

    def test_install_uses_own_proof_and_backup(self):
        with patch.object(single_line.transaction,'install') as install:
            single_line.install('resolve')
        install.assert_called_once_with('resolve',probe_path=single_line.PROBE,session=single_line.SESSION,
                                        backup=single_line.BACKUP,check=single_line.gpu_check)

    def test_rollback_uses_own_backup(self):
        with patch.object(single_line.transaction,'rollback') as rollback:
            single_line.rollback('resolve')
        rollback.assert_called_once_with('resolve',backup=single_line.BACKUP)

    def test_python39_compatible(self):
        ast.parse(Path('td_builders/update_motion_target_single_line.py').read_text(encoding='utf-8'),
                  feature_version=(3,9))
