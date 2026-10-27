"""Guard the contour experiment without rewriting local routing or runtime."""
import ast
from pathlib import Path
import unittest
from unittest.mock import patch

from td_builders import update_motion_target_outline as outline
from td_builders import update_motion_target_divisions as divisions
from td_builders import update_motion_target_single_line as single_line
from td_builders import update_motion_target_surface_lines as surface_lines
from td_builders import update_motion_target_frame_strip as frame_strip
from td_builders import update_motion_target_equal_bands as equal_bands
from td_builders import update_motion_target_inner_divider as inner_divider
from td_builders import compare_motion_target_divider as divider_compare


class TargetOutlineTests(unittest.TestCase):
    def original(self):
        text=Path('td_builders/motion_design.frag').read_text(encoding='utf-8')
        text=text.replace(divider_compare.DEFAULT,divider_compare.VISIBLE)
        text=text.replace(inner_divider.HELPER,inner_divider.bands.HELPER).replace(inner_divider.FLOOR,inner_divider.bands.FLOOR)
        text=text.replace(equal_bands.HELPER,frame_strip.HELPER).replace(equal_bands.FLOOR,frame_strip.FLOOR)
        text=text.replace(frame_strip.HELPER,surface_lines.NEW_HELPER).replace(frame_strip.FLOOR,surface_lines.FLOOR_NEW)
        text=text.replace(surface_lines.NEW_HELPER,single_line.NEW).replace(surface_lines.FLOOR_NEW,surface_lines.FLOOR_OLD)
        text=text.replace(single_line.NEW,single_line.OLD)
        for old,new in divisions.PAIRS: text=text.replace(new,old)
        for old,new in outline.PAIRS: text=text.replace(new,old)
        return text

    def test_patch_preserves_other_local_code_and_is_idempotent(self):
        old=self.original()+'\n// local note\n'
        new=outline.patch_shader(old)
        restored=new
        for original,installed in outline.PAIRS: restored=restored.replace(installed,original)
        self.assertEqual(restored,old)
        self.assertEqual(outline.patch_shader(new),new)

    def test_unknown_duplicate_or_partial_edit_is_rejected(self):
        old=self.original()
        for text in (old.replace(outline.TARGET,''),old+outline.TARGET,
                     old.replace(outline.OLD_GUIDES,outline.NEW_GUIDES)):
            with self.subTest(text=text[-30:]):
                with self.assertRaises(RuntimeError): outline.patch_shader(text)

    def test_physical_target_mask_and_success_field_are_preserved(self):
        old=self.original()
        new=outline.patch_shader(old)
        self.assertIn(outline.TARGET,new)
        for anchor in ('*smoothstep(0.0,1.0,state.y)*targetMask;',
                       'layer=vec4(0.0,236.0/255.0,101.0/255.0,1.0);',
                       'layer*=sourceMask*released*remain;', 'layer*=redisplay;'):
            self.assertEqual(old.count(anchor),1)
            self.assertEqual(new.count(anchor),1)

    def test_install_uses_own_gpu_proof_and_backup(self):
        with patch.object(outline.transaction,'install') as install:
            outline.install('resolve')
        install.assert_called_once_with('resolve',probe_path=outline.PROBE,session=outline.SESSION,
                                        backup=outline.BACKUP,check=outline.gpu_check)

    def test_rollback_uses_own_backup(self):
        with patch.object(outline.transaction,'rollback') as rollback:
            outline.rollback('resolve')
        rollback.assert_called_once_with('resolve',backup=outline.BACKUP)

    def test_installer_parses_in_td_python39(self):
        ast.parse(Path('td_builders/update_motion_target_outline.py').read_text(encoding='utf-8'),
                  feature_version=(3,9))
