import threading
import unittest

from aisi.app.live_layout_worker import LiveLayoutWorker, StableLayoutProposal, current_source_poses, layout_job_key
from aisi.app.sim_scene_to_osc import send_layout_source_presence


class LiveLayoutWorkerTests(unittest.TestCase):
    def test_slow_planner_does_not_block_current_source_messages_or_queue_more_jobs(self):
        worker = LiveLayoutWorker()
        started, release = threading.Event(), threading.Event()
        calls = []
        def slow(value):
            calls.append(value); started.set()
            release.wait(3)
            return value
        class Client:
            def __init__(self): self.messages = []
            def send_message(self, address, value): self.messages.append((address, value))
        client = Client()
        try:
            self.assertEqual(worker.poll('same', slow, 1), (False, None))
            self.assertTrue(started.wait(1))
            for x in range(12):
                self.assertEqual(worker.poll('same', slow, x + 100), (False, None))
                send_layout_source_presence(client, {'tables': [{'id': 'a', 'x_cm': x}]},
                                            [{'id': 'a'}], refresh_poses=True)
            self.assertEqual(calls, [1])
            self.assertEqual([value for address, value in client.messages if address == '/table/0/source_x'],
                             list(range(12)))
            release.set(); worker._future.result(timeout=1)
            self.assertEqual(worker.poll('same', slow, 999), (True, 1))
        finally:
            release.set(); worker.close()

    def test_old_request_result_is_discarded_and_latest_request_is_started(self):
        worker = LiveLayoutWorker()
        try:
            worker.poll('old-count', lambda: 'old')
            worker._future.result(timeout=1)
            self.assertEqual(worker.poll('new-count', lambda: 'new'), (False, None))
            worker._future.result(timeout=1)
            self.assertEqual(worker.poll('new-count', lambda: None), (True, 'new'))
        finally: worker.close()

    def test_invalidated_format_and_invalid_layout_cannot_reuse_old_results(self):
        worker = LiveLayoutWorker()
        try:
            worker.poll('discussion', lambda: 'stale')
            worker._future.result(timeout=1)
            worker.invalidate()
            self.assertEqual(worker.poll('discussion', lambda: 'fresh'), (False, None))
            worker._future.result(timeout=1)
            self.assertEqual(worker.poll('discussion', lambda: None), (True, 'fresh'))
            def invalid(): raise ValueError('not enough tables')
            worker.poll('invalid', invalid)
            try: worker._future.result(timeout=1)
            except ValueError: pass
            with self.assertRaisesRegex(ValueError, 'not enough tables'):
                worker.poll('invalid', invalid)
            self.assertEqual(worker.poll('valid', lambda: 'recovered'), (False, None))
            worker._future.result(timeout=1)
            self.assertEqual(worker.poll('valid', lambda: None), (True, 'recovered'))
        finally: worker.close()

    def test_job_identity_keeps_moving_poses_but_rejects_parameter_id_and_geometry_changes(self):
        scene = {'roi': {'width_cm': 500}, 'tables': [{'id': 'a', 'x_cm': 10, 'type': 'rect', 'width_cm': 160}]}
        request = {'participants': 8, 'transformation_strength': 1}
        key = layout_job_key(scene, request)
        scene['tables'][0]['x_cm'] = 100
        self.assertEqual(layout_job_key(scene, request), key)
        self.assertNotEqual(layout_job_key(scene, dict(request, participants=9)), key)
        scene['tables'][0]['width_cm'] = 80
        self.assertNotEqual(layout_job_key(scene, request), key)
        scene['tables'][0]['width_cm'] = 160
        scene['tables'][0]['id'] = 'b'
        self.assertNotEqual(layout_job_key(scene, request), key)

    def test_finished_plan_uses_current_sources_without_slot_permutation(self):
        old = [{'id': 'a', 'x_cm': 1}, {'id': 'b', 'x_cm': 2}]
        current = {'tables': [{'id': 'b', 'x_cm': 222, 'rotation_deg': 35},
                              {'id': 'a', 'x_cm': 111}, {'id': 'new', 'x_cm': 999}]}
        output = current_source_poses(old, current)
        self.assertEqual([t['id'] for t in output], ['a', 'b'])
        self.assertEqual([t['x_cm'] for t in output], [111, 222])
        self.assertEqual(output[1]['rotation_deg'], 35)
        self.assertEqual(old, [{'id': 'a', 'x_cm': 1}, {'id': 'b', 'x_cm': 2}])

    def test_valid_proposal_keeps_targets_and_chairs_while_only_sources_move(self):
        cache = StableLayoutProposal()
        scene = {'tables': [{'id': 'a', 'x_cm': 1, 'rotation_deg': 0}]}
        request = {'learning_format': 'groupwork', 'participants': 4, 'layout_revision': 0}
        key = layout_job_key(scene, request)
        output = (scene['tables'], [], [{'x_cm': 300}], [{'x_cm': 250}], None)
        self.assertIsNone(cache.get(key))
        cache.store(key, output)
        for x in (20, 40, 100):
            scene['tables'][0].update(x_cm=x, rotation_deg=30)
            current = cache.get(layout_job_key(scene, request))
            self.assertEqual(current[2:4], output[2:4])
            tables = current_source_poses(current[0], scene)
            self.assertEqual(tables[0]['x_cm'], x)
            self.assertEqual(current[0][0]['x_cm'], 1)
        self.assertIsNone(cache.get(layout_job_key(scene, dict(request, layout_revision=1))))
        # Rückwechsel zu einer inzwischen verlassenen Anfrage erfordert ebenfalls neuen Vorschlag.
        self.assertIsNone(cache.get(key))

    def test_inventory_change_invalidates_frozen_proposal(self):
        cache = StableLayoutProposal()
        scene = {'tables': [{'id': 'a'}]}
        key = layout_job_key(scene, {})
        cache.store(key, ('valid',))
        scene['tables'].append({'id': 'b'})
        self.assertIsNone(cache.get(layout_job_key(scene, {})))


if __name__ == '__main__': unittest.main()
