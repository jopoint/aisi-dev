"""Preserve unrelated shader edits around source-bar/halo-growth changes."""
import ast
from pathlib import Path
import unittest
from unittest.mock import patch

from td_builders import update_motion_feedback_response as response


class FeedbackResponseTests(unittest.TestCase):
    def original(self):
        return (Path('td_builders/motion_design.frag').read_text(encoding='utf-8')
                .replace(response.NEW_RADIUS,response.OLD_RADIUS).replace(response.NEW_BARS,response.OLD_BARS)
                .replace(response.NEW_COMMENT,response.OLD_COMMENT))

    def test_only_source_bar_composition_and_halo_radius_change(self):
        old=self.original()+'\n// local note\n'
        new=response.patch_shader(old)
        self.assertEqual(new.replace(response.NEW_RADIUS,response.OLD_RADIUS)
                         .replace(response.NEW_BARS,response.OLD_BARS)
                         .replace(response.NEW_COMMENT,response.OLD_COMMENT),old)
        self.assertEqual(response.patch_shader(new),new)

    def test_unknown_or_partial_edits_are_rejected(self):
        old=self.original()
        for text in (old.replace(response.OLD_RADIUS,''),old+response.OLD_BARS,
                     old.replace(response.OLD_BARS,response.NEW_BARS)):
            with self.subTest(text=text[-30:]):
                with self.assertRaises(RuntimeError): response.patch_shader(text)

    def test_install_requires_own_proof_and_backup(self):
        with patch.object(response.transaction,'install') as install:
            response.install('resolve')
        install.assert_called_once_with('resolve',probe_path=response.PROBE,session=response.SESSION,
                                        backup=response.BACKUP,check=response.gpu_check)

    def test_rollback_uses_own_backup(self):
        with patch.object(response.transaction,'rollback') as rollback:
            response.rollback('resolve')
        rollback.assert_called_once_with('resolve',backup=response.BACKUP)

    def test_installer_parses_in_td_python39(self):
        ast.parse(Path('td_builders/update_motion_feedback_response.py').read_text(encoding='utf-8'),
                  feature_version=(3,9))
