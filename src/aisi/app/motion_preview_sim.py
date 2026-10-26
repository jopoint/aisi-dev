"""Room Editor with one, three or five tables -> isolated Motion preview.

Only /aisi_motion/* is sent. No study or legacy /table channels are written.
"""
from __future__ import annotations

import argparse
import copy
from pathlib import Path
import secrets
import sys
import queue
import threading

from pythonosc.osc_bundle_builder import OscBundleBuilder, IMMEDIATELY
from pythonosc.osc_message_builder import OscMessageBuilder
from pythonosc.udp_client import UDPClient

from aisi.app.sim_room_editor import SimRoomEditor, make_default_table, tk
from aisi.core.table_geometry import world_footprint

# TD helpers deliberately remain outside the installed application package.
REPO = Path(__file__).resolve().parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0,str(REPO))
from td_builders.motion_osc import frame_values, MAX_COUNTER
from td_builders.motion_design import Pose, metrics


def bundle_for(values):
    bundle = OscBundleBuilder(IMMEDIATELY)
    for name,value in values.items():
        message = OscMessageBuilder(address='/'+name)
        message.add_arg(value)
        bundle.add_content(message.build())
    return bundle.build()


def make_scenario(count):
    """Deterministic test fixtures only; no study/layout configuration changes."""
    if count == 1:
        sources=[Pose(110,180,84)]
        destinations=[Pose(320,330,122)]
    elif count == 3:
        # Two independently moving tables; the third only receives the reveal.
        sources=[Pose(100,110,90),Pose(250,110,70),Pose(400,250,90)]
        destinations=[Pose(100,370,90),Pose(250,370,90),Pose(400,250,90)]
    elif count == 5:
        sources=[Pose(100,100,90),Pose(250,100,90),Pose(400,100,90),
                 Pose(100,400,90),Pose(250,400,90)]
        destinations=[Pose(100,150,90),Pose(250,150,90),Pose(400,100,90),
                      Pose(100,350,90),Pose(250,350,90)]
    else:
        raise ValueError('Motion-Simulation unterstützt 1, 3 oder 5 Tische.')
    tables=[]
    targets={}
    for index,(source,target) in enumerate(zip(sources,destinations)):
        identity='table_%d' % index
        table=make_default_table(identity,source.x,source.y,2)
        table['rotation_deg']=source.r
        tables.append(table)
        targets[identity]=target
    return tables,targets


class MotionSimulation:
    def __init__(self, editor, client, targets=None):
        self.editor,self.client = editor,client
        self.session = secrets.randbelow(MAX_COUNTER)+1
        self.frame,self.revision = 0,1
        self.targets = dict(targets) if targets is not None else {'table_0':Pose(320,330,122)}
        self.active = {table['id']:not metrics(
            Pose(table['x_cm'],table['y_cm'],table['rotation_deg']),self.targets[table['id']])[3]
            for table in editor.tables if table['id'] in self.targets}
        self.paused = False
        self.proposal = None
        self.pending = None

    def activate_proposal(self, proposal):
        """Commit one complete, ID-bound proposal; pose ticks never call this."""
        ids = [t['id'] for t in self.editor.tables if t['type']=='rect']
        targets = dict(proposal.targets)
        if len(ids) != len(targets) or set(ids) != set(targets):
            raise ValueError('Tischmenge während Berechnung verändert; erneut aktivieren.')
        active = {t['id']:not metrics(Pose(t['x_cm'],t['y_cm'],t['rotation_deg']),targets[t['id']])[3]
                  for t in self.editor.tables if t['type']=='rect'}
        self.targets, self.active, self.proposal = targets, active, proposal
        self.revision = self.revision % MAX_COUNTER + 1

    def request_proposal(self, settings):
        """Keep sending the old proposal while the existing planner computes."""
        if self.pending is not None:
            return
        from aisi.app.motion_layout_proposal import generate_proposal
        tables, settings = copy.deepcopy(self.editor.tables), copy.deepcopy(settings)
        self.pending = queue.Queue()
        results = self.pending
        self.editor.clipboard_status.set('Layout wird berechnet; bisheriger Vorschlag bleibt aktiv.')
        def worker():
            try:
                results.put((generate_proposal(tables, settings), None))
            except Exception as error:
                results.put((None, str(error)))
        threading.Thread(target=worker, daemon=True).start()
        self.editor.root.after(50,self.poll_proposal)

    def poll_proposal(self):
        if not self.editor.running or self.pending is None:
            return
        try:
            proposal,error = self.pending.get_nowait()
        except queue.Empty:
            self.editor.root.after(50,self.poll_proposal)
            return
        self.pending = None
        if error is None:
            try:
                self.activate_proposal(proposal)
            except ValueError as exc:
                error = str(exc)
        self.editor.clipboard_status.set('Kein neuer Vorschlag: '+error if error else
            'Aktiv: %s, Revision %d, %d Chairs. Ziele bleiben fest.' %
            (proposal.learning_format,self.revision,len(proposal.chairs)))
        self.editor.redraw()

    def activate(self):
        self.revision = self.revision % MAX_COUNTER + 1
        for table in self.editor.tables:
            if table['type'] != 'rect':
                continue
            identity = table['id']
            source = Pose(table['x_cm'],table['y_cm'],table['rotation_deg'])
            self.targets.setdefault(identity,source)
            self.active[identity] = not metrics(source,self.targets[identity])[3]

    def set_target_pose(self):
        for table in self.editor.tables:
            if table['id'] == (self.editor.selected_id or 'table_0') and table['id'] in self.targets:
                pose = self.targets[table['id']]
                table.update(x_cm=pose.x,y_cm=pose.y,rotation_deg=pose.r)
                self.editor.save_now()
                self.editor.redraw()
                break

    def tick(self):
        if not self.editor.running:
            return
        if not self.paused:
            self.frame += 1
            if self.frame > MAX_COUNTER:
                self.session = self.session % MAX_COUNTER + 1
                self.frame = 1
            rows = []
            for table in self.editor.tables:
                identity=table['id']
                if table['type'] != 'rect' or identity not in self.targets:
                    continue
                source=Pose(table['x_cm'],table['y_cm'],table['rotation_deg'])
                rows.append((identity,source,self.targets[identity],True,self.active[identity]))
            try:
                values = {}
                if self.proposal is not None:
                    from td_builders.motion_chairs import chair_values
                    values.update(chair_values(self.proposal.chairs, self.session, self.frame,
                                               self.revision,self.proposal.show_chairs))
                values.update(frame_values(rows,self.session,self.frame,self.revision))
                self.client.send(bundle_for(values))
            except (OSError,ValueError) as error:
                self.editor.clipboard_status.set('Motion: '+str(error))
        self.editor.root.after(50,self.tick)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host',default='127.0.0.1')
    parser.add_argument('--port',type=int,default=9000)
    parser.add_argument('--tables',type=int,choices=(1,3,5),default=1)
    parser.add_argument('--generated-layouts',action='store_true',
                        help='Beim Aktivieren aktuelle Lernformat-Einstellungen einmal berechnen.')
    parser.add_argument('--scene',type=Path,default=Path('/private/tmp/aisi-motion-sim/live_scene.json'))
    args=parser.parse_args()
    args.scene.parent.mkdir(parents=True,exist_ok=True)
    editor=SimRoomEditor(scene_path=args.scene)
    editor.tables,targets=make_scenario(args.tables)
    editor.chairs,editor.persons=[],[]
    editor.initial_tables=copy.deepcopy(editor.tables)
    editor.initial_chairs,editor.initial_persons=[],[]
    editor.next_table_number=args.tables
    editor.root.title('AISI Motion — %d Tische, isolierte Simulation' % args.tables)
    simulation=MotionSimulation(editor,UDPClient(args.host,args.port),targets=targets)
    if args.generated_layouts:
        # Start without the fixture targets; an explicit successful activation
        # is required before any generated guidance or chairs are displayed.
        simulation.targets = {}
        simulation.active = {}
    controls=tk.Frame(editor.root)
    controls.pack(fill='x')
    def activate():
        if args.generated_layouts:
            from aisi.app.learning_format_server import read_state
            simulation.request_proposal(read_state())
        else:
            simulation.activate()
    tk.Button(controls,text='Vorschlag aktivieren',command=activate).pack(side='left')
    tk.Button(controls,text='Auf Zielpose',command=simulation.set_target_pose).pack(side='left')
    pause=tk.Button(controls,text='Übertragung pausieren')
    def toggle():
        simulation.paused=not simulation.paused
        pause.configure(text='Übertragung fortsetzen' if simulation.paused else 'Übertragung pausieren')
    pause.configure(command=toggle)
    pause.pack(side='left')
    # Existing editor rendering/interaction stays intact. Add a target-only guide.
    original_redraw=editor.redraw
    def redraw():
        from aisi.app.sim_room_editor import world_to_screen
        original_redraw()
        for identity,target in simulation.targets.items():
            polygon=world_footprint('rect',target.x,target.y,target.r)
            coords=[v for point in polygon for v in world_to_screen(*point)]
            editor.canvas.create_polygon(*coords,fill='',outline='#00ec65',dash=(5,4),width=2)
            x,y=world_to_screen(target.x,target.y)
            editor.canvas.create_text(x,y,text='Ziel '+identity,fill='#00ec65')
        if simulation.proposal is not None and simulation.proposal.show_chairs:
            for x,y,r,_ in simulation.proposal.chairs:
                x0,y0=world_to_screen(x-r,y-r)
                x1,y1=world_to_screen(x+r,y+r)
                editor.canvas.create_oval(x0,y0,x1,y1,outline='#00ec65',width=2)
    editor.redraw=redraw
    editor.root.after(0,simulation.tick)
    print('Motion-OSC: nur /aisi_motion/* an %s:%s' % (args.host,args.port))
    editor.run()


if __name__=='__main__':
    main()
