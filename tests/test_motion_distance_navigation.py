"""Preserve the accepted alignment experiment around a local distance patch."""
import ast
from pathlib import Path
import unittest
from unittest.mock import patch

from td_builders import update_motion_distance_navigation as distance
from td_builders import update_motion_alignment_timing as timing


class DistanceNavigationTests(unittest.TestCase):
    def original(self):
        return (Path('td_builders/motion_design.frag').read_text(encoding='utf-8')
                .replace(timing.NEW_RADIUS,timing.OLD_RADIUS).replace(timing.NEW_GUIDES,timing.OLD_GUIDES)
                .replace(distance.NEW_SCALE,distance.OLD_SCALE)
                .replace(distance.NEW_ARROW,distance.OLD_ARROW))

    def test_patch_preserves_everything_except_scale_and_arrow(self):
        old=self.original()+'\n// local note\n'
        new=distance.patch_shader(old)
        self.assertEqual(new.replace(distance.NEW_SCALE,distance.OLD_SCALE)
                         .replace(distance.NEW_ARROW,distance.OLD_ARROW),old)
        self.assertEqual(distance.patch_shader(new),new)

    def test_partial_or_unknown_edits_are_rejected(self):
        old=self.original()
        for text in (old.replace(distance.OLD_SCALE,''),old+distance.OLD_ARROW,
                     old.replace(distance.OLD_ARROW,distance.NEW_ARROW)):
            with self.subTest(text=text[-30:]):
                with self.assertRaises(RuntimeError): distance.patch_shader(text)

    def test_install_uses_own_proof_and_backup(self):
        with patch.object(distance.transaction,'install') as install:
            distance.install('resolve')
        install.assert_called_once_with('resolve',probe_path=distance.PROBE,session=distance.SESSION,
                                        backup=distance.BACKUP,check=distance.gpu_check)

    def test_rollback_uses_own_backup(self):
        with patch.object(distance.transaction,'rollback') as rollback:
            distance.rollback('resolve')
        rollback.assert_called_once_with('resolve',backup=distance.BACKUP)

    def test_installer_parses_in_td_python39(self):
        ast.parse(Path('td_builders/update_motion_distance_navigation.py').read_text(encoding='utf-8'),
                  feature_version=(3,9))
