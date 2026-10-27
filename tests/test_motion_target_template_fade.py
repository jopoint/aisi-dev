"""Only the target template circle gains the existing guide fade factor."""
import ast
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from td_builders import update_motion_target_template_fade as fade


class TargetTemplateFadeTests(unittest.TestCase):
    def original(self):
        return Path('td_builders/motion_design.frag').read_text(encoding='utf-8').replace(fade.NEW,fade.OLD)

    def test_patch_preserves_everything_except_target_ring_factor(self):
        old=self.original()+'\n// local note\n'
        new=fade.patch_shader(old)
        self.assertEqual(new.replace(fade.NEW,fade.OLD),old)
        self.assertEqual(fade.patch_shader(new),new)

    def test_local_unexpected_or_duplicate_ring_is_rejected(self):
        old=self.original()
        for text in (old.replace(fade.OLD,''),old+fade.OLD):
            with self.assertRaises(RuntimeError): fade.patch_shader(text)

    def test_open_temporary_preview_must_be_adopted_before_next_patch(self):
        comp=SimpleNamespace(fetch=lambda key,default=None: {'old':'preview'})
        with patch.object(fade.transaction.shadow,'_validate',return_value=comp), \
                patch.object(fade.transaction,'prepare') as prepare:
            with self.assertRaisesRegex(RuntimeError,'Vergleich noch offen'): fade.prepare(None)
        prepare.assert_not_called()

    def test_install_uses_own_gpu_proof_and_backup(self):
        with patch.object(fade.transaction,'install') as install:
            fade.install('resolve')
        install.assert_called_once_with('resolve',probe_path=fade.PROBE,session=fade.SESSION,
                                        backup=fade.BACKUP,check=fade.gpu_check)

    def test_rollback_uses_own_backup(self):
        with patch.object(fade.transaction,'rollback') as rollback:
            fade.rollback('resolve')
        rollback.assert_called_once_with('resolve',backup=fade.BACKUP)

    def test_python39_compatible(self):
        ast.parse(Path('td_builders/update_motion_target_template_fade.py').read_text(encoding='utf-8'),
                  feature_version=(3,9))
