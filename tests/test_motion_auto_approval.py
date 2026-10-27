"""Deterministic frame separation and fail-closed automatic output approval."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock

from td_builders.motion_auto_approval import Approval
from td_builders.install_motion_auto_approval import callback_text
from aisi.app.motion_td_status import read_approval, outputs_confirmed_off


class AutoApprovalTests(unittest.TestCase):
    def setUp(self):
        self.machine = Approval()
        self.report = dict(passed=True, live_stream=dict(fresh=True, ids=['table_01'],
                           signature=(100, 10), layout=('osc', 100, 2)))
        self.sample = Mock(side_effect=lambda: copy.deepcopy(self.report))
        self.verify = Mock(side_effect=lambda: copy.deepcopy(self.report))
        self.confirm = Mock(side_effect=lambda: copy.deepcopy(self.report))
        self.enable, self.disable = Mock(), Mock()

    def step(self, now=0, frame=1, mode=True):
        self.machine.step(now, frame, mode, self.sample, self.verify,
                          self.confirm, self.enable, self.disable)

    def active(self):
        self.step()
        self.report['live_stream']['signature'] = (100, 11)
        self.step(.1, 2)
        self.step(.2, 3)
        self.assertEqual(self.machine.phase, 'active')

    def test_requires_full_proof_later_td_frame_advancing_source_and_postcheck(self):
        self.step()
        self.assertEqual(self.machine.phase, 'confirming')
        self.enable.assert_not_called()
        self.step(.01, 1)
        self.step(.1, 2)
        self.enable.assert_not_called()
        self.report['live_stream']['signature'] = (100, 11)
        self.step(.2, 3)
        self.enable.assert_called_once()
        self.assertEqual(self.machine.phase, 'checking_output')
        self.step(.3, 4)
        self.assertEqual(self.machine.phase, 'active')
        self.assertEqual(self.verify.call_count, 2)

    def test_active_does_not_repeat_gpu_proof_or_generate_layout(self):
        self.active()
        self.verify.reset_mock()
        self.step(1, 20)
        self.verify.assert_not_called()

    def test_stale_source_disables_and_recovery_rechecks(self):
        self.active()
        self.report['passed'] = False
        self.step(.3, 4)
        self.assertEqual(self.machine.phase, 'waiting')
        self.report['passed'] = True
        previous = self.verify.call_count
        self.step(.4, 5)
        self.assertEqual(self.verify.call_count, previous)
        self.step(2.4, 6)
        self.assertEqual(self.machine.phase, 'confirming')

    def test_failed_gpu_proof_never_enables_and_has_retry_backoff(self):
        self.verify.side_effect = ValueError('Maskenabweichung')
        self.step()
        self.enable.assert_not_called()
        self.step(.1, 2)
        self.assertEqual(self.verify.call_count, 1)
        self.assertIn('Maskenabweichung', self.machine.message)

    def test_new_revision_or_session_revokes_approval_before_rechecking(self):
        for key in (('osc', 100, 3), ('osc', 200, 2)):
            self.setUp()
            self.active()
            self.report['live_stream']['layout'] = key
            self.step(.3, 4)
            self.assertEqual(self.machine.phase, 'confirming')
            self.assertEqual(self.enable.call_count, 1)

    def test_modes_zero_one_and_simulation_never_enable(self):
        self.active()
        self.step(.3, 4, False)
        self.assertEqual(self.machine.phase, 'waiting')
        self.assertIsNone(self.machine.key)

    def test_failed_post_enable_proof_revokes_output(self):
        self.step()
        self.report['live_stream']['signature'] = (100, 11)
        self.step(.1, 2)
        self.verify.side_effect = ValueError('Nachkontrolle fehlgeschlagen')
        count = self.disable.call_count
        self.step(.2, 3)
        self.assertGreater(self.disable.call_count, count)
        self.assertEqual(self.machine.phase, 'waiting')

    def test_changed_source_during_proof_or_confirmation_fails_closed(self):
        for stage in ('proof', 'confirmation'):
            self.setUp()
            if stage == 'confirmation':
                self.step()
            changed = copy.deepcopy(self.report)
            changed['live_stream']['ids'] = ['other']
            callback = self.verify if stage == 'proof' else self.confirm
            callback.side_effect = lambda: changed
            self.step(.1, 2)
            self.enable.assert_not_called()
            self.assertEqual(self.machine.phase, 'waiting')

    def test_callback_compiles_for_saved_windows_path_and_fails_closed(self):
        source = callback_text(Path('C:/dev/Promotion_Prototypen/AISI'))
        compile(source, 'callbacks', 'exec')
        self.assertIn('def onStart()', source)
        self.assertIn('safe_off()', source)
        self.assertNotIn('project.save', source)


class ApprovalStatusTests(unittest.TestCase):
    def test_automatic_reconnect_requires_fresh_positive_off_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'status.json'
            data = dict(updated_at=100, automatic=True, enabled=True, output_flags=[False,False])
            path.write_text(json.dumps(data))
            self.assertTrue(outputs_confirmed_off(path,101))
            self.assertFalse(outputs_confirmed_off(path,104))
            for field, value in (('enabled',False),('automatic',False),('output_flags',[True,False])):
                changed = dict(data, **{field:value})
                path.write_text(json.dumps(changed))
                self.assertFalse(outputs_confirmed_off(path,101))

    def test_status_requires_recent_matching_session_revision_and_ids(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'status.json'
            data = dict(updated_at=100, approved=True, layout=['osc', 1, 2], ids=['a'], message='ok')
            path.write_text(json.dumps(data))
            self.assertTrue(read_approval(1, 2, ['a'], path, 101)['approved'])
            for session, revision, ids, now in ((2,2,['a'],101), (1,3,['a'],101),
                                              (1,2,['b'],101), (1,2,['a'],104)):
                self.assertFalse(read_approval(session, revision, ids, path, now)['approved'])
            path.write_text('broken')
            self.assertFalse(read_approval(1, 2, ['a'], path, 101)['approved'])


class AutoApprovalInstallTests(unittest.TestCase):
    def setUp(self):
        from unittest.mock import patch
        from test_motion_live_output import LiveOutputTests
        from test_motion_output_routing import Node
        self.helper = LiveOutputTests()
        self.helper.setUp()
        self.addCleanup(self.helper.doCleanups)
        self.helper.prepare()
        self.graph = self.helper.graph
        self.startup = patch.object(Node, 'storeStartupValue', lambda *args: None, create=True)
        self.startup.start()
        self.addCleanup(self.startup.stop)

    def test_prepare_is_passive_install_disables_flags_and_rollback_only_removes_owned_component(self):
        from td_builders import install_motion_auto_approval as installer
        self.helper.comp.par.Enablemotion = True
        self.helper.comp.par.Sourceapproved = True
        report = installer.prepare(self.graph.get, dict(containerCOMP='container', executeDAT='execute'))
        self.assertTrue(report['prepared'])
        self.assertTrue(self.helper.comp.par.Enablemotion.eval())
        with self.assertRaises(RuntimeError):
            installer.prepare(self.graph.get, dict(containerCOMP='container', executeDAT='execute'))
        self.assertTrue(installer.install(self.graph.get)['automatic_approval_armed'])
        self.assertFalse(self.helper.comp.par.Enablemotion.eval())
        self.assertFalse(self.helper.comp.par.Sourceapproved.eval())
        self.assertTrue(installer.rollback(self.graph.get)['removed'])
        self.assertNotIn(installer.PATH, self.graph)

    def test_local_callback_or_extra_node_blocks_removal(self):
        from td_builders import install_motion_auto_approval as installer
        from test_motion_output_routing import Node
        installer.prepare(self.graph.get, dict(containerCOMP='container', executeDAT='execute'))
        Node(self.graph, installer.PATH+'/local_node')
        with self.assertRaises(RuntimeError):
            installer.rollback(self.graph.get)
