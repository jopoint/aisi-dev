"""Lockere Discussion-Teilstärken offline prüfen und mit 100 % vergleichen."""
import argparse
from dataclasses import replace
import json
import math
from pathlib import Path
import time

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon

from aisi.app.sim_room_editor import make_default_tables, scene_payload
from aisi.app.sim_layout_rules import _normalize_scene_for_aisi
from aisi.app.sim_scene_to_osc import prepare_scene_output
from aisi.core.table_geometry import table_world_footprint
from aisi.generation.discussion_chairs import (
    plan_discussion_chairs, transform_discussion_plan, validate_discussion_chairs,
)
from aisi.input.scene_loader import build_scene_state_from_dict


def check(raw, name):
    state=build_scene_state_from_dict(_normalize_scene_for_aisi(raw),learning_format='discussion')
    records=[]; examples={}
    for count in range(1,16):
        final=plan_discussion_chairs(state,count)
        for strength in (0.,.01,.25,.5,.75,.99,1.):
            start=time.monotonic()
            tables,_,chairs,targets,error=prepare_scene_output(raw,'discussion',strength,False,
                activity_parameters={'adaptive_layout_preview':True,'participants':count})
            assert error is None and tables==raw['tables'] and len(targets)==len(state.tables)
            assert len(chairs)==(0 if strength==0 else count)
            if strength>0:
                plan=final if strength==1 else transform_discussion_plan(state,final,strength)
                validate_discussion_chairs(state,plan)
                assert plan.active_table_ids==final.active_table_ids and plan.parked_table_ids==final.parked_table_ids
                assert [t.table_id for t in plan.targets]==[t.table_id for t in state.tables]
                assert plan==(plan_discussion_chairs(state,count) if strength==1 else transform_discussion_plan(state,final,strength))
                reversed_state=replace(state,tables=list(reversed(state.tables)))
                other_final=plan_discussion_chairs(reversed_state,count)
                other=other_final if strength==1 else transform_discussion_plan(reversed_state,other_final,strength)
                assert plan.targets==list(reversed(other.targets)) and plan.chairs==other.chairs
                if count in (6,10,15) and strength in (.25,.5,1.): examples[count,strength]=plan
            else:
                assert targets==[dict(x_cm=t.x,y_cm=t.y,rotation_deg=t.rot_deg) for t in state.tables]
            records.append(dict(scene=name,participants=count,strength=strength,seconds=time.monotonic()-start,
                total_movement_cm=sum(math.hypot(t['x_cm']-s['x_cm'],t['y_cm']-s['y_cm']) for t,s in zip(targets,tables))))
    return state,records,examples


def plot(state, examples, output):
    fig,axes=plt.subplots(3,3,figsize=(13,13))
    by_id={t.table_id:t for t in state.tables}
    for row,count in enumerate((6,10,15)):
        for col,strength in enumerate((.25,.5,1.)):
            ax=axes[row,col];plan=examples[count,strength]
            for region in plan.regions.values():
                ax.add_patch(Polygon(region,facecolor='#cce6ef',edgecolor='none',alpha=.5))
            for target in plan.targets:
                table=by_id[target.table_id]
                ax.add_patch(Polygon(table_world_footprint(table,(table.x,table.y),table.rot_deg),
                    fill=False,edgecolor='#3492dc',alpha=.55,linewidth=.8))
                parked=target.table_id in plan.parked_table_ids
                ax.add_patch(Polygon(table_world_footprint(table,(target.target_x,target.target_y),target.target_rot_deg),
                    facecolor='white' if parked else '#b9c1c9',edgecolor='#475569',hatch='//' if parked else None))
            for chair in plan.chairs:
                ax.add_patch(Circle((chair['x_cm'],chair['y_cm']),25,facecolor='#f3c383',edgecolor='#b76516'))
            ax.set(xlim=(0,500),ylim=(500,0),aspect='equal',title=f'{count} Personen · {strength:.0%}',xlabel='X [cm]',ylabel='Y [cm]')
    fig.suptitle('Discussion · einzelne Tische bei Teilstärke frei\nBlau: Source · Grau: Ziel · Schraffiert: geparkt',fontsize=14)
    fig.tight_layout(rect=(0,0,1,.95));fig.savefig(output/'vergleich.png',dpi=140);plt.close(fig)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--scene',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    sources={'editor':scene_payload(make_default_tables(),chairs=[],persons=[]),
             'live':json.loads(args.scene.read_text())}
    records=[]
    for name,raw in sources.items():
        state,checks,examples=check(raw,name);records.extend(checks)
        if name=='live': plot(state,examples,args.output)
        print(name,'bestanden',flush=True)
    (args.output/'sources.json').write_text(json.dumps(sources,indent=2)+'\n')
    (args.output/'checks.json').write_text(json.dumps(records,indent=2)+'\n')
    print(len(records),'Fälle bestanden; keine OSC-Netzwerkausgabe')


if __name__=='__main__': main()
