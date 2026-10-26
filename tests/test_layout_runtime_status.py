import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from aisi.app.layout_runtime_status import LayoutStatusPublisher, read_status, request_key
from aisi.app.learning_format_server import build_html, default_state


class LayoutRuntimeStatusTests(unittest.TestCase):
    def test_invalid_request_and_recovery_keep_same_request_and_current_count(self):
        state = default_state()
        state.update(learning_format='discussion', participants=7, adaptive_layout_preview=True)
        key = request_key('discussion', 1, state)
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'status.json'
            publisher = LayoutStatusPublisher(path)
            publisher.publish(key, 'invalid', 2, 'Discussion benötigt für 7 Personen 4 Tische; nur 2 verfügbar.')
            result = read_status(state, path)
            self.assertEqual(result['state'], 'invalid')
            self.assertEqual(result['available_tables'], 2)
            self.assertIn('4 Tische', result['message'])
            publisher.publish(key, 'ready', 4, 'Layout aktiv.')
            self.assertEqual(read_status(state, path)['state'], 'ready')
            self.assertEqual(read_status(state, path)['available_tables'], 4)

    def test_old_request_cannot_be_displayed_as_current(self):
        state = default_state()
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'status.json'
            LayoutStatusPublisher(path).publish(request_key('groupwork', 1, state), 'ready', 2)
            for field, value in (('learning_format', 'input'), ('participants', 9),
                                 ('number_of_groups', 3), ('presentation_side', 'north'),
                                 ('adaptive_layout_preview', True), ('transformation_strength', .5),
                                 ('layout_revision', 1)):
                with self.subTest(field=field):
                    self.assertEqual(read_status(dict(state, **{field: value}), path)['state'], 'pending')

    def test_missing_malformed_or_stale_status_is_not_ready(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'status.json'
            self.assertEqual(read_status(default_state(), path)['state'], 'unavailable')
            path.write_text('broken')
            self.assertEqual(read_status(default_state(), path)['state'], 'unavailable')
            publisher = LayoutStatusPublisher(path)
            with patch('aisi.app.layout_runtime_status.time.time', return_value=1):
                publisher.publish(request_key('groupwork', 1, default_state()), 'ready', 2)
            self.assertEqual(read_status(default_state(), path)['state'], 'unavailable')

    def test_write_failure_does_not_stop_sender_and_retries(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'status.json'
            publisher = LayoutStatusPublisher(path)
            with patch('aisi.app.layout_runtime_status.os.replace', side_effect=PermissionError):
                publisher.publish({}, 'ready', 2)
            self.assertFalse(path.exists())
            publisher.publish({}, 'ready', 2)
            self.assertTrue(path.exists())
            self.assertEqual(list(path.parent.glob('*.tmp')), [])

    def test_refresh_is_throttled_but_count_changes_are_immediate(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'status.json'
            publisher = LayoutStatusPublisher(path)
            with patch('aisi.app.layout_runtime_status.time.monotonic', return_value=10):
                publisher.publish({}, 'ready', 2)
                with patch('aisi.app.layout_runtime_status.os.replace') as replace:
                    publisher.publish({}, 'ready', 2)
                    replace.assert_not_called()
                publisher.publish({}, 'ready', 3)
            self.assertEqual(json.loads(path.read_text())['available_tables'], 3)

    def test_page_polls_status_without_reloading_form_or_injecting_message_html(self):
        html = build_html('discussion', True, True, 1)
        self.assertIn('fetch("/layout-status"', html)
        self.assertIn('setInterval(updateLayoutStatus, 1000)', html)
        self.assertIn('box.textContent', html)
        self.assertNotIn('box.innerHTML', html)
        self.assertIn('Zielvorschlag bleibt stehen und ist veraltet', html)


if __name__ == '__main__':
    unittest.main()
