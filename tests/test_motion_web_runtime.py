"""Web activation remains an explicit, atomic layout boundary."""
import copy
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from aisi.app.motion_web_runtime import MotionWebRuntime, enhance_html
from aisi.app.motion_layout_proposal import MotionProposal
from aisi.app.motion_sender_lock import MotionSenderLock
from test_motion_live_adapter import frame, EPOCH


class MotionWebRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / 'camera.jsonl'
        self.path.write_bytes(b'')
        self.settings = dict(learning_format='input', participants=2,
                             transformation_strength=.2, layout_revision=0)
        self.proposal = MotionProposal((('a', (200, 200, 0)), ('b', (350, 300, 0))),
                                       ((200, 180, 20, 'a'),), True, 'input')
        self.seen = []
        def planner(tables, settings):
            self.seen.append(copy.deepcopy(settings))
            return self.proposal
        self.runtime = MotionWebRuntime(self.path, planner=planner)
        self.clock = patch('aisi.app.motion_web_runtime.time.monotonic', return_value=.1)
        self.clock.start()
        self.runtime.controller.adapter.ingest(frame(10), 0, EPOCH)
        self.runtime.controller.adapter.ingest(frame(11), .1, EPOCH+.1)

    def tearDown(self):
        self.clock.stop()
        self.temp.cleanup()

    def finish(self):
        deadline = time.time()+2
        while self.runtime.results.empty() and time.time()<deadline:
            time.sleep(.005)
        self.runtime.tick()

    def test_settings_do_not_activate_and_explicit_activation_freezes_snapshot(self):
        self.assertTrue(self.runtime.status(self.settings)['pending_settings'])
        self.assertIsNone(self.runtime.controller.proposal)
        self.assertTrue(self.runtime.activate(self.settings))
        self.settings['participants'] = 9
        self.finish()
        self.assertEqual(self.seen[0]['participants'], 2)
        self.assertEqual(self.seen[0]['transformation_strength'], 1)
        self.assertEqual(self.runtime.controller.revision, 2)
        self.assertTrue(self.runtime.status(self.settings)['pending_settings'])
        self.assertGreaterEqual(self.runtime.status(self.settings)['planning_seconds'], 0)
        self.runtime.tick()
        self.assertEqual(self.runtime.controller.revision, 2)

    def test_busy_rejects_duplicate_activation_and_failed_plan_preserves_layout(self):
        self.runtime.activate(self.settings)
        self.assertFalse(self.runtime.activate(self.settings))
        self.finish()
        old = self.runtime.controller.proposal
        def fail(*args):
            raise ValueError('Nicht genügend Tische')
        self.runtime.planner = fail
        self.runtime.activate(self.settings)
        self.finish()
        self.assertIs(self.runtime.controller.proposal, old)
        self.assertEqual(self.runtime.controller.revision, 2)
        self.assertIn('Nicht genügend Tische', self.runtime.message)
        self.assertGreaterEqual(self.runtime.status(self.settings)['planning_seconds'], 0)

    def test_changed_inventory_during_planning_cannot_commit(self):
        self.runtime.activate(self.settings)
        self.runtime.controller.adapter.ingest(frame(12, ('other',)), .1, EPOCH+.1)
        self.finish()
        self.assertIsNone(self.runtime.controller.proposal)
        self.assertEqual(self.runtime.controller.revision, 1)

    def test_reconnect_starts_blank_session_without_automatic_proposal(self):
        self.runtime.activate(self.settings)
        self.finish()
        previous = self.runtime.controller.session
        self.runtime.reconnect()
        self.assertIsNone(self.runtime.controller.proposal)
        self.assertEqual(self.runtime.controller.revision, 1)
        self.assertNotEqual(self.runtime.controller.session, previous)
        self.assertFalse(self.runtime.status(self.settings)['camera_fresh'])

    def test_functional_ui_exposes_activation_without_manual_reconnect(self):
        html = enhance_html('<body>settings</body>')
        self.assertIn('activate_motion', html)
        self.assertNotIn('name="outputs_off"', html)
        self.assertNotIn('value="reconnect_motion"', html)
        self.assertIn('/motion-status', html)
        self.assertIn('TD-Ausgabe', html)
        self.assertGreater(html.index('<script>'), html.index('settings'))

    def feed(self, frames, off=True):
        with patch('aisi.app.motion_web_runtime.read_new_jsonl_lines', return_value=(0,b'',frames)), \
             patch('aisi.app.motion_web_runtime._frame_from_json_line', side_effect=lambda value:value), \
             patch('aisi.app.motion_web_runtime.time.time', return_value=EPOCH+.1), \
             patch('aisi.app.motion_td_status.outputs_confirmed_off', return_value=off):
            self.runtime.tick()

    def test_camera_restart_reconnects_only_after_td_off_without_reusing_old_proposal(self):
        self.runtime.activate(self.settings)
        self.finish()
        old = self.runtime.controller.proposal
        self.feed([frame(0)], off=False)
        self.assertFalse(self.runtime.controller.requires_activation)
        self.assertFalse(self.runtime.status(self.settings)['camera_fresh'])
        self.feed([frame(1)], off=True)
        self.assertTrue(self.runtime.controller.requires_activation)
        self.assertFalse(self.runtime.status(self.settings)['camera_fresh'])
        self.feed([frame(2)], off=True)
        self.assertTrue(self.runtime.status(self.settings)['camera_fresh'])
        self.assertIs(self.runtime.controller.proposal, old)
        self.assertEqual(self.runtime.controller.revision, 2)
        values = self.runtime.controller.values(.1)
        self.assertEqual(values['aisi_motion/count'], 0)
        self.assertEqual(values['aisi_motion/chairs/count'], 0)
        self.assertTrue(self.runtime.activate(self.settings))
        self.finish()
        self.assertEqual(self.runtime.controller.revision, 3)
        self.assertFalse(self.runtime.controller.requires_activation)

    def test_restart_does_not_accept_changed_calibration_or_commit_old_worker(self):
        self.runtime.activate(self.settings)
        old_queue = self.runtime.results
        self.feed([frame(0)], off=True)
        self.assertIsNone(self.runtime.results)
        self.assertIsNone(self.runtime.controller.proposal)
        self.assertIsNotNone(old_queue)
        changed = frame(1)
        changed.world['calibration_id'] = 'different'
        self.feed([changed], off=True)
        self.assertFalse(self.runtime.status(self.settings)['camera_fresh'])
        self.assertEqual(self.runtime.controller.adapter.reset_reason, 'calibration')

    def test_sender_lock_rejects_second_writer_and_releases_on_close(self):
        path = Path(self.temp.name) / 'sender.lock'
        first = MotionSenderLock(path)
        try:
            with self.assertRaises(RuntimeError):
                MotionSenderLock(path)
        finally:
            first.close()
        MotionSenderLock(path).close()


class MotionWebHttpTests(unittest.TestCase):
    def test_settings_and_activation_are_separate_http_actions(self):
        import json
        import threading
        from http.server import HTTPServer
        from urllib.request import urlopen, Request
        from unittest.mock import Mock
        from aisi.app import learning_format_server as web
        state = web.default_state() if hasattr(web, 'default_state') else {
            'learning_format':'input', 'show_persons':False, 'show_chairs':True,
            'transformation_strength':1., 'participants':2, 'number_of_groups':2,
            'presentation_side':None, 'adaptive_layout_preview':True, 'layout_revision':0}
        runtime = Mock()
        runtime.status.return_value = {'revision':1}
        server = HTTPServer(('127.0.0.1', 0), web.LearningFormatHandler)
        server.motion = runtime
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = 'http://127.0.0.1:%d' % server.server_port
        try:
            with patch.object(web, 'read_state', side_effect=lambda: copy.deepcopy(state)), \
                 patch.object(web, 'write_state', side_effect=lambda value: state.update(value)):
                def post(data):
                    with urlopen(Request(base+'/set', data=data.encode())) as response:
                        return response.read().decode()
                self.assertIn('activate_motion', post('learning_format=groupwork'))
                runtime.activate.assert_not_called()
                post('participants=3')
                runtime.activate.assert_not_called()
                post('action=activate_motion')
                self.assertEqual(runtime.activate.call_args.args[0]['participants'], 3)
                self.assertEqual(runtime.activate.call_args.args[0]['learning_format'], 'groupwork')
                post('action=reconnect_motion')
                runtime.reconnect.assert_not_called()
                post('action=reconnect_motion&outputs_off=yes')
                runtime.reconnect.assert_called_once()
                with urlopen(base+'/motion-status') as response:
                    self.assertEqual(json.load(response), {'revision':1})
        finally:
            server.shutdown()
            thread.join(timeout=2)
            server.server_close()


if __name__ == '__main__':
    unittest.main()
