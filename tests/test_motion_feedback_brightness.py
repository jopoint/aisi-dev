"""Local shader preservation and guarded feedback brightness installation."""
import ast
import hashlib
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from td_builders import update_motion_feedback_brightness as clip


class FeedbackBrightnessTests(unittest.TestCase):
    def original(self):
        return Path('td_builders/motion_design.frag').read_text(encoding='utf-8').replace(clip.NEW, clip.OLD)

    def fixture(self):
        old = self.original()
        info = dict(old=old, new=clip.patch_shader(old), mask='isolated mask shader')
        pixel = SimpleNamespace(text=old)
        storage = {'motion_engine': SimpleNamespace(revision=2), 'motion_osc_reader': object(),
                   clip.shadow.BACKUP: {'old': 'pre-shadow shader', 'new_sha256': 'preserve'}}
        comp = SimpleNamespace(op=lambda name:pixel, fetch=lambda key, default=None:storage.get(key, default),
                               store=lambda key, value:storage.update({key:value}), unstore=storage.pop)
        probe = SimpleNamespace(fetch=lambda key, default=None:info, destroy=lambda:None,
                                op=lambda name:SimpleNamespace(text=info[name.removesuffix('_pixel')]))
        return info, pixel, storage, comp, probe

    def test_only_feedback_color_changes_and_local_shadow_is_preserved(self):
        old = self.original() + '\n// local edit\n'
        new = clip.patch_shader(old)
        self.assertEqual(new.replace(clip.NEW, clip.OLD), old)
        self.assertIn(clip.shadow.HELPER, new)
        self.assertEqual(clip.patch_shader(new), new)

    def test_unknown_or_ambiguous_local_feedback_is_rejected(self):
        old = self.original()
        for text in (old.replace(clip.OLD, ''), old + clip.OLD, old + clip.NEW):
            with self.subTest(text=text[-30:]):
                with self.assertRaises(RuntimeError): clip.patch_shader(text)

    def test_gpu_failure_does_not_change_shader_or_existing_backup(self):
        info, pixel, storage, comp, probe = self.fixture()
        before = storage.copy()
        with patch.object(clip.shadow, '_validate', return_value=comp), \
                patch.object(clip, 'gpu_check', side_effect=RuntimeError('GPU failed')):
            with self.assertRaisesRegex(RuntimeError, 'GPU failed'): clip.install(lambda path:probe)
        self.assertEqual(pixel.text, info['old'])
        self.assertEqual(storage, before)

    def test_later_shader_edit_prevents_installation(self):
        info, pixel, storage, comp, probe = self.fixture()
        pixel.text += '// later edit'
        with patch.object(clip.shadow, '_validate', return_value=comp), patch.object(clip, 'gpu_check') as gpu:
            with self.assertRaises(RuntimeError): clip.install(lambda path:probe)
        gpu.assert_not_called()
        self.assertEqual(pixel.text, info['old'] + '// later edit')

    def test_compile_failure_restores_exact_old_shader(self):
        info, pixel, storage, comp, probe = self.fixture()
        with patch.object(clip.shadow, '_validate', return_value=comp), \
                patch.object(clip, 'gpu_check', return_value=[]), \
                patch.object(clip.routing, 'digest', side_effect=RuntimeError('compile failed')):
            with self.assertRaisesRegex(RuntimeError, 'compile failed'): clip.install(lambda path:probe)
        self.assertEqual(pixel.text, info['old'])
        self.assertNotIn(clip.BACKUP, storage)

    def test_install_and_rollback_preserve_shadow_and_state(self):
        info, pixel, storage, comp, probe = self.fixture()
        before = storage.copy()
        with patch.object(clip.shadow, '_validate', return_value=comp), \
                patch.object(clip, 'gpu_check', return_value=[]), patch.object(clip.routing, 'digest'):
            self.assertTrue(clip.install(lambda path:probe)['passed'])
            self.assertEqual(pixel.text, info['new'])
            self.assertEqual(storage[clip.BACKUP]['new_sha256'], hashlib.sha256(pixel.text.encode()).hexdigest())
            self.assertTrue(clip.rollback(None)['restored'])
        self.assertEqual(pixel.text, info['old'])
        self.assertEqual(storage, before)

    def test_rollback_refuses_later_edit(self):
        info, pixel, storage, comp, probe = self.fixture()
        storage[clip.BACKUP] = dict(old=info['old'], new_sha256=hashlib.sha256(info['new'].encode()).hexdigest())
        pixel.text = info['new'] + '// local'
        with patch.object(clip.shadow, '_validate', return_value=comp):
            with self.assertRaises(RuntimeError): clip.rollback(None)
        self.assertTrue(pixel.text.endswith('// local'))

    def test_td_python39_compatible(self):
        ast.parse(Path('td_builders/update_motion_feedback_brightness.py').read_text(encoding='utf-8'),
                  feature_version=(3, 9))
