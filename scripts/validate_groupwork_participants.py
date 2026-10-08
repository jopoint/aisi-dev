"""Fokussierte Offline-Prüfung der teilnehmendenbasierten Groupwork-Bausteine."""
from dataclasses import asdict
import argparse
from copy import deepcopy
import json
from pathlib import Path
import time

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon

from aisi.app.sim_layout_rules import _normalize_scene_for_aisi
from aisi.app.sim_room_editor import make_default_tables, scene_payload
from aisi.core.table_geometry import table_world_footprint
from aisi.input.scene_loader import build_scene_state_from_dict
from aisi.generation.groupwork_participants import plan_participant_groupwork, validate_groupwork_plan
from aisi.generation.adaptive_layout_v1 import LayoutConstraintError


def plot(ax,state,plan,title):
    tables={t.table_id:t for t in state.tables}
    targets={t.table_id:t for t in plan.targets}
    colors=plt.get_cmap('tab10')
    for cluster in plan.clusters:
        color=colors(int(cluster.group_id.split('_')[-1]))
        for region in plan.regions[cluster.cluster_id]:
            ax.add_patch(Polygon(region,facecolor=color,alpha=.12,edgecolor=color))
        for tid in cluster.table_ids:
            target=targets[tid]
            ax.add_patch(Polygon(table_world_footprint(tables[tid],(target.target_x,target.target_y),target.target_rot_deg),facecolor=color,alpha=.65))
            ax.text(target.target_x,target.target_y,
                    f'Tisch {tid.removeprefix("table_")}\nGruppe {int(cluster.group_id.split("_")[-1])+1}',
                    ha='center',va='center',fontsize=8)
    for tid in plan.parked_table_ids:
        target=targets[tid]
        ax.add_patch(Polygon(table_world_footprint(tables[tid],(target.target_x,target.target_y),target.target_rot_deg),facecolor='#cccccc',edgecolor='#555555'))
    for chair in plan.chairs:
        ax.add_patch(Circle((chair['x_cm'],chair['y_cm']),chair['radius_cm'],facecolor='#e79345',edgecolor='#333333'))
    ax.set(xlim=(0,500),ylim=(500,0),aspect='equal',xlabel='X [cm]',ylabel='Y [cm]',title=title)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--fixtures',type=Path,help='Gespeicherter validation.json-Bericht als Quelle')
    parser.add_argument('--policy', choices=('group_capacity','few_tables','regular_seats'), default='group_capacity')
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    root=Path(__file__).resolve().parents[1]
    sources={'editor':scene_payload(make_default_tables(),chairs=[],persons=[]),
             'live':json.loads((root/'data/aisi/scenes/simulated/live_scene.json').read_text())}
    if args.fixtures:
        saved=json.loads(args.fixtures.read_text())
        sources={name:(saved.get('sources') or saved['fixtures'])[name] for name in ('editor','live')}
    records=[];examples=[];started=time.monotonic()
    for name,raw in sources.items():
        state=build_scene_state_from_dict(_normalize_scene_for_aisi(raw),learning_format='groupwork')
        for people,groups in ((3,1),(5,1),(7,2),(10,2),(15,2),(15,5)):
            policy = args.policy
            try:
                plan=plan_participant_groupwork(state,people,groups,table_policy=policy)
            except LayoutConstraintError as exc:
                records.append(dict(source=name,participants=people,groups=groups,policy=policy,
                                    passed=False,error=str(exc)))
                print(name,people,groups,policy,'explizit abgelehnt:',str(exc),flush=True)
                continue
            validate_groupwork_plan(state,plan)
            assert plan==plan_participant_groupwork(state,people,groups,table_policy=policy)
            reversed_state=deepcopy(state);reversed_state.tables.reverse()
            reversed_plan=plan_participant_groupwork(reversed_state,people,groups,table_policy=policy)
            assert plan.targets==list(reversed(reversed_plan.targets))
            assert plan.chairs==reversed_plan.chairs and plan.clusters==reversed_plan.clusters
            records.append(dict(source=name,participants=people,groups=groups,policy=policy,passed=True,plan=asdict(plan)))
            label={'group_capacity':'Einzeltisch bis drei, danach Pair','few_tables':'wenige Tische','regular_seats':'Längsseiten bevorzugt'}[policy]
            if name=='editor' and (people,groups) in ((3,1),(5,1),(15,2)):examples.append((state,plan,f'{people} Personen · {groups} Gruppen · {label}'))
            print(name,people,groups,policy,'bestanden',round(time.monotonic()-started,1),'s',flush=True)
    fig,axes=plt.subplots(1,len(examples),figsize=(6*len(examples),6))
    for ax,(state,plan,title) in zip(axes,examples):plot(ax,state,plan,title)
    fig.tight_layout();fig.savefig(args.output/'gruppen_und_sitzprioritaet.png',dpi=140);plt.close(fig)
    passed=sum(record['passed'] for record in records)
    report=dict(cases=len(records),passed=passed,determinism=passed,scene_order=passed,
                sources=sources,results=records,live_output_enabled=False)
    (args.output/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(f'{passed}/{len(records)} Fälle realisiert; keine OSC-Ausgabe.',flush=True)
    if passed != len(records):raise SystemExit(1)


if __name__=='__main__':main()
