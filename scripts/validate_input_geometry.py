"""Reproduzierbare Offline-Prüfung der gemeinsamen Rect-Input-Geometrie."""
from __future__ import annotations
import argparse
from collections import Counter
from copy import deepcopy
from dataclasses import asdict
import hashlib
import json
import math
from pathlib import Path
import subprocess
import time

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon, Rectangle
from aisi.analysis.synthetic_input_validation import validate_synthetic_input
from aisi.app.sim_layout_rules import (_normalize_scene_for_aisi, compute_synthetic_layout, validate_synthetic_input_geometry)
from aisi.app.sim_room_editor import make_default_tables, scene_payload
from aisi.core.models import TableTarget
from aisi.core.table_geometry import table_world_footprint
from aisi.generation.layout_synthesizer import _rect_input_clearance_regions, _rect_input_presenter_and_axis
from aisi.input.scene_loader import build_scene_state_from_dict

ROOT = Path(__file__).resolve().parents[1]
SIDES = (None, 'north', 'east', 'south', 'west')

def fixtures(root):
    default=scene_payload(make_default_tables(), chairs=[], persons=[])
    live=json.loads((root/'data/aisi/scenes/simulated/live_scene.json').read_text())
    rotated=deepcopy(default)
    angle=math.radians(35)
    for t in rotated['tables']:
        x,y=t['x_cm']-250,t['y_cm']-250
        t['x_cm']=250+x*math.cos(angle)-y*math.sin(angle)
        t['y_cm']=250+x*math.sin(angle)+y*math.cos(angle)
        t['rotation_deg']+=35
    asymmetric=deepcopy(default)
    for table, pose in zip(asymmetric['tables'], ((100,100,18),(390,150,-20),(120,320,70),(310,390,10),(410,320,90))):
        table.update(x_cm=pose[0], y_cm=pose[1], rotation_deg=pose[2])
    return {'editor': default, 'live': live, 'diagonal': rotated, 'asymmetric': asymmetric}

def run(raw, count, side):
    return compute_synthetic_layout(raw,'input',1.0, {'participants':count,'presentation_side':side,'adaptive_layout_preview':True})

def identity(raw, out):
    return dict(zip((t['id'] for t in raw['tables']), out.table_targets))

def verify(raw, out, count, side):
    validate_synthetic_input_geometry(raw,out)
    errors=validate_synthetic_input(raw,out,count,side)
    assert not errors, errors
    assert len(out.table_targets)==5 and len(out.chairs)==count
    assert len(out.active_table_ids)==min(5, math.ceil(count/2))
    ids={t['id'] for t in raw['tables']}
    assert set(out.active_table_ids).isdisjoint(out.parked_table_ids)
    assert set(out.active_table_ids)|set(out.parked_table_ids)==ids
    assert out.parked_table_ids==tuple(t['id'] for t in raw['tables'] if t['id'] not in out.active_table_ids)
    counts=Counter(str(c['table_id']) for c in out.chairs)
    assert set(counts)==set(out.active_table_ids)
    assert max(counts.values()) <= (2 if count<=10 else 3)
    assert max(counts.values())-min(counts.values())<=1
    roi=build_scene_state_from_dict(_normalize_scene_for_aisi(raw),learning_format='input').roi
    for c in out.chairs:
        x,y,r=float(c['x_cm']),float(c['y_cm']),float(c['radius_cm'])
        assert r==25 and roi.x_min<=x-r and x+r<=roi.x_max and roi.y_min<=y-r and y+r<=roi.y_max
    if side:
        active=[t for t in raw['tables'] if t['id'] in out.active_table_ids]
        axis={'north':(0,-1),'east':(1,0),'south':(0,1),'west':(-1,0)}[side]
        presenter=max(active,key=lambda t:(t['x_cm']*axis[0]+t['y_cm']*axis[1],t['id']))['id']
        targets=identity(raw,out)
        for c in out.chairs:
            tid=str(c['table_id']); target=targets[tid]
            signed=(float(c['x_cm'])-target['x_cm'])*axis[0]+(float(c['y_cm'])-target['y_cm'])*axis[1]
            assert signed>0 if tid==presenter else signed<0
        if len(active)>1:
            projection=lambda tid:targets[tid]['x_cm']*axis[0]+targets[tid]['y_cm']*axis[1]
            assert all(projection(presenter)>projection(t['id']) for t in active if t['id']!=presenter)

def plot(ax,raw,out,title):
    state=build_scene_state_from_dict(_normalize_scene_for_aisi(raw),learning_format='input')
    ts=[TableTarget(t.table_id,z['x_cm'],z['y_cm'],t.rot_deg,z['rotation_deg']) for t,z in zip(state.tables,out.table_targets)]
    active=[t for t in state.tables if t.table_id in out.active_table_ids]
    p,a=_rect_input_presenter_and_axis(active,out.presentation_side)
    ats=[t for t in ts if t.table_id in out.active_table_ids]
    for region in _rect_input_clearance_regions(ats,active,p.table_id,a):
        ax.add_patch(Polygon(region,facecolor='#cfe8f3',edgecolor='#64a5c5',alpha=.7))
    for table,target in zip(state.tables,ts):
        ax.add_patch(Polygon(table_world_footprint(table,(table.x,table.y),table.rot_deg),fill=False,edgecolor='#aab3b0',linewidth=.6,linestyle=':'))
        ax.add_patch(Polygon(table_world_footprint(table,(target.target_x,target.target_y),target.target_rot_deg),facecolor='#2878a4' if table.table_id in out.active_table_ids else '#999999',alpha=.6,edgecolor='#17405a'))
        ax.text(target.target_x,target.target_y,table.table_id.replace('table_','T'),ha='center',va='center',fontsize=8)
    for c in out.chairs:
        ax.add_patch(Circle((float(c['x_cm']),float(c['y_cm'])),float(c['radius_cm']),facecolor='#ee9147',edgecolor='#9c5220'))
    ax.add_patch(Rectangle((0,0),500,500,fill=False,edgecolor='#222222'))
    ax.set(xlim=(-10,510),ylim=(510,-10),aspect='equal',title=title,xlabel='X [cm]',ylabel='Y [cm]')
    ax.grid(alpha=.1)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,default=ROOT)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--fixtures',type=Path,help='Gespeicherte validation.json statt aktueller Quellszenen verwenden')
    args=parser.parse_args(); args.output.mkdir(parents=True,exist_ok=True)
    scenes=json.loads(args.fixtures.read_text())['fixtures'] if args.fixtures else fixtures(args.root)
    records=[]; stored={}; start=time.monotonic(); permutations=0
    for name,raw in scenes.items():
        for side in SIDES:
            for count in range(1,16):
                try:
                    out=run(raw,count,side); verify(raw,out,count,side)
                    assert out==run(raw,count,side), 'Nicht deterministisch'
                    if count in (1,3,5,7,9,11,15):
                        perm=deepcopy(raw); perm['tables']=list(reversed(perm['tables']))
                        other=run(perm,count,side); verify(perm,other,count,side)
                        assert identity(raw,out)==identity(perm,other), 'ID-Ziele ändern sich bei Scene-Order-Wechsel'
                        assert out.chairs==other.chairs, 'Chair-Identität ändert sich bei Scene-Order-Wechsel'
                        permutations+=1
                    stored[name,side,count]=out
                    records.append({'scene':name,'side':side,'count':count,'passed':True})
                except Exception as e:
                    records.append({'scene':name,'side':side,'count':count,'passed':False,'error':str(e)})
                    print(name,side,count,str(e),flush=True)
        print(name, 'fertig',round(time.monotonic()-start,1),'s',flush=True)
    for name,raw in scenes.items():
        for side in SIDES:
            for count in (16,17,30):
                try: run(raw,count,side)
                except ValueError: pass
                else: raise AssertionError(f'Überkapazität akzeptiert: {name}/{side}/{count}')
    report={'cases':len(records),'passed':sum(r['passed'] for r in records),'scene_order_cases':permutations,'determinism_repetitions':len(records),'overcapacity_rejections':len(scenes)*len(SIDES)*3,'strength':1.0,'chair_radius_cm':25,'fixtures':scenes,'results':records}
    (args.output/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    examples=[('editor',None,1),('editor',None,5),('editor',None,15)]
    for filename,cases in [('kapazitaet.png',examples),('quelladaptiv.png',[('live',None,7),('live',None,15),('diagonal',None,15)]),('praesentationsseiten.png',[('live',s,15) for s in SIDES[1:]])]:
        fig,axes=plt.subplots(1,len(cases),figsize=(5*len(cases),5.6))
        for ax,key in zip(axes,cases):
            if key in stored: plot(ax,scenes[key[0]],stored[key],f'{key[0]} · {key[2]} Chairs · {key[1] or "automatisch"}')
            else: ax.set_title(f'Fehler: {key}')
        fig.suptitle('Rect Input: aktiv blau · geparkt grau · Sitzfläche hellblau · Chair orange · Source gepunktet')
        fig.tight_layout(); fig.savefig(args.output/filename,dpi=150); plt.close(fig)
    print(json.dumps({k:v for k,v in report.items() if k not in ('fixtures','results')},ensure_ascii=False),flush=True)
    if report['passed']!=report['cases']: raise SystemExit(1)

if __name__=='__main__': main()
