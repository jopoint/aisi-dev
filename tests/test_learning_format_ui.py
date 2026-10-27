"""UI rendering and HTTP edits preserve the explicit Motion activation boundary."""
import copy
from html.parser import HTMLParser
import json
import threading
import unittest
from unittest.mock import Mock, patch
from urllib.request import Request, urlopen
from http.server import HTTPServer

from aisi.app import learning_format_server as web
from aisi.app.learning_format_ui import build_motion_html


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
    def handle_starttag(self, tag, attributes):
        values = dict(attributes)
        if 'id' in values:
            self.ids.append(values['id'])


class LearningFormatUiTests(unittest.TestCase):
    def test_motion_page_removes_operational_prose_and_keeps_diagnostics_collapsed(self):
        html = build_motion_html(web.default_state())
        self.assertNotIn('Einstellungen sind vorgemerkt.',html)
        self.assertNotIn('Andere Tisch-IDs werden niemals',html)
        self.assertNotIn('name="transformation_strength"',html)
        self.assertIn('<details class="diagnostics">',html)
        parser = PageParser()
        parser.feed(html)
        self.assertEqual(len(parser.ids),len(set(parser.ids)))

    def test_json_settings_cannot_escape_script_element(self):
        state = web.default_state()
        state['extra'] = '</script><img src=x onerror=alert(1)>'
        self.assertNotIn(state['extra'],build_motion_html(state))

    def test_json_http_settings_do_not_activate_and_preserve_generator(self):
        state = web.default_state()
        state['adaptive_layout_preview'] = True
        runtime = Mock()
        runtime.status.return_value = {'revision':2,'pending_settings':True}
        server = HTTPServer(('127.0.0.1',0),web.LearningFormatHandler)
        server.motion = runtime
        thread = threading.Thread(target=server.serve_forever,daemon=True)
        thread.start()
        base = 'http://127.0.0.1:%s' % server.server_port
        try:
            with patch.object(web,'read_state',side_effect=lambda:copy.deepcopy(state)), \
                 patch.object(web,'write_state',side_effect=lambda value:state.update(value)):
                def post(body):
                    with urlopen(Request(base+'/set',data=body.encode(),headers={'Accept':'application/json'})) as response:
                        self.assertIn('application/json',response.headers['Content-Type'])
                        return json.load(response)
                payload = post('learning_format=groupwork&participants=9&number_of_groups=3&adaptive_layout_preview=on')
                self.assertEqual(payload['settings']['participants'],9)
                self.assertTrue(payload['settings']['adaptive_layout_preview'])
                runtime.activate.assert_not_called()
                post('action=activate_motion')
                runtime.activate.assert_called_once()
                self.assertEqual(runtime.activate.call_args.args[0]['number_of_groups'],3)
                with urlopen(base) as response:
                    self.assertIn('Wie lernen wir jetzt?',response.read().decode())
        finally:
            server.shutdown(); thread.join(timeout=2); server.server_close()
