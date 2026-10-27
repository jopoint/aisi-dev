"""Disconnected experiment must preserve production and reject local divergence."""
import ast
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from td_builders import prepare_motion_under_table_probe as probe


class UnderTableProbeTests(unittest.TestCase):
    def original(self):
        return Path('td_builders/motion_design.frag').read_text(encoding='utf-8')

    def test_patch_restores_only_target_component_and_preserves_original_shader(self):
        old=self.original()+'\n// local note\n'
        new=probe.patch_shader(old)
        self.assertEqual(probe.patch_shader(new),new)
        for before,after in probe.PAIRS: new=new.replace(after,before)
        self.assertEqual(new,old)
        self.assertNotIn('floorTargets',old)
        self.assertIn(probe.FINAL,probe.patch_shader(old))

    def test_partial_duplicate_and_nonstandard_fill_refused(self):
        old=self.original()
        for text in (old+probe.FINAL,old.replace(probe.TARGET,''),
                     old.replace(probe.DECLARATION,probe.PAIRS[0][1]),
                     old.replace('float targetLines=0.0;','float targetLines=1.0;')):
            with self.assertRaises(RuntimeError): probe.patch_shader(text)

    def test_no_production_install_api(self):
        self.assertFalse(hasattr(probe,'install'))

    def test_missing_probe_cannot_be_checked_or_removed(self):
        for action in (probe.check,probe.cleanup):
            with self.assertRaises(RuntimeError): action(lambda path:None)

    def test_projector_change_aborts_before_gpu_check(self):
        owner=SimpleNamespace(fetch=lambda key,default=None:{'owned':{},'projection':{'old':'snapshot'}})
        with patch.object(probe,'own_snapshot',return_value={}), \
                patch.object(probe,'projection_snapshot',return_value={'new':'snapshot'}), \
                patch.object(probe,'gpu_check') as gpu:
            with self.assertRaisesRegex(RuntimeError,'Projektor-/Masken-/Kalibrierungsgraph'):
                probe.check(lambda path:owner)
        gpu.assert_not_called()

    def test_calibration_table_text_is_protected(self):
        node=SimpleNamespace(isDAT=True,type='table',text='1\t0\t0')
        with patch.object(probe.routing,'signature',side_effect=lambda node:{}):
            first=probe.signature(node)
            node.text='2\t0\t0'
            second=probe.signature(node)
        self.assertNotEqual(first,second)

    def test_python39_compatible(self):
        ast.parse(Path('td_builders/prepare_motion_under_table_probe.py').read_text(encoding='utf-8'),
                  feature_version=(3,9))
