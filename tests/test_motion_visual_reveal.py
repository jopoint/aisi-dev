"""A separate visual clock waits for proof without resetting Motion state."""
import ast
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np
import test_motion_redisplay as fixtures
from td_builders import motion_visual_reveal as visual
from td_builders import update_motion_visual_reveal as update
from td_builders.motion_design import td_tick


class VisualClockTests(unittest.TestCase):
    def test_arbitrarily_long_proof_cannot_consume_reveal_time(self):
        record = None
        for now in (1,2,4,30):
            record, age = visual.clock(record, ('osc',1,2), now, False)
            self.assertEqual(age,0)
            self.assertIsNone(record['started'])
        record, age = visual.clock(record, ('osc',1,2), 31, True)
        self.assertEqual(age,0)
        self.assertAlmostEqual(visual.clock(record, ('osc',1,2), 33.9, True)[1],2.9)
        self.assertEqual(visual.clock(record, ('osc',1,2), 34, True)[1],3)

    def test_recovery_and_modes_do_not_restart_same_revision(self):
        record, _ = visual.clock(None, ('osc',1,2), 10, True)
        visual.clock(record, ('osc',1,2), 11, False)
        same, age = visual.clock(record, ('osc',1,2), 20, True)
        self.assertIs(same,record)
        self.assertEqual(age,10)
        fresh, age = visual.clock(record, ('osc',1,3), 21, False)
        self.assertEqual(age,0)
        self.assertIsNone(fresh['started'])

    def test_actual_runtime_changes_only_visual_clock_and_marker(self):
        baseline = fixtures.RedisplayTests().owner()
        owner = fixtures.RedisplayTests().owner()
        for item in (baseline, owner):
            item.par.Sourcex.val = 300
        class Par:
            def eval(self): return True
        controller = SimpleNamespace(phase='waiting', key=(('manual',2),('preview_table',)))
        auto = SimpleNamespace(par=SimpleNamespace(Enabled=Par()), fetch=lambda *args:controller)
        routing = SimpleNamespace(par=SimpleNamespace(Enablemotion=Par(), Sourceapproved=Par()))
        owner.op = lambda path:{visual.AUTO:auto,visual.ROUTING:routing}.get(path)
        namespace = {'__name__':'patched_motion_runtime'}
        exec(update.patch_runtime(Path('td_builders/motion_design.py').read_text()),namespace)
        tick = namespace['td_tick']
        for now in (0,10):
            original, actual = td_tick(baseline,now), tick(owner,now)
            np.testing.assert_array_equal(original[:5],actual[:5])
            np.testing.assert_array_equal(original[5,0],actual[5,0])
            self.assertEqual(tuple(actual[5,1]),(0,0,1,0))
        engine = owner.fetch('motion_engine')
        revision, started, tables = engine.revision,engine.started,dict(engine.tables)
        controller.phase = 'checking_output'
        self.assertEqual(tick(owner,11)[5,1,1],0)
        controller.phase = 'active'
        first = tick(owner,12)
        self.assertEqual(first[5,1,0],0)
        self.assertEqual(first[5,1,1],1)
        self.assertAlmostEqual(tick(owner,12.5)[5,1,0],.5)
        self.assertEqual((engine.revision,engine.started),(revision,started))
        for key, table in tables.items():
            self.assertIs(engine.tables[key],table)

    def test_old_approval_for_another_revision_does_not_release_clock(self):
        owner = fixtures.RedisplayTests().owner()
        par = SimpleNamespace(eval=lambda:True)
        controller = SimpleNamespace(phase='active',key=(('osc',1,2),('a',)))
        auto = SimpleNamespace(par=SimpleNamespace(Enabled=par),fetch=lambda *args:controller)
        routing = SimpleNamespace(par=SimpleNamespace(Enablemotion=par,Sourceapproved=par))
        owner.op = lambda path:{visual.AUTO:auto,visual.ROUTING:routing}.get(path)
        engine = SimpleNamespace(revision=('osc',1,3))
        age,ready,managed = visual.display_state(owner,engine,10,8,True)
        self.assertEqual((age,ready,managed),(0,False,True))

    def test_legacy_mode_without_automatic_component_is_unchanged(self):
        owner = SimpleNamespace(op=lambda path:None)
        self.assertEqual(visual.display_state(owner,None,10,8,True),(8,True,False))

    def test_patches_preserve_all_unrelated_runtime_and_shader_text(self):
        runtime = Path('td_builders/motion_design.py').read_text()+'\n# local note\n'
        shader = Path('td_builders/motion_design.frag').read_text()+'\n// local note\n'
        self.assertEqual(update.patch_runtime(runtime).replace(update.NEW_RUNTIME,update.RUNTIME,1),runtime)
        self.assertEqual(update.patch_shader(shader).replace(update.NEW_SHADER,update.SHADER,1),shader)
        with self.assertRaises(RuntimeError): update.patch_runtime(runtime+update.RUNTIME)
        with self.assertRaises(RuntimeError): update.patch_shader(shader+update.SHADER)

    def test_python39_syntax(self):
        for name in ('motion_visual_reveal.py','update_motion_visual_reveal.py'):
            ast.parse(Path('td_builders',name).read_text(),feature_version=(3,9))


class RevealTransactionTests(unittest.TestCase):
    def fixture(self):
        pixel,runtime,storage,comp,probe = fixtures.RedisplayTests().installation_fixture()
        storage['motion_engine'].started = 1
        comp.storeStartupValue = lambda *args:None
        return pixel,runtime,storage,comp,probe

    def test_gpu_failure_does_not_change_production(self):
        pixel,runtime,storage,comp,probe = self.fixture()
        with patch.object(update.transaction.shadow,'_validate',return_value=comp), \
             patch.object(update,'gpu_check',side_effect=RuntimeError('GPU failed')):
            with self.assertRaisesRegex(RuntimeError,'GPU failed'):
                update.install(lambda path:probe)
        self.assertEqual((pixel.text,runtime.text),('old shader','old runtime'))
        self.assertNotIn(visual.KEY,storage)

    def test_success_and_rollback_preserve_engine_reader_revision_and_other_backups(self):
        pixel,runtime,storage,comp,probe = self.fixture()
        original = storage.copy()
        with patch.object(update.transaction.shadow,'_validate',return_value=comp), \
             patch.object(update,'gpu_check',return_value=[]), patch.object(update.routing,'digest'):
            self.assertTrue(update.install(lambda path:probe)['passed'])
            self.assertTrue(update.rollback(None)['restored'])
        self.assertEqual(storage,original)
        self.assertEqual((pixel.text,runtime.text),('old shader','old runtime'))

    def test_compile_failure_restores_both_dats_and_visual_state(self):
        pixel,runtime,storage,comp,probe = self.fixture()
        with patch.object(update.transaction.shadow,'_validate',return_value=comp), \
             patch.object(update,'gpu_check',return_value=[]), \
             patch.object(update.routing,'digest',side_effect=RuntimeError('compile failed')):
            with self.assertRaisesRegex(RuntimeError,'compile failed'):
                update.install(lambda path:probe)
        self.assertEqual((pixel.text,runtime.text),('old shader','old runtime'))
        self.assertNotIn(visual.KEY,storage)
