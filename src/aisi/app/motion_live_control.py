"""Explicit live proposal control; sending is opt-in and never approves TD output.

Reads new camera FrameEvents, without modifying the camera, scene adapter or
legacy OSC sender. Stop the owned Motion simulator and disable its output test
before starting with --send: both use the existing /aisi_motion/ namespace.
"""
from __future__ import annotations

import argparse
import copy
from pathlib import Path
import queue
import secrets
import threading
import time

from aisi.app.motion_live_adapter import MotionLiveAdapter


def content_pose(p):
    """World -> observed original mask transforms -> existing content camera.

    Confirmed in the Windows Textport on 2026-10-26. No calibration changes.
    Rect orientation is axial; the joint 180-degree position turn preserves r.
    """
    from td_builders.motion_design import td_pose
    from td_builders.study_start_pose import TD_UNITS_PER_CM
    return td_pose((250-p[0])*TD_UNITS_PER_CM,
                   (p[1]-250)*TD_UNITS_PER_CM,-p[2])


class MotionLiveSession:
    def __init__(self,adapter=None):
        from td_builders.motion_osc import MAX_COUNTER
        self.adapter=adapter or MotionLiveAdapter()
        self.session=secrets.randbelow(MAX_COUNTER)+1
        self.frame=0
        self.revision=1
        self.proposal=None

    def commit(self,proposal,now):
        from td_builders.motion_osc import MAX_COUNTER
        tables=self.adapter.current_tables(now)
        sources={t['id'] for t in tables}
        targets=dict(proposal.targets)
        if len(targets)!=len(proposal.targets) or set(targets)!=set(sources):
            raise ValueError('Tischmenge während Berechnung verändert; erneut aktivieren.')
        if self.revision>=MAX_COUNTER:
            raise ValueError('Layoutzähler ausgeschöpft; neue Sitzung erforderlich.')
        # Arrival is a reversible Motion state, not an inactive layout role.
        # Every generated table target must remain eligible for reactivation.
        active=list(targets)
        revision=self.revision+1
        self.adapter.activate(revision,targets,active,now)
        self.proposal,self.revision=proposal,revision

    def values(self,now):
        from td_builders.motion_osc import MAX_COUNTER,frame_values
        from td_builders.motion_chairs import chair_values
        snap=self.adapter.snapshot(now)
        self.frame+=1
        if self.frame>MAX_COUNTER:
            self.session=self.session % MAX_COUNTER+1
            self.frame=1
        rows=[(identity,content_pose(source),content_pose(target),valid,active)
              for identity,source,target,valid,active in snap['rows']]
        chairs=()
        visible=False
        if self.proposal is not None:
            chairs=tuple((*content_pose((x,y,0))[:2],r,identity)
                         for x,y,r,identity in self.proposal.chairs)
            visible=self.proposal.show_chairs and snap['fresh']
        # Global table frame remains the final bundle commit marker.
        values=chair_values(chairs,self.session,self.frame,self.revision,visible)
        values['aisi_motion/camera/fresh']=int(snap['fresh'])
        values['aisi_motion/camera/session']=self.session
        values['aisi_motion/camera/frame']=self.frame
        values.update(frame_values(rows,self.session,self.frame,self.revision))
        return values


def main():
    from aisi.app.vision_live_to_aisi_scene import (
        default_input_path,initial_live_offset,read_new_jsonl_lines,_frame_from_json_line)
    from aisi.app.learning_format_server import read_state
    from aisi.app.motion_layout_proposal import generate_proposal
    from aisi.app.motion_preview_sim import bundle_for
    import tkinter as tk
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,default=default_input_path())
    parser.add_argument('--send',action='store_true',help='Nur bei deaktiviertem TD-Ausgabetest verwenden.')
    parser.add_argument('--host',default='127.0.0.1')
    parser.add_argument('--port',type=int,default=9000)
    args=parser.parse_args()
    client=None
    if args.send:
        from pythonosc.udp_client import UDPClient
        client=UDPClient(args.host,args.port)
    controller=MotionLiveSession()
    offset,pending=initial_live_offset(args.input),b''
    results=None
    root=tk.Tk()
    root.title('AISI Motion — echte Kamera, explizite Aktivierung')
    source_status=tk.StringVar(value='Warte auf zwei neue Kameraframes.')
    proposal_status=tk.StringVar(value='Kein aktivierter Vorschlag. TD-Freigabe bleibt separat.')
    tk.Label(root,textvariable=source_status,wraplength=620,justify='left').pack(padx=16,pady=8)
    tk.Label(root,textvariable=proposal_status,wraplength=620,justify='left').pack(padx=16,pady=8)

    def activate():
        nonlocal results
        if results is not None:
            return
        try:
            tables=controller.adapter.current_tables(time.monotonic())
            settings=copy.deepcopy(read_state())
        except ValueError as error:
            proposal_status.set('Kein neuer Vorschlag: '+str(error))
            return
        results=queue.Queue()
        destination=results
        proposal_status.set('Berechnung aus aktuellen Istposen; bisheriger Vorschlag bleibt fest.')
        def worker():
            try:
                destination.put((generate_proposal(tables,settings),None))
            except Exception as error:
                destination.put((None,str(error)))
        threading.Thread(target=worker,daemon=True).start()

    tk.Button(root,text='Vorschlag aktivieren',command=activate).pack(padx=16,pady=8)
    tk.Label(root,text='OSC: /aisi_motion/*' if client else 'Nur lokale Vorschau; kein OSC-Versand.').pack(pady=8)

    def tick():
        nonlocal offset,pending,results
        try:
            offset,pending,lines=read_new_jsonl_lines(args.input,offset,pending)
            for line in lines:
                controller.adapter.ingest(_frame_from_json_line(line),time.monotonic(),time.time())
        except (OSError,ValueError,KeyError,TypeError) as error:
            source_status.set('Lesefehler: '+str(error))
        if results is not None:
            try:
                proposal,error=results.get_nowait()
            except queue.Empty:
                pass
            else:
                results=None
                if error is None:
                    try:
                        controller.commit(proposal,time.monotonic())
                    except ValueError as exc:
                        error=str(exc)
                proposal_status.set('Kein neuer Vorschlag: '+error if error else
                    'Aktiv: %s, Revision %d, %d Chairs. Ziele bleiben fest.' %
                    (proposal.learning_format,controller.revision,len(proposal.chairs)))
        status=controller.adapter.snapshot(time.monotonic())
        tables=controller.adapter.current_tables(time.monotonic()) if status['fresh'] else []
        source_status.set('Kamera: %s; Frame %s; IDs: %s' %
                          (status['reason'],status['camera_frame_id'],', '.join(t['id'] for t in tables)))
        if client is not None:
            try:
                client.send(bundle_for(controller.values(time.monotonic())))
            except (OSError,ValueError) as error:
                proposal_status.set('OSC: '+str(error))
        root.after(50,tick)

    root.after(0,tick)
    root.mainloop()


if __name__=='__main__':
    main()
