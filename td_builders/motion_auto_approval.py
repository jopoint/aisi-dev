"""Frame-separated automatic approval; no layout generation or calibration edits."""
import json
import os
from pathlib import Path
import tempfile
import time

from td_builders import motion_live_output as live

STATUS_NAME = 'motion_td_approval.json'


def identity(report):
    stream = report.get('live_stream', {})
    if not report.get('passed') or not stream.get('fresh') or not stream.get('ids'):
        raise ValueError(report.get('status', 'Keine frische aktivierte Tischmenge.'))
    return (tuple(stream['layout']), tuple(stream['ids']))


class Approval:
    """Only a successful full proof and a later advancing frame can enable."""
    def __init__(self):
        self.phase = 'waiting'
        self.key = None
        self.proof_signature = None
        self.proof_frame = None
        self.next_attempt = 0
        self.message = 'Warte auf aktivierten Vorschlag und frische Quelle.'

    def clear(self, disable, message, now, retry=0):
        disable()
        self.phase, self.key = 'waiting', None
        self.proof_signature = None
        self.message = message
        self.next_attempt = now + retry

    def step(self, now, frame, enabled_mode, sample, verify, confirm, enable, disable):
        if not enabled_mode:
            self.clear(disable, 'Automatik wartet: AISI-Modus und normale Ausgabe erforderlich.', now)
            return
        try:
            current = sample()
            key = identity(current)
            if self.phase == 'waiting' and now < self.next_attempt:
                return
            if self.key != key:
                retry_at = self.next_attempt
                self.clear(disable, 'Neue Sitzung, Revision oder Tischmenge: Maskenprüfung erforderlich.', now)
                self.next_attempt = max(now, retry_at)
                self.key = key
            if self.phase == 'active':
                self.message = 'TD-Ausgabe automatisch geprüft und freigegeben.'
                return
            if now < self.next_attempt:
                return
            if self.phase == 'waiting':
                disable()
                proof = verify()
                if identity(proof) != key:
                    raise ValueError('Quelle während Maskenprüfung verändert.')
                self.key = key
                self.proof_signature = tuple(proof['live_stream']['signature'])
                self.proof_frame = frame
                self.phase = 'confirming'
                self.message = 'Maskenprüfung bestanden; warte auf späteren TD-Frame.'
                return
            if frame <= self.proof_frame:
                return
            if self.phase == 'confirming':
                following = confirm()
                if identity(following) != key:
                    raise ValueError('Quelle seit Maskenprüfung verändert.')
                signature = tuple(following['live_stream']['signature'])
                if signature == self.proof_signature:
                    return
                if signature[0] != self.proof_signature[0] or signature[1] <= self.proof_signature[1]:
                    raise ValueError('Motion-Frame läuft nicht vorwärts.')
                enable()
                self.phase = 'checking_output'
                self.proof_frame = frame
                self.message = 'Freigegeben; separate Ausgabekontrolle steht aus.'
                return
            if self.phase == 'checking_output':
                if identity(verify()) != key:
                    raise ValueError('Quelle während Ausgabekontrolle verändert.')
                self.phase = 'active'
                self.message = 'TD-Ausgabe automatisch geprüft und freigegeben.'
        except Exception as error:
            self.clear(disable, str(error), now, retry=2)


def disable(resolve):
    comp = resolve(live.test.routing.PATH)
    if comp is not None:
        comp.par.Enablemotion = False
        comp.par.Sourceapproved = False


def reset(resolve, owner):
    disable(resolve)
    owner.store('approval_runtime', None)
    owner.store('approval_last_tick', -10)
    owner.store('approval_last_publish', -10)
    owner.store('approval_status', {'approved': False, 'message': 'TD-Start: erneute Prüfung erforderlich.'})


def publish(owner, controller, now, frame, flags):
    key = controller.key
    report = dict(updated_at=time.time(), td_frame=frame, phase=controller.phase,
                  automatic=True, enabled=bool(owner.par.Enabled.eval()), output_flags=[bool(v) for v in flags],
                  approved=controller.phase == 'active' and all(flags),
                  layout=list(key[0]) if key else None, ids=list(key[1]) if key else [],
                  message=controller.message, saved=False)
    owner.store('approval_status', report)
    if now - owner.fetch('approval_last_publish', -10) < .5:
        return
    destination = Path(__file__).resolve().parents[1] / 'data/aisi/state' / STATUS_NAME
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=str(destination.parent),
                                         delete=False, suffix='.tmp') as handle:
            temporary = handle.name
            json.dump(report, handle, ensure_ascii=False)
        os.replace(temporary, str(destination))
        owner.store('approval_last_publish', now)
    finally:
        if temporary and os.path.exists(temporary):
            os.unlink(temporary)


def tick(resolve, owner, frame):
    now = time.monotonic()
    controller = owner.fetch('approval_runtime', None)
    if controller is None:
        reset(resolve, owner)
        controller = Approval()
        owner.store('approval_runtime', controller)
        owner.storeStartupValue('approval_runtime', None)
        owner.storeStartupValue('approval_last_tick', -10)
        owner.storeStartupValue('approval_last_publish', -10)
    if now - owner.fetch('approval_last_tick', -10) < .1:
        return
    owner.store('approval_last_tick', now)
    comp = resolve(live.test.routing.PATH)
    try:
        if comp is None:
            raise ValueError('Motion-Routing fehlt.')
        def off():
            disable(resolve)
        def on():
            live.validate(resolve, comp)
            comp.par.Sourceapproved = True
            comp.par.Enablemotion = True
            if live.indices(comp) != dict(floor=1, tabletop=1, simulation_mask=0, simulation_chairs=1):
                raise ValueError('Automatische Freigabe wählt unerwartete Ausgabeeingänge.')
        def sample():
            # Read fresh frame/camera validity cheaply; full GPU proof only on transitions.
            report = live.masks.current_stream(resolve)
            if report.get('passed'):
                count = raw['vision/table/count'] if raw is not None else None
                if count is None or count.eval() != len(report['live_stream'].get('ids', [])):
                    raise ValueError('Tracking-Tischmenge und aktiver Motion-Vorschlag weichen ab.')
            return report
        def verify():
            return live.verify(resolve)
        def confirm():
            live.validate(resolve, comp)
            return live.masks.current_sources(resolve)
        raw = resolve(live.test.routing.RAW)
        mode_ok = (owner.par.Enabled.eval() and not comp.par.Simulationtest.eval()
                   and raw is not None and raw['study/mode'] is not None
                   and raw['study/mode'].eval() == 2)
        for path in (live.test.routing.LAYOUT+'panel_mode', '/project1/comp_output/panel_mode'):
            panel = resolve(path)
            mode_ok = mode_ok and panel is not None and panel['state'] is not None and panel['state'].eval() == 0
        if controller.phase == 'active' and not (comp.par.Enablemotion.eval() and comp.par.Sourceapproved.eval()):
            controller.clear(off, 'Freigabe aufgehoben; erneute Prüfung.', now)
        controller.step(now, frame, mode_ok, sample, verify, confirm, on, off)
        publish(owner, controller, time.monotonic(), frame,
                (comp.par.Enablemotion.eval(), comp.par.Sourceapproved.eval()))
    except Exception as error:
        disable(resolve)
        controller.phase = 'waiting'
        controller.message = str(error)
        owner.store('approval_status', {'approved':False, 'message':str(error)})
