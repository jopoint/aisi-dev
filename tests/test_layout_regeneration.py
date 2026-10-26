import io
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from aisi.app import learning_format_server as server
from aisi.app.layout_runtime_status import request_key
from aisi.app.sim_scene_to_osc import load_activity_parameters


class LayoutRegenerationTests(unittest.TestCase):
    def post(self, state, body):
        handler = object.__new__(server.LearningFormatHandler)
        handler.path = '/set'
        handler.headers = {'Content-Length': str(len(body))}
        handler.rfile, handler.wfile = io.BytesIO(body), io.BytesIO()
        handler.send_response = lambda *args: None
        handler.send_header = lambda *args: None
        handler.end_headers = lambda: None
        with patch.object(server, 'read_state', return_value=dict(state)), patch.object(server, 'write_state') as write:
            handler.do_POST()
            return write.call_args.args[0]

    def test_regenerate_changes_only_revision_and_new_page_has_button(self):
        state = dict(server.default_state(), presentation_side='east', adaptive_layout_preview=True)
        updated = self.post(state, b'action=regenerate')
        self.assertEqual(updated, dict(state, layout_revision=1))
        self.assertNotEqual(request_key('input', 1, state), request_key('input', 1, updated))
        self.assertIn('value="regenerate"', server.build_html('input', True, True, 1))

    def test_visibility_toggle_preserves_revision_layout_and_presentation_side(self):
        state = dict(server.default_state(), presentation_side='east', layout_revision=4)
        updated = self.post(state, b'toggle=chairs')
        self.assertEqual(updated, dict(state, show_chairs=False))
        self.assertEqual(request_key('input', 1, state), request_key('input', 1, updated))

    def test_revision_is_saved_and_loaded_by_ui_and_sender(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / 'state.json'
            with patch.object(server, 'state_file_path', return_value=path):
                state = dict(server.default_state(), layout_revision=12)
                self.assertTrue(server.write_state(state))
                self.assertEqual(server.read_state()['layout_revision'], 12)
                self.assertEqual(load_activity_parameters(path)['layout_revision'], 12)


if __name__ == '__main__': unittest.main()
