import ast
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np
import test_motion_redisplay as fixtures
from td_builders import motion_group_success as group
from td_builders import update_motion_group_success as update
from td_builders import update_motion_visual_reveal as reveal
from td_builders import update_motion_feedback_size_cutouts as feedback
from td_builders import update_motion_target_dashes as dashes


class GroupSuccessTests(unittest.TestCase):
    def test_first_check_persists_until_last_then_all_reverse_together(self):
        record, scales = group.step(None, 1, {'a':True,'b':False}, 0, True)
        record, scales = group.step(record, 1, {'a':True,'b':False}, 30, True)
        self.assertAlmostEqual(scales['a'], 1)
        self.assertEqual(scales['b'], 0)
        record, scales = group.step(record, 1, {'a':True,'b':True}, 31, True)
        self.assertAlmostEqual(scales['a'], 1)
        self.assertAlmostEqual(scales['b'], 0)
        record, scales = group.step(record, 1, {'a':True,'b':True}, 31.5, True)
        self.assertEqual(scales['a'], scales['b'])
        record, scales = group.step(record, 1, {'a':True,'b':True}, 32.2, True)
        self.assertEqual(scales['a'], scales['b'])
        self.assertGreater(scales['a'], 0)
        record, scales = group.step(record, 1, {'a':True,'b':True}, 32.4, True)
        self.assertAlmostEqual(max(scales.values()), 0)
        record, scales = group.step(record, 1, {'a':True,'b':True}, 60, True)
        self.assertAlmostEqual(max(scales.values()), 0)

    def test_one_to_five_initially_complete_tables_pop_then_exit_together(self):
        for count in range(1, 6):
            completed = {str(i):True for i in range(count)}
            record, _ = group.step(None, 1, completed, 10, False)
            record, scales = group.step(record, 1, completed, 100, True)
            self.assertAlmostEqual(max(scales.values()), 0)
            record, scales = group.step(record, 1, completed, 100.5, True)
            self.assertTrue(all(abs(v-1)<1e-8 for v in scales.values()))
            record, scales = group.step(record, 1, completed, 101.4, True)
            self.assertAlmostEqual(max(scales.values()), 0)

    def test_tracking_failure_pauses_finish_without_replaying_arrival(self):
        done = {'a':True,'b':True}
        record, _ = group.step(None, 1, done, 0, True)
        record, scales = group.step(record, 1, done, .5, True)
        record, hidden = group.step(record, 1, done, .6, False)
        self.assertEqual(max(hidden.values()), 0)
        record, recovered = group.step(record, 1, done, 100, True)
        self.assertEqual(recovered, scales)
        self.assertEqual(record['finish'], .5)

    def test_reactivation_and_new_revision_clear_only_display_barrier(self):
        record, _ = group.step(None, 1, {'a':True,'b':True}, 0, True)
        record, _ = group.step(record, 1, {'a':True,'b':True}, 2, True)
        record, scales = group.step(record, 1, {'a':True,'b':False}, 3, True)
        self.assertAlmostEqual(scales['a'], 1)
        self.assertEqual(scales['b'], 0)
        self.assertIsNone(record['finish'])
        record, scales = group.step(record, 2, {'c':True}, 4, True)
        self.assertEqual(record['ids'], ('c',))
        self.assertAlmostEqual(scales['c'], 0)

    def test_missing_or_changed_id_cannot_finish_same_layout(self):
        record, _ = group.step(None, 1, {'a':True,'b':False}, 0, True)
        record, scales = group.step(record, 1, {'a':True}, 20, True)
        self.assertEqual(scales, {'a':0})
        self.assertIsNone(record['finish'])

    def test_inactive_initial_table_included_but_only_after_complete_reveal(self):
        owner = fixtures.RedisplayTests().owner()
        engine = SimpleNamespace(revision=1, tables={'a':SimpleNamespace(phase='completed')})
        data = np.zeros((6,6,4), np.float32)
        data[0,0] = (250,250,0,1)
        data[0,5] = (1,1,0,0)
        data[5,0] = (10,10,1,1)
        data[5,1] = (2,1,1,0)
        rows = [('a',(250,250,0),(250,250,0),True,False)]
        group.apply(owner, engine, rows, data, 10)
        self.assertEqual(data[0,5,2], 0)
        data[5,1,0] = 3
        group.apply(owner, engine, rows, data, 11)
        group.apply(owner, engine, rows, data, 11.5)
        self.assertAlmostEqual(data[0,5,2], 1)
        self.assertEqual(data[0,5,3], 1)
        self.assertEqual(data[0,5,0], 1)

    def test_actual_runtime_preserves_every_existing_state_channel(self):
        runtime = reveal.patch_runtime(Path('td_builders/motion_design.py').read_text(encoding='utf-8'))
        baseline, patched = {}, {}
        exec(runtime, baseline)
        exec(update.patch_runtime(runtime), patched)
        first, second = fixtures.RedisplayTests().owner(), fixtures.RedisplayTests().owner()
        first.op = second.op = lambda path: None
        for now in (0, 1, 3, 3.5, 4.5, 5):
            old = baseline['td_tick'](first, now)
            new = patched['td_tick'](second, now)
            np.testing.assert_array_equal(old[:5,:5], new[:5,:5])
            np.testing.assert_array_equal(old[:5,5,:2], new[:5,5,:2])
            np.testing.assert_array_equal(old[5], new[5])
        self.assertEqual(first.fetch('motion_engine').revision, second.fetch('motion_engine').revision)

    def test_patch_preserves_accepted_feedback_and_dashes(self):
        shader = feedback.patch_shader(dashes.patch_shader(Path('td_builders/motion_design.frag').read_text(encoding='utf-8')))
        new = update.patch_shader(shader)
        self.assertEqual(new.replace(update.OVERLAY, update.previous.OVERLAY), shader)
        with self.assertRaises(RuntimeError):
            update.patch_shader(new)
        runtime = reveal.patch_runtime(Path('td_builders/motion_design.py').read_text(encoding='utf-8'))
        self.assertEqual(update.patch_runtime(runtime).replace(update.NEW_RETURN, update.RETURN), runtime)
        with self.assertRaises(RuntimeError):
            update.patch_runtime(runtime.replace(update.STATE, update.STATE.replace(', 1, 0, 0)', ', 1, 9, 9)')))

    def test_python39(self):
        for module in (group, update):
            ast.parse(Path(module.__file__).read_text(encoding='utf-8'), feature_version=(3,9))


class GroupSuccessTransactionTests(unittest.TestCase):
    def fixture(self):
        values = fixtures.RedisplayTests().installation_fixture()
        values[2]['motion_engine'].started = 1
        return values

    def test_gpu_failure_does_not_change_runtime_or_shader(self):
        pixel, runtime, storage, comp, probe = self.fixture()
        with patch.object(update.transaction.shadow, '_validate', return_value=comp), \
                patch.object(update, 'gpu_check', side_effect=RuntimeError('GPU failed')):
            with self.assertRaisesRegex(RuntimeError, 'GPU failed'):
                update.install(lambda path:probe)
        self.assertEqual((pixel.text,runtime.text), ('old shader','old runtime'))
        self.assertNotIn(update.BACKUP, storage)

    def test_render_failure_restores_both_dats_and_display_storage(self):
        pixel, runtime, storage, comp, probe = self.fixture()
        with patch.object(update.transaction.shadow, '_validate', return_value=comp), \
                patch.object(update, 'gpu_check', return_value=[]), \
                patch.object(update.routing, 'digest', side_effect=RuntimeError('compile failed')):
            with self.assertRaisesRegex(RuntimeError, 'compile failed'):
                update.install(lambda path:probe)
        self.assertEqual((pixel.text,runtime.text), ('old shader','old runtime'))
        self.assertNotIn(group.KEY, storage)
        self.assertNotIn(update.BACKUP, storage)

    def test_install_and_rollback_preserve_engine_reader_and_older_backup(self):
        pixel, runtime, storage, comp, probe = self.fixture()
        before = storage.copy()
        with patch.object(update.transaction.shadow, '_validate', return_value=comp), \
                patch.object(update, 'gpu_check', return_value=[]), patch.object(update.routing, 'digest'):
            self.assertTrue(update.install(lambda path:probe)['passed'])
            self.assertTrue(update.rollback(None)['restored'])
        self.assertEqual(storage, before)
        self.assertEqual((pixel.text,runtime.text), ('old shader','old runtime'))
