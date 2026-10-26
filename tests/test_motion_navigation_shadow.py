"""Local shader preservation and transactional navigation-shadow installation."""
import ast
import hashlib
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from td_builders import update_motion_navigation_shadow as shadow


class NavigationShadowTests(unittest.TestCase):
    def original(self):
        return (Path('td_builders/motion_design.frag').read_text(encoding='utf-8')
                .replace(shadow.HELPER, '').replace('\n' + shadow.CALL, ''))

    def test_patch_preserves_all_other_code_and_local_edits(self):
        old = self.original() + '\n// local note\n'
        new = shadow.patch_shader(old)
        self.assertEqual(new.replace(shadow.HELPER, '').replace('\n' + shadow.CALL, ''), old)
        self.assertEqual(shadow.patch_shader(new), new)

    def test_offset_shadow_updates_only_its_known_helper_to_centered_radial(self):
        centered = shadow.patch_shader(self.original() + '\n// local note\n')
        offset = centered.replace(shadow.HELPER, shadow.OFFSET_HELPER)
        self.assertEqual(shadow.patch_shader(offset), centered)
        self.assertIn('float d=length(offset);', centered)
        self.assertNotIn('vec2(2.5,2.5)', centered)

    def test_existing_shadow_backup_requires_exact_current_shader(self):
        original = self.original()
        installed = shadow.patch_shader(original).replace(shadow.HELPER, shadow.OFFSET_HELPER)
        backup = dict(old=original, new_sha256=hashlib.sha256(installed.encode()).hexdigest())
        comp = SimpleNamespace(fetch=lambda key, default=None: backup)
        self.assertEqual(shadow._checked_backup(comp, installed), backup)
        with self.assertRaises(RuntimeError): shadow._checked_backup(comp, installed + '// edit')

    def test_upgrade_keeps_original_no_shadow_backup_for_full_rollback(self):
        original = self.original()
        installed = shadow.patch_shader(original).replace(shadow.HELPER, shadow.OFFSET_HELPER)
        backup = dict(old=original, new_sha256=hashlib.sha256(installed.encode()).hexdigest())
        info = dict(old=installed, new=shadow.patch_shader(installed), reference=original,
                    previous_backup=backup.copy())
        pixel = SimpleNamespace(text=installed)
        storage = {shadow.BACKUP: backup}
        comp = SimpleNamespace(op=lambda name: pixel, fetch=lambda key, default=None:storage.get(key, default),
                               store=lambda key, value:storage.update({key:value}))
        probe = SimpleNamespace(fetch=lambda key, default=None:info, destroy=lambda:None,
            op=lambda name:SimpleNamespace(text=info['reference' if name == 'old_pixel' else 'new']))
        with patch.object(shadow, '_validate', return_value=comp), \
                patch.object(shadow, 'gpu_check', return_value=[]), patch.object(shadow.routing, 'digest'):
            self.assertTrue(shadow.install(lambda path:probe)['passed'])
        self.assertEqual(storage[shadow.BACKUP]['old'], original)
        self.assertEqual(storage[shadow.BACKUP]['new_sha256'], hashlib.sha256(pixel.text.encode()).hexdigest())

    def test_local_navigation_edit_duplicate_or_partial_shadow_is_rejected(self):
        old = self.original()
        for text in (old.replace(shadow.ANCHOR, ''), old.replace(shadow.ANCHOR, shadow.ANCHOR * 2),
                     old + shadow.HELPER, shadow.patch_shader(old).replace('*.65*scale', '*.9*scale')):
            with self.subTest(text=text[-30:]):
                with self.assertRaises(RuntimeError): shadow.patch_shader(text)

    def fixture(self):
        old = self.original()
        info = dict(old=old, new=shadow.patch_shader(old))
        pixel = SimpleNamespace(text=old)
        nodes = {'motion_pixel': pixel, 'render_floor': object(), 'render_tabletop': object(),
                 'render_preview': object()}
        comp = SimpleNamespace(op=nodes.get, fetch=lambda key, default=None: default)
        probe = SimpleNamespace(fetch=lambda key, default=None: info,
                                op=lambda name: SimpleNamespace(text=info['old' if name == 'old_pixel' else 'new']))
        return old, pixel, comp, probe

    def test_failed_gpu_proof_never_changes_production_shader(self):
        old, pixel, comp, probe = self.fixture()
        with patch.object(shadow, '_validate', return_value=comp), \
                patch.object(shadow, 'gpu_check', side_effect=RuntimeError('GPU proof failed')):
            with self.assertRaisesRegex(RuntimeError, 'GPU proof failed'): shadow.install(lambda path: probe)
        self.assertEqual(pixel.text, old)

    def test_compile_failure_restores_old_shader_without_state_writes(self):
        old, pixel, comp, probe = self.fixture()
        with patch.object(shadow, '_validate', return_value=comp), \
                patch.object(shadow, 'gpu_check', return_value=[]), \
                patch.object(shadow.routing, 'digest', side_effect=RuntimeError('compile failed')):
            with self.assertRaisesRegex(RuntimeError, 'compile failed'): shadow.install(lambda path: probe)
        self.assertEqual(pixel.text, old)

    def test_rollback_preserves_a_later_local_shader_edit(self):
        pixel = SimpleNamespace(text='later local shader edit')
        info = dict(old='old', new_sha256=hashlib.sha256(b'installed').hexdigest())
        comp = SimpleNamespace(op=lambda name: pixel, fetch=lambda key, default=None: info)
        with patch.object(shadow, '_validate', return_value=comp):
            with self.assertRaisesRegex(RuntimeError, 'verändert'): shadow.rollback(None)
        self.assertEqual(pixel.text, 'later local shader edit')

    def test_installer_parses_in_td_python39(self):
        ast.parse(Path('td_builders/update_motion_navigation_shadow.py').read_text(), feature_version=(3, 9))
