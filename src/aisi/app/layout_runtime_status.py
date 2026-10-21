"""Lokaler Senderstatus für die Lernformat-Oberfläche, ohne Layoutberechnung."""

from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
import time


def status_path() -> Path:
    return Path(__file__).resolve().parents[3] / 'data/aisi/state/layout_status.json'


def request_key(mode: str, strength: float, parameters: dict) -> dict:
    return {'learning_format': mode, 'transformation_strength': float(strength),
            **{name: parameters.get(name, default) for name, default in (
                ('participants', 4), ('number_of_groups', 2),
                ('presentation_side', None), ('adaptive_layout_preview', False))}}


class LayoutStatusPublisher:
    def __init__(self, path: Path | None = None):
        self.path = path or status_path()
        self._last_payload = None
        self._last_write = 0.0

    def publish(self, request: dict, state: str, available_tables: int, message: str = '') -> None:
        payload = {'request': request, 'state': state,
                   'available_tables': available_tables, 'message': message}
        now = time.monotonic()
        if payload == self._last_payload and now - self._last_write < 1.0:
            return
        temporary = None
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8',
                    dir=self.path.parent, suffix='.tmp', delete=False) as handle:
                temporary = handle.name
                json.dump(dict(payload, updated_at=time.time()), handle, ensure_ascii=False)
            os.replace(temporary, self.path)
        except OSError:
            return  # Status darf die laufende OSC-Ausgabe nicht unterbrechen.
        else:
            self._last_payload, self._last_write = payload, now
        finally:
            if temporary and os.path.exists(temporary):
                try:
                    os.unlink(temporary)
                except OSError:
                    pass


def read_status(state: dict, path: Path | None = None) -> dict:
    try:
        payload = json.loads((path or status_path()).read_text(encoding='utf-8'))
        if time.time() - float(payload['updated_at']) > 15:
            raise ValueError('Status veraltet')
        expected = request_key(str(state['learning_format']), float(state['transformation_strength']), state)
        if payload['request'] != expected:
            return {'state': 'pending', 'message': 'Neue Anfrage wird übernommen.'}
        return payload
    except (OSError, ValueError, KeyError, TypeError):
        return {'state': 'unavailable', 'message': 'Keine aktuelle Rückmeldung vom Layout-Sender.'}
