"""Frame and divider share the alignment-bar width; live IDs remain untouched."""
import ast
from pathlib import Path
import unittest
from unittest.mock import patch

from td_builders import update_motion_target_equal_bands as bands
from td_builders import update_motion_target_inner_divider as inner_divider
from td_builders import compare_motion_target_divider as divider_compare


class TargetEqualBandsTests(unittest.TestCase):
    def original(self):
        return (Path('td_builders/motion_design.frag').read_text(encoding='utf-8')
                .replace(divider_compare.DEFAULT,divider_compare.VISIBLE)
                .replace(inner_divider.HELPER,bands.HELPER).replace(inner_divider.FLOOR,bands.FLOOR)
                .replace(bands.HELPER,bands.frame.HELPER).replace(bands.FLOOR,bands.frame.FLOOR))

    def test_patch_preserves_other_local_code_and_is_idempotent(self):
        old=self.original()+'\n// local note\n'
        new=bands.patch_shader(old)
        self.assertEqual(new.replace(bands.HELPER,bands.frame.HELPER).replace(bands.FLOOR,bands.frame.FLOOR),old)
        self.assertEqual(bands.patch_shader(new),new)

    def test_local_alignment_width_change_is_rejected(self):
        old=self.original().replace('coverage(d-1.25)','coverage(d-1.5)')
        with self.assertRaises(RuntimeError): bands.patch_shader(old)

    def test_partial_local_changes_are_rejected(self):
        old=self.original().replace(bands.frame.HELPER,bands.HELPER)
        with self.assertRaises(RuntimeError): bands.patch_shader(old)

    def test_install_uses_own_gpu_proof_and_backup(self):
        with patch.object(bands.transaction,'install') as install:
            bands.install('resolve')
        install.assert_called_once_with('resolve',probe_path=bands.PROBE,session=bands.SESSION,
                                        backup=bands.BACKUP,check=bands.gpu_check)

    def test_rollback_uses_own_backup(self):
        with patch.object(bands.transaction,'rollback') as rollback:
            bands.rollback('resolve')
        rollback.assert_called_once_with('resolve',backup=bands.BACKUP)

    def test_python39_compatible(self):
        ast.parse(Path('td_builders/update_motion_target_equal_bands.py').read_text(encoding='utf-8'),
                  feature_version=(3,9))
