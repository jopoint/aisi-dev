"""Offline-Prüfung der Discussion-Teilnehmerstufen, ohne OSC-Netzwerkversand."""
import argparse
from collections import Counter
from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path
import time

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon

from aisi.app.sim_room_editor import make_default_tables, scene_payload
from aisi.app.sim_layout_rules import _normalize_scene_for_aisi
from aisi.app.sim_scene_to_osc import prepare_scene_output, send_chairs
from aisi.core.table_geometry import table_world_footprint
from aisi.generation.discussion_chairs import plan_discussion_chairs, validate_discussion_chairs
from aisi.input.scene_loader import build_scene_state_from_dict


def check_source(name, raw, output):
    state=build_scene_state_from_dict(_normalize_scene_for_aisi(raw),learning_format='discussion')
    records=[];examples={}
    for count in range(1,16):
        start=time.monotonic()
        plan=plan_discussion_chairs(state,count)
        validate_discussion_chairs(state,plan)
        repeated=plan_discussion_chairs(state,count)
        reversed_plan=plan_discussion_chairs(replace(state,tables=list(reversed(state.tables))),count)
        assert plan==repeated
        assert plan.targets==list(reversed(reversed_plan.targets)) and plan.chairs==reversed_plan.chairs
        tables,_,chairs,targets,error=prepare_scene_output(raw,'discussion',1.,False,
            activity_parameters={'adaptive_layout_preview':True,'participants':count})
        assert error is None and tables==raw['tables'] and chairs==plan.chairs
        assert len(targets)==len(state.tables) and len(chairs)==count
        messages=[]
        class Recorder:
            def send_message(self,address,value): messages.append((address,value))
        send_chairs(Recorder(),chairs,True)
        assert len(messages)==3*count
        assert all(type(value) is float for _,value in messages)
        required=2 if count<=6 else 4 if count<=12 else 5
        assert len(plan.active_table_ids)==required and len(plan.parked_table_ids)==5-required
        kinds=Counter(c['seat_kind'] for c in chairs)
        if required in (4,5):
            assert kinds['regular_long']==min(count,2*required)
            assert kinds['regular_corner']==max(0,count-2*required) and kinds['dense_long']==0
        records.append(dict(participants=count,active=list(plan.active_table_ids),
            parked=list(plan.parked_table_ids),seat_kinds=dict(kinds),seconds=time.monotonic()-start))
        if count in (4,6,12,15): examples[count]=deepcopy(plan)
    fig,axes=plt.subplots(2,2,figsize=(11,11))
    by_id={t.table_id:t for t in state.tables}
    for ax,(count,plan) in zip(axes.flat,examples.items()):
        for region in plan.regions.values():
            ax.add_patch(Polygon(region,facecolor='#dcecf3',edgecolor='#277595',alpha=.65))
        for target in plan.targets:
            parked=target.table_id in plan.parked_table_ids
            footprint=table_world_footprint(by_id[target.table_id],(target.target_x,target.target_y),target.target_rot_deg)
            ax.add_patch(Polygon(footprint,facecolor='white' if parked else '#b9c1c9',edgecolor='#475569',hatch='//' if parked else None))
        for chair in plan.chairs:
            corner=chair['seat_kind']=='regular_corner'
            ax.add_patch(Circle((chair['x_cm'],chair['y_cm']),25,
                facecolor='#bca7e8' if corner else '#f3c383',edgecolor='#673da0' if corner else '#b76516'))
        ax.set(xlim=(0,500),ylim=(500,0),aspect='equal',xlabel='X [cm]',ylabel='Y [cm]',
            title=f'{count} Personen · {len(plan.active_table_ids)} aktive Tische')
    fig.suptitle(f'Discussion · Teilnehmerstufen · {name}\nViolett: Eckplätze · Schraffiert: geparkte Tische',fontsize=14)
    fig.tight_layout(rect=(0,0,1,.95))
    fig.savefig(output/f'{name}_stufen.png',dpi=150);plt.close(fig)
    return records


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--scene',type=Path,required=True,help='Zweite Ausgangsszene mit fünf Rect-Tischen')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    sources={'editor':scene_payload(make_default_tables(),chairs=[],persons=[]),
             'live':json.loads(args.scene.read_text())}
    report={}
    for name,raw in sources.items():
        (args.output/f'{name}_source.json').write_text(json.dumps(raw,ensure_ascii=False,indent=2)+'\n')
        report[name]=check_source(name,raw,args.output)
    (args.output/'checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(f'{sum(map(len,report.values()))} Fälle bestanden; {args.output}')


if __name__=='__main__': main()
