"""Read only the local TD heartbeat, bound to the current Motion layout."""
import json
from pathlib import Path
import time


def outputs_confirmed_off(path=None, now=None):
    path = Path(path) if path else Path(__file__).resolve().parents[3] / 'data/aisi/state/motion_td_approval.json'
    now = time.time() if now is None else now
    try:
        status = json.loads(path.read_text(encoding='utf-8'))
        age = now - float(status['updated_at'])
        return (0 <= age <= 3 and status.get('automatic') is True and
                status.get('enabled') is True and status.get('output_flags') == [False, False])
    except (OSError, ValueError, KeyError, TypeError):
        return False


def read_approval(session, revision, ids, path=None, now=None):
    path = Path(path) if path else Path(__file__).resolve().parents[3] / 'data/aisi/state/motion_td_approval.json'
    now = time.time() if now is None else now
    try:
        status = json.loads(path.read_text(encoding='utf-8'))
        age = now - float(status['updated_at'])
        if not 0 <= age <= 3:
            return dict(approved=False, message='Keine aktuelle TD-Rückmeldung. TD öffnen und Play prüfen.')
        if status.get('layout') is None:
            return dict(approved=False, message=status.get('message', 'TD wartet auf Quelle.'))
        if status.get('layout') != ['osc', session, revision] or sorted(status.get('ids', [])) != sorted(ids):
            return dict(approved=False, message='TD wartet auf Prüfung des aktuellen Vorschlags.')
        return dict(approved=status.get('approved') is True, phase=status.get('phase'),
                    message=status.get('message', ''), td_frame=status.get('td_frame'))
    except (OSError, ValueError, KeyError, TypeError):
        return dict(approved=False, message='TD-Automatik noch nicht verbunden; einmalige Installation erforderlich.')
