"""Guard surface-specific target-line changes and the unchanged mask recipe."""
import ast
from pathlib import Path
import unittest
from unittest.mock import patch

from td_builders import update_motion_target_surface_lines as lines
from td_builders import update_motion_target_frame_strip as frame_strip
from td_builders import update_motion_target_equal_bands as equal_bands
from td_builders import update_motion_target_inner_divider as inner_divider
from td_builders import compare_motion_target_divider as divider_compare


class TargetSurfaceLinesTests(unittest.TestCase):
    def original(self):
        return (Path('td_builders/motion_design.frag').read_text(encoding='utf-8')
                .replace(divider_compare.DEFAULT,divider_compare.VISIBLE)
                .replace(inner_divider.HELPER,inner_divider.bands.HELPER).replace(inner_divider.FLOOR,inner_divider.bands.FLOOR)
                .replace(equal_bands.HELPER,frame_strip.HELPER).replace(equal_bands.FLOOR,frame_strip.FLOOR)
                .replace(frame_strip.HELPER,lines.NEW_HELPER).replace(frame_strip.FLOOR,lines.FLOOR_NEW)
                .replace(lines.NEW_HELPER,lines.single_line.NEW).replace(lines.FLOOR_NEW,lines.FLOOR_OLD))

    def test_patch_preserves_all_other_local_code_and_is_idempotent(self):
        old=self.original()+'\n// local note\n'
        new=lines.patch_shader(old)
        restored=new.replace(lines.NEW_HELPER,lines.single_line.NEW).replace(lines.FLOOR_NEW,lines.FLOOR_OLD)
        self.assertEqual(restored,old)
        self.assertEqual(lines.patch_shader(new),new)

    def test_known_three_line_predecessor_can_upgrade_without_overwriting_other_code(self):
        one=self.original()+'\n// local note\n'
        three=one.replace(lines.single_line.NEW,lines.divisions.HELPER)
        self.assertEqual(lines.patch_shader(three),lines.patch_shader(one))

    def test_unknown_and_partial_edits_are_rejected(self):
        old=self.original()
        for text in (old.replace(lines.single_line.NEW,''),old+lines.single_line.NEW,
                     old.replace(lines.FLOOR_OLD,lines.FLOOR_NEW)):
            with self.subTest(text=text[-30:]):
                with self.assertRaises(RuntimeError): lines.patch_shader(text)

    def test_physical_mask_and_success_recipe_remain_exact(self):
        old=self.original()
        new=lines.patch_shader(old)
        for anchor in ('occupied=max(occupied,sourceMask);',
                       'floorColor=over(white(waveAlpha),floorColor)*(1.0-occupied);',
                       'layer*=sourceMask*released*remain;',
                       'layer=vec4(0.0,236.0/255.0,101.0/255.0,1.0);'):
            self.assertEqual(old.count(anchor),1)
            self.assertEqual(new.count(anchor),1)

    def test_install_uses_own_gpu_proof_and_backup(self):
        with patch.object(lines.transaction,'install') as install:
            lines.install('resolve')
        install.assert_called_once_with('resolve',probe_path=lines.PROBE,session=lines.SESSION,
                                        backup=lines.BACKUP,check=lines.gpu_check)

    def test_rollback_uses_own_backup(self):
        with patch.object(lines.transaction,'rollback') as rollback:
            lines.rollback('resolve')
        rollback.assert_called_once_with('resolve',backup=lines.BACKUP)

    def test_python39_compatible(self):
        ast.parse(Path('td_builders/update_motion_target_surface_lines.py').read_text(encoding='utf-8'),
                  feature_version=(3,9))
