"""Promote the accepted no-divider preview without losing local shader edits."""
import ast
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from td_builders import compare_motion_target_divider as compare


class SolidTargetDefaultTests(unittest.TestCase):
    def fixture(self,preview=True):
        visible=compare.VISIBLE+'\n// retained local adjustment\n'
        hidden=visible.replace(compare.VISIBLE,compare.HIDDEN)
        pixel=SimpleNamespace(text=hidden if preview else visible)
        storage={'motion_engine':SimpleNamespace(revision=3),'motion_osc_reader':object(),
                 'older_backup':'preserve'}
        if preview:
            storage[compare.SESSION]=dict(old=visible,old_sha256=compare._hash(visible),
                                          hidden_sha256=compare._hash(hidden))
        comp=SimpleNamespace(op=lambda name:pixel,fetch=lambda key,default=None:storage.get(key,default),
                             store=lambda key,value:storage.update({key:value}),
                             unstore=lambda key:storage.pop(key,None))
        return visible,hidden,pixel,storage,comp

    def test_preview_promotes_to_default_and_closes_temporary_session(self):
        visible,hidden,pixel,storage,comp=self.fixture()
        with patch.object(compare.shadow,'_validate',return_value=comp),patch.object(compare.routing,'digest'):
            result=compare.adopt_as_default(None)
        self.assertTrue(result['standard'])
        self.assertEqual(pixel.text,hidden.replace(compare.HIDDEN,compare.DEFAULT))
        self.assertNotIn(compare.SESSION,storage)
        self.assertEqual(storage[compare.DEFAULT_BACKUP]['old_visible'],visible)
        self.assertEqual(storage['older_backup'],'preserve')

    def test_visible_shader_can_be_adopted_directly_without_other_edits(self):
        visible,hidden,pixel,storage,comp=self.fixture(False)
        with patch.object(compare.shadow,'_validate',return_value=comp),patch.object(compare.routing,'digest'):
            compare.adopt_as_default(None)
        self.assertEqual(pixel.text,visible.replace(compare.VISIBLE,compare.DEFAULT))

    def test_later_local_preview_edit_is_rejected(self):
        visible,hidden,pixel,storage,comp=self.fixture()
        pixel.text+='// later'
        with patch.object(compare.shadow,'_validate',return_value=comp),patch.object(compare,'_apply') as apply:
            with self.assertRaises(RuntimeError): compare.adopt_as_default(None)
        apply.assert_not_called()
        self.assertIn(compare.SESSION,storage)

    def test_compile_failure_keeps_preview_and_its_backup(self):
        visible,hidden,pixel,storage,comp=self.fixture()
        with patch.object(compare.shadow,'_validate',return_value=comp), \
                patch.object(compare.routing,'digest',side_effect=RuntimeError('compile failed')):
            with self.assertRaisesRegex(RuntimeError,'compile failed'): compare.adopt_as_default(None)
        self.assertEqual(pixel.text,hidden)
        self.assertIn(compare.SESSION,storage)
        self.assertNotIn(compare.DEFAULT_BACKUP,storage)

    def test_adoption_is_idempotent_and_explicit_rollback_restores_previous_divider(self):
        visible,hidden,pixel,storage,comp=self.fixture()
        engine=storage['motion_engine']
        with patch.object(compare.shadow,'_validate',return_value=comp),patch.object(compare.routing,'digest'):
            compare.adopt_as_default(None)
            self.assertTrue(compare.adopt_as_default(None)['already_adopted'])
            self.assertTrue(compare.restore_previous_divider(None)['restored'])
        self.assertEqual(pixel.text,visible)
        self.assertIs(storage['motion_engine'],engine)
        self.assertEqual(engine.revision,3)

    def test_rollback_refuses_later_local_edits(self):
        visible,hidden,pixel,storage,comp=self.fixture()
        with patch.object(compare.shadow,'_validate',return_value=comp),patch.object(compare.routing,'digest'):
            compare.adopt_as_default(None)
            pixel.text+='// later'
            with self.assertRaises(RuntimeError): compare.restore_previous_divider(None)
        self.assertTrue(pixel.text.endswith('// later'))

    def test_python39_compatible(self):
        ast.parse(Path('td_builders/compare_motion_target_divider.py').read_text(encoding='utf-8'),
                  feature_version=(3,9))
