"""Correct four-centimetre frame strips without changing masks or state."""
import ast
from pathlib import Path
import unittest
from unittest.mock import patch

from td_builders import update_motion_target_frame_strip as frame
from td_builders import update_motion_target_equal_bands as equal_bands
from td_builders import update_motion_target_inner_divider as inner_divider
from td_builders import compare_motion_target_divider as divider_compare


class TargetFrameStripTests(unittest.TestCase):
    def original(self):
        return (Path('td_builders/motion_design.frag').read_text(encoding='utf-8')
                .replace(divider_compare.DEFAULT,divider_compare.VISIBLE)
                .replace(inner_divider.HELPER,inner_divider.bands.HELPER).replace(inner_divider.FLOOR,inner_divider.bands.FLOOR)
                .replace(equal_bands.HELPER,frame.HELPER).replace(equal_bands.FLOOR,frame.FLOOR)
                .replace(frame.HELPER,frame.single_line.NEW).replace(frame.FLOOR,frame.surfaces.FLOOR_OLD))

    def test_patch_preserves_other_local_code_and_is_idempotent(self):
        old=self.original()+'\n// local note\n'
        new=frame.patch_shader(old)
        restored=new.replace(frame.HELPER,frame.single_line.NEW).replace(frame.FLOOR,frame.surfaces.FLOOR_OLD)
        self.assertEqual(restored,old)
        self.assertEqual(frame.patch_shader(new),new)

    def test_corrects_known_misunderstood_surface_variant(self):
        old=self.original()
        misunderstood=frame.surfaces.patch_shader(old)
        self.assertEqual(frame.patch_shader(misunderstood),frame.patch_shader(old))

    def test_known_three_line_and_outline_predecessors_upgrade(self):
        old=self.original()
        three=old.replace(frame.single_line.NEW,frame.divisions.HELPER)
        outline=three
        for original,new in frame.divisions.PAIRS: outline=outline.replace(new,original)
        self.assertEqual(frame.patch_shader(three),frame.patch_shader(old))
        self.assertEqual(frame.patch_shader(outline),frame.patch_shader(old))

    def test_unknown_or_partial_edits_are_rejected(self):
        old=self.original()
        for text in (old.replace(frame.single_line.NEW,''),old+frame.single_line.NEW,
                     old.replace(frame.surfaces.FLOOR_OLD,frame.FLOOR)):
            with self.subTest(text=text[-30:]):
                with self.assertRaises(RuntimeError): frame.patch_shader(text)

    def test_physical_masks_success_and_redisplay_unchanged(self):
        old=self.original()
        new=frame.patch_shader(old)
        for anchor in ('occupied=max(occupied,sourceMask);',
                       'floorColor=over(white(waveAlpha),floorColor)*(1.0-occupied);',
                       'layer*=sourceMask*released*remain;', 'layer*=redisplay;',
                       'layer=vec4(0.0,236.0/255.0,101.0/255.0,1.0);'):
            self.assertEqual(old.count(anchor),1)
            self.assertEqual(new.count(anchor),1)

    def test_install_uses_own_gpu_proof_and_backup(self):
        with patch.object(frame.transaction,'install') as install:
            frame.install('resolve')
        install.assert_called_once_with('resolve',probe_path=frame.PROBE,session=frame.SESSION,
                                        backup=frame.BACKUP,check=frame.gpu_check)

    def test_rollback_uses_own_backup(self):
        with patch.object(frame.transaction,'rollback') as rollback:
            frame.rollback('resolve')
        rollback.assert_called_once_with('resolve',backup=frame.BACKUP)

    def test_python39_compatible(self):
        ast.parse(Path('td_builders/update_motion_target_frame_strip.py').read_text(encoding='utf-8'),
                  feature_version=(3,9))
