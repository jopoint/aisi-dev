"""Guard the checkmark-only pop/fade and reversible installation."""
import ast
from pathlib import Path
import unittest
from unittest.mock import patch

from td_builders import update_motion_success_pop as pop
from td_builders import update_motion_success_pop_out as pop_out


class SuccessPopTests(unittest.TestCase):
    def original(self):
        text=Path('td_builders/motion_design.frag').read_text(encoding='utf-8')
        for old,new in pop_out.PAIRS: text=text.replace(new,old)
        for old,new in pop.PAIRS: text=text.replace(new,old)
        return text

    def test_patch_preserves_existing_guidance_success_runtime_contract(self):
        old=self.original()+'\n// local note\n'
        new=pop.patch_shader(old)
        self.assertEqual(pop.patch_shader(new),new)
        for before,after in pop.PAIRS: new=new.replace(after,before)
        self.assertEqual(new,old)

    def test_partial_or_duplicate_patch_refused(self):
        old=self.original()
        for text in (old+pop.ANCHOR,old.replace(pop.success.OVERLAY,''),
                     old.replace(pop.ANCHOR,pop.HELPER+pop.ANCHOR)):
            with self.assertRaises(RuntimeError): pop.patch_shader(text)

    def test_prepare_reports_confirmed_three_seconds(self):
        with patch.object(pop.transaction,'prepare',return_value={}) as prepare:
            result=pop.prepare('resolve')
        self.assertEqual(result['duration_seconds'],3)
        self.assertEqual(result['pop_seconds'],.32)
        self.assertFalse(result['runtime_changed'])
        self.assertIs(prepare.call_args.kwargs['patcher'],pop.patch_shader)

    def test_install_and_rollback_use_own_guarded_backup(self):
        with patch.object(pop.transaction,'install') as install: pop.install('resolve')
        self.assertEqual(install.call_args.kwargs['backup'],pop.BACKUP)
        self.assertIs(install.call_args.kwargs['check'],pop.gpu_check)
        with patch.object(pop.transaction,'rollback') as rollback: pop.rollback('resolve')
        rollback.assert_called_once_with('resolve',backup=pop.BACKUP)

    def test_pop_curve_grows_overshoots_and_settles_without_negative_scale(self):
        def scale(age):
            x=max(0,min(1,age/.32))-1
            return max(0,1+2.70158*x**3+1.70158*x*x)
        self.assertAlmostEqual(scale(0),0)
        self.assertLess(scale(.08),1)
        self.assertGreater(scale(.2),1.09)
        self.assertEqual(scale(.32),1)
        self.assertEqual(scale(3),1)
        self.assertIn('clamp(1.0-pulse.z/3.0,0.0,1.0)',pop.OVERLAY)

    def test_python39_compatible(self):
        ast.parse(Path('td_builders/update_motion_success_pop.py').read_text(encoding='utf-8'),
                  feature_version=(3,9))
