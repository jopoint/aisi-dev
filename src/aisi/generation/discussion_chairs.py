"""Discussion-Chairs aus den kanonischen äußeren Sitzflächen des Rect-Rings."""
from copy import deepcopy
from dataclasses import dataclass, replace
from functools import lru_cache
from itertools import combinations
import math

from aisi.core.models import ROI, SceneState, TableState, TableTarget
from aisi.core.table_geometry import (
    GEOMETRY_EPSILON, circle_inside_convex_polygon, circle_intersects_convex_polygon,
    convex_polygons_intersect, polygon_inside_roi, resolve_table_state_geometry,
    table_world_footprint,
)
from aisi.analysis.rect_groupwork_adaptive_prototype import single_long_side_clearance_region
from aisi.generation.adaptive_layout_v1 import LayoutConstraintError, evenly_distribute
from aisi.generation.layout_synthesizer import (
    DISCUSSION_SEAT_CLEARANCE_DEPTH_CM, _layout_rect_discussion_templates,
    _rect_discussion_singleton_clearances_valid,
)

CHAIR_RADIUS_CM = 25.
# Johannes akzeptiert den geplotteten 0,51-cm-Überstand an den Rundungen.
ROUNDED_CORNER_TOLERANCE_CM = .51


@dataclass
class DiscussionChairPlan:
    targets: list[TableTarget]
    chairs: list[dict]
    regions: dict[str, tuple]


def _roi_polygon(roi):
    return ((roi.x_min,roi.y_min),(roi.x_max,roi.y_min),
            (roi.x_max,roi.y_max),(roi.x_min,roi.y_max))


def _seating_geometry(state, targets):
    by_id={t.table_id:t for t in state.tables}
    center=(math.fsum(t.target_x for t in targets)/len(targets),
            math.fsum(t.target_y for t in targets)/len(targets))
    result={}
    for target in targets:
        table=by_id[target.table_id];g=resolve_table_state_geometry(table)
        angle=math.radians(target.target_rot_deg)
        tangent=(math.cos(angle),math.sin(angle));normal=(-math.sin(angle),math.cos(angle))
        outward=(target.target_x-center[0],target.target_y-center[1])
        # A centered singleton has no radial direction: use +local short axis.
        sign=1. if normal[0]*outward[0]+normal[1]*outward[1]>=0. else -1.
        direction=(sign*normal[0],sign*normal[1])
        region=single_long_side_clearance_region(target,table,seat_direction=direction,
            clearance_depth_cm=DISCUSSION_SEAT_CLEARANCE_DEPTH_CM)
        distance=g.nominal_depth/2+DISCUSSION_SEAT_CLEARANCE_DEPTH_CM/2
        row_center=(target.target_x+direction[0]*distance,target.target_y+direction[1]*distance)
        strip_table=replace(table,table_type=None,width=g.nominal_width,height=DISCUSSION_SEAT_CLEARANCE_DEPTH_CM)
        rectangle=table_world_footprint(strip_table,row_center,target.target_rot_deg)
        result[target.table_id]=(region,rectangle,row_center,tangent,g)
    return result


def validate_discussion_chairs(state, plan):
    by_id={t.table_id:t for t in state.tables}
    if len(plan.targets)!=len(by_id) or {t.table_id for t in plan.targets}!=set(by_id):
        raise LayoutConstraintError('Discussion muss alle Tischidentitäten erhalten.')
    footprints={t.table_id:table_world_footprint(by_id[t.table_id],(t.target_x,t.target_y),t.target_rot_deg)
                for t in plan.targets}
    roi=_roi_polygon(state.roi)
    if any(not polygon_inside_roi(p,x_min=state.roi.x_min,y_min=state.roi.y_min,
           x_max=state.roi.x_max,y_max=state.roi.y_max) for p in footprints.values()) or any(
           convex_polygons_intersect(a,b) for a,b in combinations(footprints.values(),2)):
        raise LayoutConstraintError('Discussion-Tischkollision oder ROI-Verletzung.')
    if not _rect_discussion_singleton_clearances_valid(state,plan.targets):
        raise LayoutConstraintError("Blockierte Discussion-Bewegungsfläche oder ROI-Verletzung.")
    geometry=_seating_geometry(state,plan.targets)
    if len({c['seat_id'] for c in plan.chairs})!=len(plan.chairs):
        raise LayoutConstraintError('Discussion-Seat-IDs müssen eindeutig sein.')
    for tid,(region,rectangle,_,_,_) in geometry.items():
        if plan.regions.get(tid)!=region:
            raise LayoutConstraintError('Discussion-Sitzfläche stimmt nicht mit der äußeren Tischseite überein.')
        if not polygon_inside_roi(region,x_min=state.roi.x_min,y_min=state.roi.y_min,
            x_max=state.roi.x_max,y_max=state.roi.y_max) or any(
            convex_polygons_intersect(region,p) for other,p in footprints.items() if other!=tid):
            raise LayoutConstraintError('Blockierte Discussion-Sitzfläche oder ROI-Verletzung.')
    counts={tid:0 for tid in by_id}
    for chair in plan.chairs:
        tid=chair['table_id'];point=(chair['x_cm'],chair['y_cm']);radius=chair['radius_cm']
        if tid not in geometry or radius!=CHAIR_RADIUS_CM:
            raise LayoutConstraintError('Ungültige Discussion-Chair-Zuordnung oder Größe.')
        counts[tid]+=1
        region,rectangle,*_=geometry[tid]
        if not circle_inside_convex_polygon(point,radius,roi):
            raise LayoutConstraintError('Discussion-Chair überschreitet die ROI.')
        # Only the rounded corners may be exceeded. Straight strip bounds,
        # full circle ROI and all foreign collision checks retain the real radius.
        if not circle_inside_convex_polygon(point,radius,rectangle) or not circle_inside_convex_polygon(
            point,radius-ROUNDED_CORNER_TOLERANCE_CM,region):
            raise LayoutConstraintError('Discussion-Chair überschreitet seine Sitzfläche.')
        for other,footprint in footprints.items():
            checked_radius=radius-10*GEOMETRY_EPSILON if other==tid else radius
            if circle_intersects_convex_polygon(point,checked_radius,footprint):
                raise LayoutConstraintError('Discussion-Chair kollidiert mit einem Tisch.')
    if any(count>3 for count in counts.values()):
        raise LayoutConstraintError('Discussion erlaubt höchstens drei Chairs pro Tisch.')
    if any(math.dist((a['x_cm'],a['y_cm']),(b['x_cm'],b['y_cm']))<=a['radius_cm']+b['radius_cm']+GEOMETRY_EPSILON
           for a,b in combinations(plan.chairs,2)):
        raise LayoutConstraintError('Discussion-Chairs kollidieren.')


def _assemble(state, targets, participants, *, validate=True):
    geometry=_seating_geometry(state,targets);counts=evenly_distribute(participants,len(targets))
    chairs=[]
    for tid,count in zip(sorted(geometry),counts):
        region,rectangle,center,tangent,g=geometry[tid]
        offsets={0:(),1:(0.,),2:(-g.nominal_width/4,g.nominal_width/4),
                 3:(-(g.nominal_width/2-CHAIR_RADIUS_CM-3),0.,g.nominal_width/2-CHAIR_RADIUS_CM-3)}[count]
        for index,offset in enumerate(offsets):
            chairs.append(dict(x_cm=center[0]+tangent[0]*offset,y_cm=center[1]+tangent[1]*offset,
                radius_cm=CHAIR_RADIUS_CM,table_id=tid,seat_id=f'{tid}:discussion:{index}',
                seat_kind='dense_long' if count==3 and index==1 else 'regular_long'))
    plan=DiscussionChairPlan(targets,chairs,{tid:data[0] for tid,data in geometry.items()})
    if validate:
        validate_discussion_chairs(state,plan)
    return plan


@lru_cache(maxsize=32)
def _ring_targets(roi,key):
    state=SceneState(ROI(*roi),[TableState(*t[:6],table_type=t[6]) for t in key],'discussion')
    return _layout_rect_discussion_templates(state,state.tables)[0]


@lru_cache(maxsize=64)
def _cached_plan(roi,key,participants):
    state=SceneState(ROI(*roi),[TableState(*t[:6],table_type=t[6]) for t in key],'discussion')
    try:
        return _assemble(state,deepcopy(_ring_targets(roi,key)),participants)
    except LayoutConstraintError:
        if len(key)!=5:
            raise
        # Small corner overhang must never become ROI overhang. Reuse the
        # accepted phase/center search with a complete chair candidate filter.
        def accept(targets):
            try:
                _assemble(state,targets,participants)
                return True
            except LayoutConstraintError:
                return False
        def bounds(targets):
            plan=_assemble(state,targets,participants,validate=False)
            return tuple(point for chair in plan.chairs for point in (
                (chair["x_cm"]-CHAIR_RADIUS_CM,chair["y_cm"]),
                (chair["x_cm"]+CHAIR_RADIUS_CM,chair["y_cm"]),
                (chair["x_cm"],chair["y_cm"]-CHAIR_RADIUS_CM),
                (chair["x_cm"],chair["y_cm"]+CHAIR_RADIUS_CM)))
        try:
            targets,_=_layout_rect_discussion_templates(state,state.tables,
                candidate_filter=accept,candidate_bounds=bounds)
        except ValueError as exc:
            raise LayoutConstraintError('Kein gültiger Discussion-Ring für diese Chair-Belegung.') from exc
        return _assemble(state,targets,participants)


def plan_discussion_chairs(state, participants, targets=None):
    if type(participants) is not int or participants<1:
        raise LayoutConstraintError('Discussion benötigt eine positive ganzzahlige Teilnehmerzahl.')
    if not 1<=len(state.tables)<=5 or any(t.table_type!='rect' for t in state.tables):
        raise LayoutConstraintError('Discussion-Chairs benötigen ein bis fünf Rect-Tische.')
    if participants>3*len(state.tables):
        raise LayoutConstraintError(f'Discussion-Kapazität überschritten: höchstens {3*len(state.tables)} Personen an {len(state.tables)} Tischen.')
    if targets is not None:
        return _assemble(state,targets,participants)
    key=tuple((t.table_id,t.x,t.y,t.rot_deg,t.width,t.height,t.table_type)
              for t in sorted(state.tables,key=lambda t:t.table_id))
    roi=(state.roi.x_min,state.roi.y_min,state.roi.x_max,state.roi.y_max)
    plan=deepcopy(_cached_plan(roi,key,participants))
    by_id={t.table_id:t for t in plan.targets}
    plan.targets=[by_id[t.table_id] for t in state.tables]
    return plan
