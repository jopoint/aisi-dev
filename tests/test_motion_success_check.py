"""Success acknowledgement stays a guarded rendering-only change."""
import ast
from pathlib import Path
import unittest
from unittest.mock import patch

from td_builders import update_motion_success_check as check
from td_builders import update_motion_success_pop as pop
from td_builders import update_motion_success_pop_out as pop_out


class SuccessCheckTests(unittest.TestCase):
    def test_world_pixel_uses_independently_measured_array_axes(self):
        import numpy as np
        mask=np.zeros((1000,1000))
        mask[330:390,300:420]=1
        for flip_x,flip_y in ((False,False),(False,True),(True,False),(True,True)):
            image=mask[:,::-1] if flip_x else mask.copy()
            image=image[::-1] if flip_y else image
            axes=check.mask_axes(image,(180,180))
            self.assertEqual(axes,[flip_x,flip_y])
            self.assertEqual(check.world_pixel(image,(180,180),axes),1)
            self.assertEqual(check.world_pixel(image,(320,320),axes),0)

    def test_empty_or_ambiguous_axis_proof_refused(self):
        import numpy as np
        for mask,center in ((np.zeros((10,10)),(180,180)),(np.ones((10,10)),(250,250))):
            with self.assertRaises(RuntimeError): check.mask_axes(mask,center)

    def original(self):
        text=Path('td_builders/motion_design.frag').read_text(encoding='utf-8')
        for old,new in pop_out.PAIRS: text=text.replace(new,old)
        for old,new in pop.PAIRS: text=text.replace(new,old)
        for old,new in check.PAIRS: text=text.replace(new,old)
        return text

    def test_patch_only_adds_helper_and_success_overlay(self):
        old=self.original()+'\n// local note\n'
        new=check.patch_shader(old)
        self.assertEqual(check.patch_shader(new),new)
        for before,after in check.PAIRS: new=new.replace(after,before)
        self.assertEqual(new,old)

    def test_partial_or_duplicate_local_patch_rejected(self):
        old=self.original()
        for text in (old.replace(check.ANCHOR,''),old+check.ANCHOR,
                     old.replace(check.TABLE_ANCHOR,check.OVERLAY+check.TABLE_ANCHOR)):
            with self.assertRaises(RuntimeError): check.patch_shader(text)

    def test_completed_phase_not_excluded_and_same_success_clock_used(self):
        self.assertIn('state.w>.5 && pulse.z<3.0',check.OVERLAY)
        self.assertNotIn('state.w<1.5',check.OVERLAY)
        self.assertIn('p-source.xy,target.xyz',check.OVERLAY)
        self.assertIn('*checkAlpha*sourceMask*released',check.OVERLAY)

    def test_prepare_and_install_own_transaction_boundaries(self):
        with patch.object(check.transaction,'prepare',return_value={}) as prepare:
            result=check.prepare('resolve')
        self.assertEqual(result['duration_seconds'],3)
        self.assertFalse(result['runtime_changed'])
        self.assertIs(prepare.call_args.kwargs['patcher'],check.patch_shader)
        with patch.object(check.transaction,'install') as install:
            check.install('resolve')
        self.assertIs(install.call_args.kwargs['check'],check.gpu_check)
        self.assertEqual(install.call_args.kwargs['backup'],check.BACKUP)

    def test_rollback_own_backup(self):
        with patch.object(check.transaction,'rollback') as rollback: check.rollback('resolve')
        rollback.assert_called_once_with('resolve',backup=check.BACKUP)

    def test_python39_compatible(self):
        ast.parse(Path('td_builders/update_motion_success_check.py').read_text(encoding='utf-8'),
                  feature_version=(3,9))
