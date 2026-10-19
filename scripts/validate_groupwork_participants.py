"""Fokussierte Offline-Prüfung der teilnehmendenbasierten Groupwork-Bausteine."""
from dataclasses import asdict
import argparse
from copy import deepcopy
import json
from pathlib import Path
import time
from collections import Counter
import math

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


def capacity_examples(output):
    """Prüfe spezifizierte Belegungen unabhängig von der Standard-Tischwahl."""
    from aisi.core.models import ROI, SceneState, TableState, TableTarget
    from aisi.generation.groupwork_participants import GroupworkPlan, ParticipantCluster, cluster_seating, groups_are_spatially_distinct
    from aisi.app.sim_layout_rules import compute_synthetic_layout
    def state(poses):
        return SceneState(ROI(0,0,500,500),[
            TableState(f'table_{i}',x,y,r,160,80,table_type='rect')
            for i,(x,y,r) in enumerate(poses)],'groupwork')
    def plan_for(source,clusters,sizes):
        targets=[TableTarget(t.table_id,t.x,t.y,target_rot_deg=t.rot_deg) for t in source.tables]
        plan=GroupworkPlan(targets,[],clusters,sizes,{})
        for cluster in clusters:
            chairs,regions=cluster_seating(source,targets,cluster)
            plan.chairs.extend(chairs);plan.regions[cluster.cluster_id]=regions
        validate_groupwork_plan(source,plan)
        return plan
    single=state(((250,250,37),))
    five=plan_for(single,(ParticipantCluster('single','group_0',('table_0',),5),),(5,))
    assert Counter(c['seat_kind'] for c in five.chairs)=={'regular_long':4,'regular_end':1}
    source=state(((140,206,0),(140,294,0),(390,250,0)))
    seven=plan_for(source,(ParticipantCluster('pair','group_0',('table_0','table_1'),4),
                         ParticipantCluster('single','group_0',('table_2',),3)),(7,))
    assert Counter(c['cluster_id'] for c in seven.chairs)=={'pair':4,'single':3}
    pair=state(((250,206,0),(250,294,0)))
    capacity=[]
    for label,source_state,ids,upper in (('single',single,('table_0',),8),('pair',pair,('table_0','table_1'),11)):
        for count in range(1,upper+1):
            try:
                plan_for(source_state,(ParticipantCluster(label,'group_0',ids,count),),(count,))
                capacity.append(dict(cluster=label,participants=count,passed=True))
            except LayoutConstraintError as exc:
                assert label=='pair' and count>=9
                capacity.append(dict(cluster=label,participants=count,passed=False,error=str(exc)))
    raw=scene_payload(make_default_tables(),chairs=[],persons=[])
    offline=plan_participant_groupwork(build_scene_state_from_dict(_normalize_scene_for_aisi(raw),learning_format='groupwork'),16,5)
    assert len(offline.chairs)==16
    slot_errors=[]
    for people in (16,20,40):
        try:
            compute_synthetic_layout(raw,'groupwork',1.,dict(adaptive_layout_preview=True,participants=people,number_of_groups=5))
        except LayoutConstraintError as exc:
            assert '15 TD-Chair-Slots' in str(exc)
            slot_errors.append(dict(participants=people,error=str(exc)))
        else:
            raise AssertionError('TD-Slotlimit wurde nicht abgelehnt')
    clusters=(ParticipantCluster('a','group_0',('a',),2),ParticipantCluster('b','group_0',('b',),2),ParticipantCluster('c','group_1',('c',),2))
    separated=GroupworkPlan([TableTarget('a',100,250),TableTarget('b',180,250),TableTarget('c',400,250)],[],clusters,(4,2),{})
    assert groups_are_spatially_distinct(separated)
    interleaved=deepcopy(separated);interleaved.targets[1].target_x=450
    assert not groups_are_spatially_distinct(interleaved)
    fig,axes=plt.subplots(1,2,figsize=(12,6))
    plot(axes[0],single,five,'Ein Tisch · fünf Personen · 2 + 2 + 1')
    plot(axes[1],source,seven,'Eine Gruppe · sieben Personen · Pair 4 + Singleton 3')
    fig.tight_layout();fig.savefig(output/'spezifizierte_belegungen.png',dpi=140);plt.close(fig)
    report=dict(five=asdict(five),seven=asdict(seven),capacity=capacity,offline_sixteen=asdict(offline),
                technical_rejections=slot_errors,relative_group_assignment_positive_and_negative=True,
                live_output_enabled=False)
    (output/'capacity_examples.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Spezifizierte Belegungen, geometrische Kapazität, Gruppenzuordnung und TD-Slotlimit geprüft.',flush=True)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--retry-failures',action='store_true',help='Nur Ablehnungen aus --fixtures erneut prüfen und Bericht zusammenführen')
    parser.add_argument('--examples-only',action='store_true',help='Nur Kapazitäts-/Spezifikationsbeispiele prüfen')
    parser.add_argument('--complete',action='store_true',help='Alle Counts 1–15 und zulässigen Gruppenzahlen 1–5 prüfen')
    parser.add_argument('--fixtures',type=Path,help='Gespeicherter validation.json-Bericht als Quelle')
    parser.add_argument('--policy', choices=('group_capacity','few_tables','regular_seats'), default='group_capacity')
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    if args.examples_only:
        capacity_examples(args.output)
        return
    root=Path(__file__).resolve().parents[1]
    sources={'editor':scene_payload(make_default_tables(),chairs=[],persons=[]),
             'live':json.loads((root/'data/aisi/scenes/simulated/live_scene.json').read_text())}
    if args.fixtures:
        saved=json.loads(args.fixtures.read_text())
        sources={name:(saved.get('sources') or saved['fixtures'])[name] for name in ('editor','live')}
    if args.retry_failures and not args.fixtures:
        parser.error('--retry-failures benötigt --fixtures')
    records=[];examples=[];started=time.monotonic()
    cases = (tuple((p,g) for p in range(1,16) for g in range(1,min(p,5)+1))
             if args.complete else ((3,1),(5,1),(7,2),(10,2),(15,2),(15,5)))
    for name,raw in sources.items():
        state=build_scene_state_from_dict(_normalize_scene_for_aisi(raw),learning_format='groupwork')
        selected_cases = (tuple((r['participants'],r['groups']) for r in saved['results']
                          if r['source']==name and not r['passed']) if args.retry_failures else cases)
        for people,groups in selected_cases:
            case_started=time.monotonic()
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
            assert len(plan.group_sizes)==groups and sum(plan.group_sizes)==people
            assert max(plan.group_sizes)-min(plan.group_sizes)<=1
            assert len({c['seat_id'] for c in plan.chairs})==people
            assert Counter(c['group_id'] for c in plan.chairs)=={
                f'group_{i}':n for i,n in enumerate(plan.group_sizes)}
            by_id={t.table_id:t for t in state.tables}
            by_target={t.table_id:t for t in plan.targets}
            from aisi.core.table_geometry import table_allowed_center_bounds
            from aisi.analysis.rect_groupwork_adaptive_prototype import _polygon_distance
            for tid in plan.parked_table_ids:
                t=by_target[tid]
                x0,y0,x1,y1=table_allowed_center_bounds(by_id[tid],t.target_rot_deg,
                    x_min=state.roi.x_min,y_min=state.roi.y_min,x_max=state.roi.x_max,y_max=state.roi.y_max)
                if abs(t.target_rot_deg%180)<1e-8:
                    assert min(abs(t.target_y-y0),abs(t.target_y-y1))<1e-6
                else:
                    assert abs(t.target_rot_deg%180-90)<1e-8
                    assert min(abs(t.target_x-x0),abs(t.target_x-x1))<1e-6
            footprints={tid:table_world_footprint(by_id[tid],(t.target_x,t.target_y),t.target_rot_deg)
                        for tid,t in by_target.items()}
            gaps=[_polygon_distance(footprints[a],footprints[b]) for a in plan.parked_table_ids
                  for c in plan.clusters for b in c.table_ids]
            distances=[math.dist((by_id[t.table_id].x,by_id[t.table_id].y),(t.target_x,t.target_y))
                       for t in plan.targets]
            records.append(dict(source=name,participants=people,groups=groups,policy=policy,passed=True,
                elapsed_s=round(time.monotonic()-case_started,3),total_movement_cm=sum(distances),
                min_park_active_gap_cm=min(gaps,default=None),seat_kinds=dict(Counter(c['seat_kind'] for c in plan.chairs)),
                plan=asdict(plan)))
            label={'group_capacity':'Einzeltisch bis drei, danach Pair','few_tables':'wenige Tische','regular_seats':'Längsseiten bevorzugt'}[policy]
            if name=='editor' and (people,groups) in ((3,1),(5,1),(15,2)):examples.append((state,plan,f'{people} Personen · {groups} Gruppen · {label}'))
            print(name,people,groups,policy,'bestanden',round(time.monotonic()-started,1),'s',flush=True)
    if examples:
        fig,axes=plt.subplots(1,len(examples),figsize=(6*len(examples),6),squeeze=False)
        for ax,(state,plan,title) in zip(axes[0],examples):plot(ax,state,plan,title)
        fig.tight_layout();fig.savefig(args.output/'gruppen_und_sitzprioritaet.png',dpi=140);plt.close(fig)
    if args.retry_failures:
        updates={(r['source'],r['participants'],r['groups']):r for r in records}
        records=[updates.get((r['source'],r['participants'],r['groups']),r) for r in saved['results']]
    passed=sum(record['passed'] for record in records)
    report=dict(complete_matrix=args.complete or (args.retry_failures and saved.get('complete_matrix',False)),retry_failures=args.retry_failures,cases=len(records),passed=passed,determinism=passed,scene_order=passed,
                sources=sources,results=records,live_output_enabled=False)
    (args.output/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(f'{passed}/{len(records)} Fälle realisiert; keine OSC-Ausgabe.',flush=True)
    if args.complete:capacity_examples(args.output)
    if passed != len(records):raise SystemExit(1)


if __name__=='__main__':main()
