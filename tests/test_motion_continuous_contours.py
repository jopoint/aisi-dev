import ast
import copy
import hashlib
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from td_builders import update_motion_continuous_contours as update
from td_builders import update_motion_target_dashes as dashes
from td_builders import update_motion_feedback_size_cutouts as feedback
from td_builders import update_motion_source_bars_white as bars
from td_builders import update_motion_group_success as group


class ContinuousContoursTests(unittest.TestCase):
    def test_only_target_shape_and_chair_stroke_change(self):
        base = Path('td_builders/motion_design.frag').read_text(encoding='utf-8')
        current = group.patch_shader(feedback.patch_shader(dashes.patch_shader(base)))
        for old in (current, bars.patch_shader(current)):
            new = update.patch_shader(old)
            self.assertEqual(new.replace(update.HELPER,dashes.HELPER).replace(update.FILL,dashes.NEW_FILL),old)
            self.assertIn(feedback.RADIUS,new)
            self.assertIn(group.OVERLAY,new)
            self.assertNotIn('targetDashes(',new)
        chair = Path('td_builders/motion_chairs.frag').read_text(encoding='utf-8')
        new = update.patch_chairs(chair)
        self.assertEqual(new.replace(update.NEW_CHAIR,update.OLD_CHAIR),chair)
        self.assertIn('a*=released*(1.0-occupied);',new)
        self.assertIn('clock.y=visualReveal.x;',new)

    def test_unknown_or_repeated_patches_rejected(self):
        base = Path('td_builders/motion_design.frag').read_text(encoding='utf-8')
        dashed = dashes.patch_shader(base)
        for bad in (base, update.patch_shader(dashed), dashed+dashes.HELPER):
            with self.assertRaises(RuntimeError): update.patch_shader(bad)
        chair = Path('td_builders/motion_chairs.frag').read_text(encoding='utf-8')
        with self.assertRaises(RuntimeError): update.patch_chairs(update.patch_chairs(chair))

    def test_chair_band_is_5cm_inward_with_same_outer_radius(self):
        for radius in (20,25,30):
            center, halfwidth = radius-2.5,2.5
            self.assertEqual(center+halfwidth,radius)
            self.assertEqual(center-halfwidth,radius-5)
        self.assertIn('coverage(d)-coverage(d+5.0)',update.HELPER)

    def test_python39(self):
        ast.parse(Path(update.__file__).read_text(encoding='utf-8'), feature_version=(3,9))


class ContourTransactionTests(unittest.TestCase):
    def fixture(self):
        pixel = SimpleNamespace(text='old')
        chair_pixel = SimpleNamespace(path='/chairs/pixel',text='chair old')
        owned = {chair_pixel.path:dict(text_sha256=hashlib.sha256(b'chair old').hexdigest(),keep=7)}
        engine = SimpleNamespace(revision=7,started=10)
        reader = object()
        main_storage = {'motion_engine':engine,'older':'keep'}
        chair_storage = {'chair_owned':copy.deepcopy(owned),'chair_reader':reader}
        def comp(storage, node):
            return SimpleNamespace(op=lambda name:node if name in ('chair_pixel','motion_pixel') else object(),
                fetch=lambda key,default=None:storage.get(key,default),
                store=lambda key,value:storage.update({key:value}), unstore=lambda key:storage.pop(key,None))
        main, chair = comp(main_storage,pixel),comp(chair_storage,chair_pixel)
        info = dict(old='old',new='new',mask='mask',chair_old='chair old',chair_new='chair new',owned=owned)
        names = dict(old_pixel='old',new_pixel='new',mask_pixel='mask',old_chair_pixel='chair_old',new_chair_pixel='chair_new')
        probe = SimpleNamespace(fetch=lambda *args:info,op=lambda name:SimpleNamespace(text=info[names[name]]),destroy=lambda:None)
        return pixel,chair_pixel,main_storage,chair_storage,main,chair,probe

    def test_gpu_failure_leaves_both_shaders_and_snapshot(self):
        pixel, cp, ms, cs, main, chair, probe = self.fixture()
        before = copy.deepcopy(cs['chair_owned'])
        with patch.object(update.transaction.shadow,'_validate',return_value=main), \
                patch.object(update.chairs,'validate',return_value=chair), \
                patch.object(update,'gpu_check',side_effect=RuntimeError('GPU failed')):
            with self.assertRaisesRegex(RuntimeError,'GPU failed'):update.install(lambda path:probe)
        self.assertEqual((pixel.text,cp.text),('old','chair old'))
        self.assertEqual(cs['chair_owned'],before)
        self.assertNotIn(update.BACKUP,ms)

    def test_compile_failure_restores_both_shaders_and_snapshot(self):
        pixel, cp, ms, cs, main, chair, probe = self.fixture()
        before = copy.deepcopy(cs['chair_owned'])
        with patch.object(update.transaction.shadow,'_validate',return_value=main), \
                patch.object(update.chairs,'validate',return_value=chair), \
                patch.object(update,'gpu_check',return_value=[]), \
                patch.object(update.routing,'digest',side_effect=RuntimeError('compile failed')):
            with self.assertRaisesRegex(RuntimeError,'compile failed'):update.install(lambda path:probe)
        self.assertEqual((pixel.text,cp.text),('old','chair old'))
        self.assertEqual(cs['chair_owned'],before)
        self.assertNotIn(update.BACKUP,ms)

    def test_success_changes_only_chair_text_hash_and_rollback_restores_both(self):
        pixel, cp, ms, cs, main, chair, probe = self.fixture()
        before = copy.deepcopy(cs['chair_owned'])
        engine, reader = ms['motion_engine'],cs['chair_reader']
        with patch.object(update.transaction.shadow,'_validate',return_value=main), \
                patch.object(update.chairs,'validate',return_value=chair), \
                patch.object(update,'gpu_check',return_value=[]), \
                patch.object(update.routing,'digest'), patch.object(update.routing,'assert_snapshot'):
            self.assertTrue(update.install(lambda path:probe)['passed'])
            self.assertEqual((pixel.text,cp.text),('new','chair new'))
            self.assertEqual(cs['chair_owned'][cp.path]['keep'],7)
            self.assertTrue(update.rollback(None)['restored'])
        self.assertEqual((pixel.text,cp.text),('old','chair old'))
        self.assertEqual(cs['chair_owned'],before)
        self.assertIs(ms['motion_engine'],engine)
        self.assertIs(cs['chair_reader'],reader)
