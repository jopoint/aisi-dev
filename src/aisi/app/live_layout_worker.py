"""Ein Planungsauftrag neben dem Live-Versand, ohne anwachsende Warteschlange."""

from concurrent.futures import ThreadPoolExecutor
import json
from copy import deepcopy


def layout_job_key(scene, request, binding_present=False, active_track_id=None):
    """Posen dürfen weiterlaufen; andere Anfrage/IDs/Geometrie verwerfen alte Ergebnisse."""
    return (json.dumps(request, sort_keys=True), json.dumps(scene.get('roi'), sort_keys=True),
            tuple((t.get('id'), t.get('type'), t.get('width_cm'), t.get('height_cm'))
                  for t in scene.get('tables', [])), binding_present, active_track_id)


class LiveLayoutWorker:
    def __init__(self):
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix='aisi-layout')
        self._future = None
        self._key = None

    def poll(self, key, function, *args, **kwargs):
        if self._future is not None and not self._future.done():
            return False, None
        if self._future is not None:
            future, previous = self._future, self._key
            self._future = None
            if previous == key:
                return True, future.result()
        self._key = key
        self._future = self._executor.submit(function, *args, **kwargs)
        return False, None

    def invalidate(self):
        self._key = None

    def close(self):
        self._executor.shutdown(wait=False, cancel_futures=True)


class StableLayoutProposal:
    """Ein Vorschlag pro Anfrage/Inventar; Source-Bewegung ändert seine Ziele nicht."""
    def __init__(self):
        self.clear()

    def clear(self):
        self._key, self._output = None, None

    def get(self, key):
        if key != self._key:
            self._key, self._output = key, None
        return deepcopy(self._output)

    def store(self, key, output):
        self._key, self._output = key, deepcopy(output)


def current_source_poses(planned_tables, scene):
    """Nur aktuelle Source-Posen auffrischen; IDs/Slots/Ziele nicht neu zuordnen."""
    live = {str(t.get('id')): t for t in scene.get('tables', [])}
    result = []
    for table in planned_tables:
        updated = dict(table)
        source = live.get(str(table.get('id')))
        if source is not None:
            for field in ('x_cm', 'y_cm', 'rotation_deg'):
                if field in source:
                    updated[field] = source[field]
        result.append(updated)
    return result
