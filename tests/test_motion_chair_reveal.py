"""Chair-only shader patch and exact owned-hash transaction; no layout mutations."""
import ast
import copy
import hashlib
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from td_builders import update_motion_chair_reveal as update


class ChairRevealTests(unittest.TestCase):
    def test_patch_only_inserts_visual_reveal_gate_and_preserves_local_text(self):
        current = Path('td_builders/motion_chairs.frag').read_text()
        old = current.replace(update.NEW,update.OLD)+'\n// local note\n'
        installed = update.patch_shader(old)
        self.assertEqual(installed.replace(update.NEW,update.OLD),old)
        self.assertEqual(update.patch_shader(installed),installed)
        with self.assertRaises(RuntimeError): update.patch_shader(old+update.OLD)

    def test_canonical_shader_has_same_optional_clock_as_motion_shader(self):
        text = Path('td_builders/motion_chairs.frag').read_text()
        self.assertIn(update.NEW,text)
        self.assertIn('clock.y=visualReveal.x;',text)
        self.assertIn('a*=released*(1.0-occupied);',text)

    def fixture(self):
        pixel = SimpleNamespace(path=update.CHAIRS+'/chair_pixel',text='old')
        owned = {pixel.path:dict(text_sha256=hashlib.sha256(b'old').hexdigest(),parameters={'keep':'unchanged'})}
        chair_reader = object()
        storage = {'chair_owned':owned,'chair_reader':chair_reader,'older_backup':'keep'}
        comp = SimpleNamespace(op=lambda name:pixel if name=='chair_pixel' else object(),
            fetch=lambda key,default=None:storage.get(key,default),
            store=lambda key,value:storage.update({key:value}),unstore=lambda key:storage.pop(key,None))
        engine = SimpleNamespace(revision=('osc',123,2),started=10)
        motion = SimpleNamespace(fetch=lambda *args:engine)
        info = dict(old='old',new='new',owned=copy.deepcopy(owned))
        probe = SimpleNamespace(fetch=lambda *args:info,
            op=lambda name:SimpleNamespace(text=info[name.removesuffix('_pixel')]),destroy=lambda:None)
        resolve = lambda path:probe if path==update.PROBE else motion
        return pixel,storage,comp,engine,resolve

    def test_success_changes_only_shader_hash_then_rolls_back_exactly(self):
        pixel,storage,comp,engine,resolve = self.fixture()
        before = copy.copy(storage)
        with patch.object(update,'validate',return_value=comp), \
             patch.object(update,'gpu_check',return_value=[]), \
             patch.object(update.routing,'digest'),patch.object(update.routing,'assert_snapshot'):
            report = update.install(resolve)
            self.assertTrue(report['passed'])
            self.assertEqual(pixel.text,'new')
            self.assertEqual(storage['chair_owned'][pixel.path]['parameters'],{'keep':'unchanged'})
            self.assertEqual(storage['chair_owned'][pixel.path]['text_sha256'],hashlib.sha256(b'new').hexdigest())
            self.assertEqual((engine.revision,engine.started),(('osc',123,2),10))
            self.assertTrue(update.rollback(resolve)['restored'])
        self.assertEqual(pixel.text,'old')
        self.assertEqual(storage,before)

    def test_failed_gpu_proof_never_changes_production_or_registry(self):
        pixel,storage,comp,engine,resolve = self.fixture()
        original = copy.copy(storage)
        with patch.object(update,'validate',return_value=comp), \
             patch.object(update,'gpu_check',side_effect=RuntimeError('GPU failed')):
            with self.assertRaises(RuntimeError): update.install(resolve)
        self.assertEqual(pixel.text,'old')
        self.assertEqual(storage,original)

    def test_compile_failure_restores_both_text_and_hash(self):
        pixel,storage,comp,engine,resolve = self.fixture()
        original = copy.copy(storage)
        with patch.object(update,'validate',return_value=comp), \
             patch.object(update,'gpu_check',return_value=[]), \
             patch.object(update.routing,'digest',side_effect=RuntimeError('compile failed')):
            with self.assertRaises(RuntimeError): update.install(resolve)
        self.assertEqual(pixel.text,'old')
        self.assertEqual(storage,original)

    def test_python39_compatible(self):
        ast.parse(Path('td_builders/update_motion_chair_reveal.py').read_text(),feature_version=(3,9))
