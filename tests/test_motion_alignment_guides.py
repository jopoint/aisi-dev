"""Guard the display-only alignment experiment and its rollback boundary."""
import ast
from pathlib import Path
import unittest
from unittest.mock import patch

from td_builders import update_motion_alignment_guides as guides
from td_builders import update_motion_distance_navigation as distance_navigation
from td_builders import update_motion_alignment_timing as timing
from td_builders import update_motion_feedback_response as response


class AlignmentGuidesTests(unittest.TestCase):
    def original(self):
        return (Path('td_builders/motion_design.frag').read_text(encoding='utf-8')
                .replace(response.NEW_RADIUS,response.OLD_RADIUS).replace(response.NEW_BARS,response.OLD_BARS)
                .replace(response.NEW_COMMENT,response.OLD_COMMENT)
                .replace(timing.NEW_RADIUS,timing.OLD_RADIUS).replace(timing.NEW_GUIDES,timing.OLD_GUIDES)
                .replace(distance_navigation.NEW_SCALE, distance_navigation.OLD_SCALE)
                .replace(distance_navigation.NEW_ARROW, distance_navigation.OLD_ARROW)
                .replace(guides.NEW, guides.OLD).replace(guides.HELPER, '')
                .replace(guides.AFTER, guides.ANCHOR))

    def test_patch_preserves_all_other_local_shader_code(self):
        old = self.original() + '\n// local calibration-independent note\n'
        new = guides.patch_shader(old)
        self.assertEqual(new.replace(guides.NEW, guides.OLD).replace(guides.HELPER, '')
                         .replace(guides.AFTER, guides.ANCHOR), old)
        self.assertEqual(guides.patch_shader(new), new)

    def test_unknown_or_partial_local_guides_are_rejected(self):
        old = self.original()
        for text in (old.replace(guides.OLD, ''), old + guides.OLD, old + guides.HELPER):
            with self.subTest(text=text[-30:]):
                with self.assertRaises(RuntimeError): guides.patch_shader(text)

    def test_prepare_uses_separate_probe_and_existing_guarded_transaction(self):
        with patch.object(guides.transaction, 'prepare', return_value={}) as prepare:
            result = guides.prepare('resolve')
        self.assertEqual(prepare.call_args.kwargs, dict(probe_path=guides.PROBE,
                         session=guides.SESSION, backup=guides.BACKUP, patcher=guides.patch_shader))
        self.assertEqual(result['minimum_navigation_scale'], .5)

    def test_install_requires_alignment_gpu_proof(self):
        with patch.object(guides.transaction, 'install') as install:
            guides.install('resolve')
        self.assertIs(install.call_args.kwargs['check'], guides.gpu_check)
        self.assertEqual(install.call_args.kwargs['backup'], guides.BACKUP)

    def test_rollback_uses_own_backup(self):
        with patch.object(guides.transaction, 'rollback') as rollback:
            guides.rollback('resolve')
        rollback.assert_called_once_with('resolve', backup=guides.BACKUP)

    def test_installer_parses_on_td_python39(self):
        ast.parse(Path('td_builders/update_motion_alignment_guides.py').read_text(encoding='utf-8'),
                  feature_version=(3, 9))

    def test_floor_accepts_float_rounding_only_with_identical_rgba8(self):
        import numpy as np
        old = np.full((2,2,4), .4, np.float32)
        new = np.nextafter(old, np.float32(1))
        report = guides.check_floor(old,new)
        self.assertTrue(report['rgba8_pixel_equal'])
        self.assertGreater(report['max_float_error'],0)

    def test_floor_rejects_visible_difference_quantization_boundary_and_nan(self):
        import numpy as np
        old = np.full((2,2,4), .5, np.float32)
        for new in (old+.01, np.nextafter(old,np.float32(0)), old*np.nan):
            with self.subTest(value=new[0,0,0]):
                with self.assertRaises(RuntimeError): guides.check_floor(old,new)
