"""Restore the original floor footprint and a thin divider on both surfaces."""
import ast
from pathlib import Path
import unittest
from unittest.mock import patch

from td_builders import update_motion_target_inner_divider as divider
from td_builders import compare_motion_target_divider as divider_compare


class TargetInnerDividerTests(unittest.TestCase):
    def original(self):
        return (Path('td_builders/motion_design.frag').read_text(encoding='utf-8')
                .replace(divider_compare.DEFAULT,divider_compare.VISIBLE)
                .replace(divider.HELPER,divider.bands.HELPER).replace(divider.FLOOR,divider.bands.FLOOR))

    def test_patch_preserves_all_other_local_shader_code_and_is_idempotent(self):
        old=self.original()+'\n// local note\n'
        new=divider.patch_shader(old)
        self.assertEqual(new.replace(divider.HELPER,divider.bands.HELPER)
                         .replace(divider.FLOOR,divider.bands.FLOOR),old)
        self.assertEqual(divider.patch_shader(new),new)

    def test_unknown_partial_or_duplicate_local_code_is_rejected(self):
        old=self.original()
        for text in (old.replace(divider.bands.HELPER,''),old+divider.bands.HELPER,
                     old.replace(divider.bands.FLOOR,divider.FLOOR)):
            with self.subTest(text=text[-30:]):
                with self.assertRaises(RuntimeError): divider.patch_shader(text)

    def test_mask_alignment_and_success_recipes_are_preserved(self):
        old=self.original()
        new=divider.patch_shader(old)
        for anchor in ('return coverage(d-1.25);','occupied=max(occupied,sourceMask);',
                       'floorColor=over(white(waveAlpha),floorColor)*(1.0-occupied);',
                       'layer*=sourceMask*released*remain;','layer*=redisplay;',
                       'layer=vec4(0.0,236.0/255.0,101.0/255.0,1.0);'):
            self.assertEqual(old.count(anchor),1)
            self.assertEqual(new.count(anchor),1)

    def test_install_uses_own_proof_and_backup(self):
        with patch.object(divider.transaction,'install') as install:
            divider.install('resolve')
        install.assert_called_once_with('resolve',probe_path=divider.PROBE,session=divider.SESSION,
                                        backup=divider.BACKUP,check=divider.gpu_check)

    def test_rollback_uses_own_backup(self):
        with patch.object(divider.transaction,'rollback') as rollback:
            divider.rollback('resolve')
        rollback.assert_called_once_with('resolve',backup=divider.BACKUP)

    def test_python39_compatible(self):
        ast.parse(Path('td_builders/update_motion_target_inner_divider.py').read_text(encoding='utf-8'),
                  feature_version=(3,9))
