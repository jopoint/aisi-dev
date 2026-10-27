"""Keep entrance geometry; reverse it after one second without an alpha fade."""
import ast
from pathlib import Path
import unittest
from unittest.mock import patch

from td_builders import update_motion_success_pop_out as change


class SuccessPopOutTests(unittest.TestCase):
    def original(self):
        return Path('td_builders/motion_design.frag').read_text(encoding='utf-8').replace(change.OVERLAY,change.pop.OVERLAY)

    def test_only_overlay_replaced_and_idempotent(self):
        old=self.original()+'\n// local note\n'
        new=change.patch_shader(old)
        self.assertEqual(change.patch_shader(new),new)
        self.assertEqual(new.replace(change.OVERLAY,change.pop.OVERLAY),old)
        self.assertNotIn('checkAlpha',change.OVERLAY)
        self.assertIn('pulse.z<=1.0?successPop(pulse.z)',change.OVERLAY)
        self.assertIn('successPop(max(0.0,1.32-pulse.z))',change.OVERLAY)

    def test_missing_or_modified_helper_and_duplicate_overlay_refused(self):
        old=self.original()
        for text in (old.replace(change.pop.HELPER,''),old+change.pop.OVERLAY,
                     old.replace(change.pop.OVERLAY,'')):
            with self.assertRaises(RuntimeError): change.patch_shader(text)

    def test_prepare_timing_and_own_backup(self):
        with patch.object(change.transaction,'prepare',return_value={}) as prepare:
            result=change.prepare('resolve')
        self.assertEqual(result['exit_starts_seconds'],1)
        self.assertEqual(result['hidden_after_seconds'],1.32)
        self.assertFalse(result['fade'])
        self.assertFalse(result['runtime_changed'])
        self.assertIs(prepare.call_args.kwargs['patcher'],change.patch_shader)

    def test_guarded_install_rollback_dispatch(self):
        with patch.object(change.transaction,'install') as install: change.install('resolve')
        self.assertIs(install.call_args.kwargs['check'],change.gpu_check)
        self.assertEqual(install.call_args.kwargs['backup'],change.BACKUP)
        with patch.object(change.transaction,'rollback') as rollback: change.rollback('resolve')
        rollback.assert_called_once_with('resolve',backup=change.BACKUP)

    def test_python39_compatible(self):
        ast.parse(Path('td_builders/update_motion_success_pop_out.py').read_text(encoding='utf-8'),
                  feature_version=(3,9))
