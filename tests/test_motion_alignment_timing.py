"""The timing adjustment changes only two display expressions."""
import ast
from pathlib import Path
import unittest
from unittest.mock import patch

from td_builders import update_motion_alignment_timing as timing


class AlignmentTimingTests(unittest.TestCase):
    def original(self):
        return (Path('td_builders/motion_design.frag').read_text(encoding='utf-8')
                .replace(timing.NEW_RADIUS,timing.OLD_RADIUS).replace(timing.NEW_GUIDES,timing.OLD_GUIDES))

    def test_patch_preserves_other_local_code_and_is_idempotent(self):
        old=self.original()+'\n// local note\n'
        new=timing.patch_shader(old)
        self.assertEqual(new.replace(timing.NEW_RADIUS,timing.OLD_RADIUS)
                         .replace(timing.NEW_GUIDES,timing.OLD_GUIDES),old)
        self.assertEqual(timing.patch_shader(new),new)

    def test_unexpected_or_partial_edits_are_rejected(self):
        old=self.original()
        for text in (old.replace(timing.OLD_RADIUS,''),old+timing.OLD_GUIDES,
                     old.replace(timing.OLD_RADIUS,timing.NEW_RADIUS)):
            with self.subTest(text=text[-30:]):
                with self.assertRaises(RuntimeError): timing.patch_shader(text)

    def test_install_requires_own_proof_and_backup(self):
        with patch.object(timing.transaction,'install') as install:
            timing.install('resolve')
        install.assert_called_once_with('resolve',probe_path=timing.PROBE,session=timing.SESSION,
                                        backup=timing.BACKUP,check=timing.gpu_check)

    def test_rollback_uses_own_backup(self):
        with patch.object(timing.transaction,'rollback') as rollback:
            timing.rollback('resolve')
        rollback.assert_called_once_with('resolve',backup=timing.BACKUP)

    def test_installer_parses_in_td_python39(self):
        ast.parse(Path('td_builders/update_motion_alignment_timing.py').read_text(encoding='utf-8'),
                  feature_version=(3,9))
