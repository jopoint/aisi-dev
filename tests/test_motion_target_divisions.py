"""Guard the rounded target divisions and preserve the accepted Motion state."""
import ast
from pathlib import Path
import unittest
from unittest.mock import patch

from td_builders import update_motion_target_divisions as divisions
from td_builders import update_motion_target_single_line as single_line
from td_builders import update_motion_target_surface_lines as surface_lines
from td_builders import update_motion_target_frame_strip as frame_strip
from td_builders import update_motion_target_equal_bands as equal_bands
from td_builders import update_motion_target_inner_divider as inner_divider
from td_builders import compare_motion_target_divider as divider_compare


class TargetDivisionsTests(unittest.TestCase):
    def original(self):
        text=Path('td_builders/motion_design.frag').read_text(encoding='utf-8')
        text=text.replace(divider_compare.DEFAULT,divider_compare.VISIBLE)
        text=text.replace(inner_divider.HELPER,inner_divider.bands.HELPER).replace(inner_divider.FLOOR,inner_divider.bands.FLOOR)
        text=text.replace(equal_bands.HELPER,frame_strip.HELPER).replace(equal_bands.FLOOR,frame_strip.FLOOR)
        text=text.replace(frame_strip.HELPER,surface_lines.NEW_HELPER).replace(frame_strip.FLOOR,surface_lines.FLOOR_NEW)
        text=text.replace(surface_lines.NEW_HELPER,single_line.NEW).replace(surface_lines.FLOOR_NEW,surface_lines.FLOOR_OLD)
        text=text.replace(single_line.NEW,single_line.OLD)
        for old,new in divisions.PAIRS: text=text.replace(new,old)
        return text

    def test_patch_only_changes_target_pattern_and_guide_contrast(self):
        old=self.original()+'\n// local note\n'
        new=divisions.patch_shader(old)
        restored=new
        for original,installed in divisions.PAIRS: restored=restored.replace(installed,original)
        self.assertEqual(restored,old)
        self.assertEqual(divisions.patch_shader(new),new)

    def test_unknown_partial_and_duplicate_pattern_are_rejected(self):
        old=self.original()
        for text in (old.replace(divisions.OLD_TARGET,''),old+divisions.OLD_TARGET,
                     old.replace(divisions.outline.HELPER,divisions.HELPER)):
            with self.subTest(text=text[-30:]):
                with self.assertRaises(RuntimeError): divisions.patch_shader(text)

    def test_outer_mask_success_and_redisplay_are_unchanged(self):
        old=self.original()
        new=divisions.patch_shader(old)
        for anchor in (divisions.outline.TARGET,'*smoothstep(0.0,1.0,state.y)*targetMask;',
                       'layer=vec4(0.0,236.0/255.0,101.0/255.0,1.0);','layer*=redisplay;'):
            self.assertEqual(old.count(anchor),1)
            self.assertEqual(new.count(anchor),1)

    def test_install_uses_own_proof_and_backup(self):
        with patch.object(divisions.transaction,'install') as install:
            divisions.install('resolve')
        install.assert_called_once_with('resolve',probe_path=divisions.PROBE,session=divisions.SESSION,
                                        backup=divisions.BACKUP,check=divisions.gpu_check)

    def test_rollback_restores_contour_experiment_first(self):
        with patch.object(divisions.transaction,'rollback') as rollback:
            divisions.rollback('resolve')
        rollback.assert_called_once_with('resolve',backup=divisions.BACKUP)

    def test_python39_compatible(self):
        ast.parse(Path('td_builders/update_motion_target_divisions.py').read_text(encoding='utf-8'),
                  feature_version=(3,9))

    def test_pattern_allows_measured_subpixel_edge_rounding(self):
        import numpy as np
        actual=np.array([0,1,.47930270433425903],np.float32)
        expected=np.array([0,1,.4793660044670105],np.float32)
        report=divisions.check_pattern(actual,expected)
        self.assertLess(report['pattern_max_float_error'],1e-4)
        self.assertLessEqual(report['pattern_rgba8_max_difference'],1)

    def test_pattern_rejects_visible_shift_flat_region_change_and_nan(self):
        import numpy as np
        for actual,expected in (([.51],[.5]),([.00006],[0]),([.99994],[1]),([float('nan')],[.5])):
            with self.subTest(actual=actual,expected=expected):
                with self.assertRaises(RuntimeError):
                    divisions.check_pattern(np.array(actual,np.float32),np.array(expected,np.float32))

    def test_pattern_rejects_edge_error_above_bound_even_below_one_rgba8_step(self):
        import numpy as np
        with self.assertRaises(RuntimeError):
            divisions.check_pattern(np.array([.5002],np.float32),np.array([.5],np.float32))
