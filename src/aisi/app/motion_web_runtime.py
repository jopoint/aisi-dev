"""Headless Motion controller shared by the existing Learning-Format server."""
import copy
import queue
import threading
import time

from aisi.app.motion_live_control import MotionLiveSession
from aisi.app.motion_layout_proposal import generate_proposal
from aisi.app.vision_live_to_aisi_scene import (
    default_input_path, initial_live_offset, read_new_jsonl_lines, _frame_from_json_line)


class MotionWebRuntime:
    def __init__(self, source=None, client=None, planner=generate_proposal):
        self.source = source or default_input_path()
        self.client, self.planner = client, planner
        self.controller = MotionLiveSession()
        self.lock = threading.RLock()
        self.stop_event = threading.Event()
        self.results = None
        self.message = 'Kein aktivierter Vorschlag. Einstellungen wählen und explizit aktivieren.'
        self.active_settings = None
        self.offset, self.pending = initial_live_offset(self.source), b''
        self.thread = None
        self.error = None
        self.planning_seconds = None

    def activate(self, settings):
        with self.lock:
            if self.results is not None:
                return False
            try:
                tables = self.controller.adapter.current_tables(time.monotonic())
                if not tables:
                    raise ValueError('Keine aktuellen Tische erkannt.')
            except ValueError as error:
                self.message = 'Kein neuer Vorschlag: ' + str(error)
                return False
            frozen = copy.deepcopy(settings)
            frozen['transformation_strength'] = 1.0
            calibration = self.controller.adapter.snapshot(time.monotonic())['calibration_id']
            destination = self.results = queue.Queue()
            self.planning_seconds = None
            self.message = 'Berechnung läuft; bisherige Ziele und Chairs bleiben fest.'

            def worker():
                started = time.perf_counter()
                try:
                    proposal, error = self.planner(tables, frozen), None
                except Exception as exc:
                    proposal, error = None, str(exc)
                destination.put((proposal, error, time.perf_counter()-started))
            threading.Thread(target=worker, daemon=True).start()
            self.request_settings, self.request_calibration = frozen, calibration
            return True

    def reconnect(self):
        """Explicit reset: discard layout; never remap IDs or accept calibration silently."""
        with self.lock:
            if self.results is not None:
                self.message = 'Erst die laufende Berechnung abwarten.'
                return False
            # A new transport session cannot retain TD approval implicitly.
            self.controller = MotionLiveSession()
            self.offset, self.pending = initial_live_offset(self.source), b''
            self.active_settings = None
            self.message = ('Tracking neu verbunden: zwei neue Frames abwarten, dann Vorschlag '
                            'aktivieren und TD-Freigabe erneut prüfen.')
            return True

    def tick(self):
        from aisi.app.motion_preview_sim import bundle_for
        with self.lock:
            try:
                self.offset, self.pending, lines = read_new_jsonl_lines(
                    self.source, self.offset, self.pending)
                for line in lines:
                    frame = _frame_from_json_line(line)
                    adapter = self.controller.adapter
                    accepted = adapter.ingest(frame, time.monotonic(), time.time())
                    if not accepted and adapter.reset_reason == 'producer_restart':
                        from aisi.app.motion_td_status import outputs_confirmed_off
                        if (frame.world.get('calibration_id') == adapter._calibration
                                and outputs_confirmed_off()):
                            # In-flight proposals belong to the previous producer generation.
                            self.results = None
                            self.controller.reconnect_camera()
                            adapter.ingest(frame, time.monotonic(), time.time())
                            self.message = ('Kamera automatisch neu verbunden. Frische Tische abwarten '
                                            'und Vorschlag aktivieren; alter Vorschlag bleibt gesperrt.')
                self.error = None
            except (OSError, ValueError, KeyError, TypeError) as error:
                self.error = str(error)
            if self.results is not None:
                try:
                    proposal, error, self.planning_seconds = self.results.get_nowait()
                except queue.Empty:
                    pass
                else:
                    self.results = None
                    if error is None:
                        try:
                            now = time.monotonic()
                            if self.controller.adapter.snapshot(now)['calibration_id'] != self.request_calibration:
                                raise ValueError('Kalibrierung während Berechnung verändert.')
                            self.controller.commit(proposal, now)
                            self.active_settings = self.request_settings
                        except ValueError as exc:
                            error = str(exc)
                    self.message = ('Kein neuer Vorschlag: ' + error if error else
                                    'Vorschlag aktiviert. Ziele und Chairs bleiben fest.')
            if self.client is not None:
                try:
                    self.client.send(bundle_for(self.controller.values(time.monotonic())))
                except (OSError, ValueError) as error:
                    self.error = 'OSC: ' + str(error)

    def status(self, settings):
        from aisi.app.motion_td_status import read_approval
        with self.lock:
            snap = self.controller.adapter.snapshot(time.monotonic())
            current = copy.deepcopy(settings)
            current['transformation_strength'] = 1.0
            # Legacy regeneration counters are not Motion activations.
            def comparable(value):
                return {k: v for k, v in (value or {}).items() if k != 'layout_revision'}
            approval = read_approval(self.controller.session, self.controller.revision,
                                     [row[0] for row in snap['rows']])
            if not snap['fresh']:
                approval = dict(approved=False, message='Kameraquelle nicht aktuell; keine Freigabe bestätigt.')
            return dict(camera_fresh=snap['fresh'], camera_reason=snap['reason'],
                        camera_frame=snap['camera_frame_id'],
                        observed_ids=sorted(self.controller.adapter._sources),
                        missing_active_ids=sorted(set(self.controller.adapter._targets) -
                                                  set(self.controller.adapter._sources)),
                        session=self.controller.session, revision=self.controller.revision,
                        active_format=(self.controller.proposal.learning_format
                                       if self.controller.proposal and not self.controller.requires_activation else None),
                        chairs=(len(self.controller.proposal.chairs)
                                if self.controller.proposal and not self.controller.requires_activation else 0),
                        requires_activation=self.controller.requires_activation,
                        pending_settings=(self.controller.requires_activation or
                                          comparable(current) != comparable(self.active_settings)),
                        busy=self.results is not None, message=self.message, error=self.error,
                        planning_seconds=self.planning_seconds,
                        sending=self.client is not None, td_approved=approval['approved'],
                        td_approval=approval['message'])

    def start(self):
        def run():
            while not self.stop_event.is_set():
                self.tick()
                self.stop_event.wait(.05)
        self.thread = threading.Thread(target=run, daemon=True)
        self.thread.start()

    def close(self):
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=2)


def enhance_html(html):
    """Small functional overlay; retain existing settings and simulation UI."""
    panel = '''<section style="padding:16px;border:1px solid #777;border-radius:16px;margin:16px 0">
<h2>Motion</h2><p id="motion-status">Status wird geladen …</p>
<form method="post" action="/set"><button id="motion-activate" name="action" value="activate_motion">Vorschlag aktivieren</button></form>
<p>Einstellungen sind vorgemerkt. Erst Aktivieren setzt neue Ziele und Chairs. Planung: 100 %.</p>
<p>Nach Kameraneustart verbindet sich Motion automatisch neu, sobald TD die Ausgabe gesperrt hat.
Dann nur noch „Vorschlag aktivieren“. Andere Tisch-IDs werden niemals automatisch alten Zielen zugeordnet.</p></section>
<script>
async function motionStatus() {
 try {
  const s = await (await fetch('/motion-status', {cache:'no-store'})).json();
  document.getElementById('motion-status').textContent =
   'Kamera: ' + (s.camera_fresh ? 'aktuell' : s.camera_reason) + ' · IDs: ' + s.observed_ids.join(', ') +
   ' · Aktiv: ' + (s.active_format || 'kein Vorschlag') + ' · Revision ' + s.revision + ' · ' + s.chairs + ' Chairs. ' +
   s.message + (s.pending_settings ? ' Einstellungen noch nicht aktiviert.' : '') +
   (s.missing_active_ids.length ? ' Aktive Tisch-IDs fehlen: '+s.missing_active_ids.join(', ')+'. Erneut explizit aktivieren.' : '') +
   (s.error ? ' Fehler: '+s.error : '') + ' TD-Ausgabe: '+s.td_approval;
  document.getElementById('motion-activate').disabled = s.busy || !s.camera_fresh || !s.observed_ids.length;
 } catch(e) { document.getElementById('motion-status').textContent='Motion-Server nicht erreichbar. Start-/Statusbefehl prüfen.'; }
}
motionStatus();setInterval(motionStatus,1000);
document.querySelectorAll('button[value="regenerate"]').forEach(b=>b.closest('form').hidden=true);
document.querySelectorAll('.current').forEach(n=>n.textContent=n.textContent.replace('Current learning format:', 'Vorgemerktes Lernformat:'));
const slider=document.querySelector('input[name="transformation_strength"]');
if(slider) { slider.disabled=true; slider.closest('form').hidden=true; }
const legacy=document.getElementById('layout-status');if(legacy) legacy.hidden=true;
</script>'''
    markup, script = panel.split('<script>', 1)
    return html.replace('<body>', '<body>' + markup).replace('</body>', '<script>' + script + '</body>')
