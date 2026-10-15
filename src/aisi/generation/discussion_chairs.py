"""Teilnehmerabhängige Discussion: verbundene Zweiergruppe, Viererring, Pentagon."""
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
from aisi.analysis.rect_groupwork_adaptive_prototype import (
    single_long_side_clearance_region, singleton_long_side_clearance_regions,
    _polygons_overlap_with_positive_area, _polygon_distance,
)
from aisi.generation.adaptive_layout_v1 import LayoutConstraintError, evenly_distribute
from aisi.generation.layout_synthesizer import (
    DISCUSSION_SEAT_CLEARANCE_DEPTH_CM, _layout_rect_discussion_templates,
    _rect_discussion_singleton_clearances_valid, _rect_discussion_ring_targets,
    _tables_in_source_angular_order, _blend_targets_with_source,
)

CHAIR_RADIUS_CM = 25.
PARK_ACTIVE_CLEARANCE_CM = 60.
# Johannes akzeptiert den geplotteten 0,51-cm-Überstand an den Rundungen.
ROUNDED_CORNER_TOLERANCE_CM = .51


@dataclass
class DiscussionChairPlan:
    targets: list[TableTarget]
    chairs: list[dict]
    regions: dict[str, tuple]
    active_table_ids: tuple[str, ...] = ()
    parked_table_ids: tuple[str, ...] = ()
    topology: str = "ring"


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



def _ring_geometry(state, targets):
    geometry = _seating_geometry(state, targets)
    if len(targets)!=4:
        return geometry
    by_id = {t.table_id:t for t in state.tables}
    cx = math.fsum(t.target_x for t in targets)/4
    cy = math.fsum(t.target_y for t in targets)/4
    ordered = sorted(targets,key=lambda t:math.atan2(t.target_y-cy,t.target_x-cx))
    # Anchor to identity so common rotation never changes the corner roles.
    start = min(range(4),key=lambda i:ordered[i].table_id)
    ordered = ordered[start:]+ordered[:start]
    for first,second in zip(ordered,ordered[1:]+ordered[:1]):
        a = table_world_footprint(by_id[first.table_id],(first.target_x,first.target_y),first.target_rot_deg)
        b = table_world_footprint(by_id[second.table_id],(second.target_x,second.target_y),second.target_rot_deg)
        outward = (first.target_x+second.target_x-2*cx,first.target_y+second.target_y-2*cy)
        # The two outer supporting vertices bound the free corner between
        # neighboring tables. Derive the seat strip from this canonical edge.
        support = lambda p:p[0]*outward[0]+p[1]*outward[1]
        va,vb = max(a,key=support),max(b,key=support)
        width = math.dist(va,vb)
        if width<=2*CHAIR_RADIUS_CM:
            raise LayoutConstraintError('Discussion-Ecke bietet nicht genügend Sitzbreite.')
        tangent = ((vb[0]-va[0])/width,(vb[1]-va[1])/width)
        normal = (-tangent[1],tangent[0])
        if normal[0]*outward[0]+normal[1]*outward[1]<0:
            normal = (-normal[0],-normal[1])
        edge = ((va[0]+vb[0])/2,(va[1]+vb[1])/2)
        rotation = math.degrees(math.atan2(tangent[1],tangent[0]))
        depth = resolve_table_state_geometry(by_id[first.table_id]).nominal_depth
        proxy = replace(by_id[first.table_id],table_type=None,width=width,height=depth)
        target = replace(first,target_x=edge[0]-normal[0]*depth/2,
            target_y=edge[1]-normal[1]*depth/2,target_rot_deg=rotation)
        region = single_long_side_clearance_region(target,proxy,seat_direction=normal,
            clearance_depth_cm=DISCUSSION_SEAT_CLEARANCE_DEPTH_CM)
        row = (edge[0]+normal[0]*DISCUSSION_SEAT_CLEARANCE_DEPTH_CM/2,
               edge[1]+normal[1]*DISCUSSION_SEAT_CLEARANCE_DEPTH_CM/2)
        strip = replace(proxy,height=DISCUSSION_SEAT_CLEARANCE_DEPTH_CM)
        rectangle = table_world_footprint(strip,row,rotation)
        geometry[f'corner:{first.table_id}'] = (region,rectangle,row,tangent,resolve_table_state_geometry(proxy))
    return geometry

def _validate_ring_chairs(state, plan):
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
    geometry=_ring_geometry(state,plan.targets)
    if len({c['seat_id'] for c in plan.chairs})!=len(plan.chairs):
        raise LayoutConstraintError('Discussion-Seat-IDs müssen eindeutig sein.')
    if set(plan.regions)!=set(geometry):
        raise LayoutConstraintError('Ungültige Discussion-Sitzflächenzuordnung.')
    for tid,(region,rectangle,_,_,_) in geometry.items():
        if plan.regions.get(tid)!=region:
            raise LayoutConstraintError('Discussion-Sitzfläche stimmt nicht mit der äußeren Tischseite überein.')
        if not polygon_inside_roi(region,x_min=state.roi.x_min,y_min=state.roi.y_min,
            x_max=state.roi.x_max,y_max=state.roi.y_max) or any(
            (_polygons_overlap_with_positive_area(region,p) if tid.startswith('corner:')
             else convex_polygons_intersect(region,p)) for other,p in footprints.items() if other!=tid):
            raise LayoutConstraintError('Blockierte Discussion-Sitzfläche oder ROI-Verletzung.')
    counts={tid:0 for tid in by_id}
    long_counts={tid:0 for tid in by_id}
    corner_counts={}
    for chair in plan.chairs:
        tid=chair['table_id'];point=(chair['x_cm'],chair['y_cm']);radius=chair['radius_cm']
        key=chair.get('region_id',tid)
        if tid not in by_id or key not in geometry or radius!=CHAIR_RADIUS_CM:
            raise LayoutConstraintError('Ungültige Discussion-Chair-Zuordnung oder Größe.')
        if key.startswith('corner:') and (key!=f'corner:{tid}' or chair.get('seat_kind')!='regular_corner'):
            raise LayoutConstraintError('Ungültige Discussion-Chair-Zuordnung oder Größe.')
        counts[tid]+=1
        if key.startswith('corner:'):
            corner_counts[key]=corner_counts.get(key,0)+1
        else:
            long_counts[tid]+=1
        region,rectangle,*_=geometry[key]
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
    if len(plan.targets)==4 and (any(count>2 for count in long_counts.values())
                                or any(count>1 for count in corner_counts.values())):
        raise LayoutConstraintError('Vierer-Discussion erlaubt zwei Längsplätze und einen Eckplatz je Tisch.')
    if any(count>3 for count in counts.values()):
        raise LayoutConstraintError('Discussion erlaubt höchstens drei Chairs pro Tisch.')
    if any(math.dist((a['x_cm'],a['y_cm']),(b['x_cm'],b['y_cm']))<=a['radius_cm']+b['radius_cm']+GEOMETRY_EPSILON
           for a,b in combinations(plan.chairs,2)):
        raise LayoutConstraintError('Discussion-Chairs kollidieren.')


def _assemble(state, targets, participants, *, validate=True):
    geometry=_ring_geometry(state,targets)
    long_participants=min(participants,8) if len(targets)==4 else participants
    counts=evenly_distribute(long_participants,len(targets))
    chairs=[]
    for tid,count in zip(sorted(t.table_id for t in targets),counts):
        region,rectangle,center,tangent,g=geometry[tid]
        offsets={0:(),1:(0.,),2:(-g.nominal_width/4,g.nominal_width/4),
                 3:(-(g.nominal_width/2-CHAIR_RADIUS_CM-3),0.,g.nominal_width/2-CHAIR_RADIUS_CM-3)}[count]
        for index,offset in enumerate(offsets):
            chairs.append(dict(x_cm=center[0]+tangent[0]*offset,y_cm=center[1]+tangent[1]*offset,
                radius_cm=CHAIR_RADIUS_CM,table_id=tid,seat_id=f'{tid}:discussion:{index}',
                seat_kind='dense_long' if count==3 and index==1 else 'regular_long'))
    if len(targets)==4 and participants>8:
        corners=[key for key in geometry if key.startswith('corner:')]
        # Fill opposite corners first when only two extra seats are requested.
        for index in (0,2,1,3)[:participants-8]:
            key=corners[index];center=geometry[key][2];tid=key.removeprefix('corner:')
            chairs.append(dict(x_cm=center[0],y_cm=center[1],radius_cm=CHAIR_RADIUS_CM,
                table_id=tid,seat_id=f'discussion:{key}',seat_kind='regular_corner',region_id=key))
    plan=DiscussionChairPlan(targets,chairs,{tid:data[0] for tid,data in geometry.items()})
    if validate:
        validate_discussion_chairs(state,plan)
    return plan


@lru_cache(maxsize=32)
def _ring_targets(roi,key):
    state=SceneState(ROI(*roi),[TableState(*t[:6],table_type=t[6]) for t in key],'discussion')
    return _layout_rect_discussion_templates(state,state.tables)[0]


@lru_cache(maxsize=64)
def _cached_ring_plan(roi,key,participants):
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



def _required_tables(participants):
    return 2 if participants <= 6 else 4 if participants <= 12 else 5


def _pair_geometry(state, targets, participants):
    """One shared long edge, outward rows and optional shared short-end seats."""
    by_id = {t.table_id: t for t in state.tables}
    first, second = sorted(targets, key=lambda t: t.table_id)
    g = resolve_table_state_geometry(by_id[first.table_id])
    angle = math.radians(first.target_rot_deg)
    tangent = (math.cos(angle), math.sin(angle))
    normal = (-tangent[1], tangent[0])
    delta = (second.target_x-first.target_x, second.target_y-first.target_y)
    parallel = abs((second.target_rot_deg-first.target_rot_deg+90) % 180-90) < 1e-7
    along = delta[0]*tangent[0]+delta[1]*tangent[1]
    across = delta[0]*normal[0]+delta[1]*normal[1]
    if not parallel or abs(along)>1e-7 or abs(abs(across)-g.nominal_depth)>1e-7:
        raise LayoutConstraintError('Discussion-Zweiergruppe benötigt eine gemeinsame Längskante.')
    geometry = _seating_geometry(state, targets)
    # Ends span both joined tables. Use the canonical strip on a rotated
    # combined-table proxy, rather than two overlapping half-width seat zones.
    center = ((first.target_x+second.target_x)/2, (first.target_y+second.target_y)/2)
    proxy = replace(by_id[first.table_id], table_type=None,
                    width=2*g.nominal_depth, height=g.nominal_width)
    proxy_target = replace(first, target_x=center[0], target_y=center[1],
                           target_rot_deg=first.target_rot_deg+90)
    for index, sign in enumerate((-1., 1.)):
        if participants < 5+index:
            break
        direction = (sign*tangent[0], sign*tangent[1])
        region = single_long_side_clearance_region(proxy_target, proxy,
            seat_direction=direction, clearance_depth_cm=DISCUSSION_SEAT_CLEARANCE_DEPTH_CM)
        distance = g.nominal_width/2+DISCUSSION_SEAT_CLEARANCE_DEPTH_CM/2
        row = (center[0]+direction[0]*distance, center[1]+direction[1]*distance)
        strip = replace(proxy, width=2*g.nominal_depth, height=DISCUSSION_SEAT_CLEARANCE_DEPTH_CM)
        rectangle = table_world_footprint(strip, row, proxy_target.target_rot_deg)
        geometry[f'end:{index}'] = (region, rectangle, row, normal, g)
    return geometry


def _assemble_pair(state, targets, participants):
    geometry = _pair_geometry(state, targets, participants)
    chairs = []
    for tid, count in zip(sorted(t.table_id for t in targets), evenly_distribute(min(participants,4),2)):
        _, _, center, tangent, g = geometry[tid]
        offsets = () if count == 0 else (0.,) if count == 1 else (-g.nominal_width/4,g.nominal_width/4)
        for index, offset in enumerate(offsets):
            chairs.append(dict(x_cm=center[0]+tangent[0]*offset, y_cm=center[1]+tangent[1]*offset,
                radius_cm=CHAIR_RADIUS_CM, table_id=tid, seat_id=f'{tid}:discussion:{index}',
                seat_kind='regular_long', region_id=tid))
    for key in sorted(k for k in geometry if k.startswith('end:')):
        point = geometry[key][2]
        chairs.append(dict(x_cm=point[0], y_cm=point[1], radius_cm=CHAIR_RADIUS_CM,
            table_id=sorted(t.table_id for t in targets)[int(key.split(':')[1])], seat_id=f'discussion:{key}',
            seat_kind='regular_end', region_id=key))
    return DiscussionChairPlan(list(targets), chairs, {k:v[0] for k,v in geometry.items()},
        tuple(sorted(t.table_id for t in targets)), topology='pair')


def _active_state(state, active_ids):
    return replace(state, tables=[t for t in state.tables if t.table_id in active_ids])


def validate_discussion_chairs(state, plan):
    by_id = {t.table_id:t for t in state.tables}
    active = plan.active_table_ids or tuple(t.table_id for t in plan.targets)
    parked = plan.parked_table_ids
    if (len(active)!=len(set(active)) or len(parked)!=len(set(parked)) or set(active)&set(parked)
        or set(active)|set(parked)!=set(by_id) or len(plan.targets)!=len(by_id)
        or {t.table_id for t in plan.targets}!=set(by_id)):
        raise LayoutConstraintError('Ungültige aktive/geparkte Discussion-Tischzuordnung.')
    if not 1<=len(plan.chairs)<=15 or len(active)!=_required_tables(len(plan.chairs)):
        raise LayoutConstraintError('Discussion-Tischanzahl passt nicht zur Teilnehmerstufe.')
    active_targets = [t for t in plan.targets if t.table_id in active]
    active_state = _active_state(state, active)
    footprints = {t.table_id:table_world_footprint(by_id[t.table_id],
                  (t.target_x,t.target_y),t.target_rot_deg) for t in plan.targets}
    for tid, polygon in footprints.items():
        if not polygon_inside_roi(polygon,x_min=state.roi.x_min,y_min=state.roi.y_min,
                                  x_max=state.roi.x_max,y_max=state.roi.y_max):
            raise LayoutConstraintError('Discussion-Tisch überschreitet die ROI.')
    for (a,first),(b,second) in combinations(footprints.items(),2):
        joined = plan.topology=='pair' and a in active and b in active
        collision = (_polygons_overlap_with_positive_area(first,second) if joined
                     else convex_polygons_intersect(first,second))
        if collision:
            raise LayoutConstraintError('Discussion-Tische kollidieren.')
    if any(_polygon_distance(footprints[p],footprints[a])<PARK_ACTIVE_CLEARANCE_CM-1e-7 for p in parked for a in active):
        raise LayoutConstraintError('Geparkter Discussion-Tisch unterschreitet 60 cm Abstand.')
    if plan.topology=='ring':
        _validate_ring_chairs(active_state, replace(plan,targets=active_targets))
        # Retain both accepted ring movement strips, including the inner side.
        regions = [r for t in active_targets for r in singleton_long_side_clearance_regions(
            t,by_id[t.table_id],clearance_depth_cm=DISCUSSION_SEAT_CLEARANCE_DEPTH_CM)]
        regions.extend(r for key,r in plan.regions.items() if key.startswith('corner:'))
    elif plan.topology=='pair':
        if len(active)!=2 or not 1<=len(plan.chairs)<=6:
            raise LayoutConstraintError('Ungültige Discussion-Zweiergruppe.')
        geometry = _pair_geometry(active_state, active_targets, len(plan.chairs))
        if plan.regions!={k:v[0] for k,v in geometry.items()}:
            raise LayoutConstraintError('Ungültige Discussion-Sitzflächen.')
        regions = list(plan.regions.values())
        if len({c['seat_id'] for c in plan.chairs})!=len(plan.chairs):
            raise LayoutConstraintError('Doppelte Discussion-Seat-ID.')
        for chair in plan.chairs:
            key = chair.get('region_id'); point = (chair['x_cm'],chair['y_cm'])
            if chair['table_id'] not in active or key not in geometry or chair['radius_cm']!=CHAIR_RADIUS_CM:
                raise LayoutConstraintError('Ungültige Discussion-Chair-Zuordnung.')
            region,rectangle,*_ = geometry[key]
            if (not circle_inside_convex_polygon(point,CHAIR_RADIUS_CM,_roi_polygon(state.roi))
                or not circle_inside_convex_polygon(point,CHAIR_RADIUS_CM,rectangle)
                or not circle_inside_convex_polygon(point,CHAIR_RADIUS_CM-ROUNDED_CORNER_TOLERANCE_CM,region)):
                raise LayoutConstraintError('Discussion-Chair überschreitet Sitzfläche oder ROI.')
            # End seats touch both table halves at their shared short-end seam.
            contacts = active if key.startswith('end:') else (chair['table_id'],)
            for tid,footprint in footprints.items():
                radius = CHAIR_RADIUS_CM-10*GEOMETRY_EPSILON if tid in contacts else CHAIR_RADIUS_CM
                if circle_intersects_convex_polygon(point,radius,footprint):
                    raise LayoutConstraintError('Discussion-Chair kollidiert mit einem Tisch.')
        if any(math.dist((a['x_cm'],a['y_cm']),(b['x_cm'],b['y_cm']))<=2*CHAIR_RADIUS_CM+GEOMETRY_EPSILON
               for a,b in combinations(plan.chairs,2)):
            raise LayoutConstraintError('Discussion-Chairs kollidieren.')
    else:
        raise LayoutConstraintError('Unbekannte Discussion-Topologie.')
    for region in regions:
        if not polygon_inside_roi(region,x_min=state.roi.x_min,y_min=state.roi.y_min,
                                  x_max=state.roi.x_max,y_max=state.roi.y_max):
            raise LayoutConstraintError('Discussion-Sitzfläche überschreitet die ROI.')
        if any(convex_polygons_intersect(region,footprints[tid]) for tid in parked):
            raise LayoutConstraintError('Geparkter Tisch blockiert Discussion-Sitzfläche.')
    # Pair strips may touch their own active edge, but cannot enter any table.
    if plan.topology=='pair' and any(_polygons_overlap_with_positive_area(region,fp)
        for region in regions for fp in footprints.values()):
        raise LayoutConstraintError('Blockierte Discussion-Sitzfläche.')
    for chair in plan.chairs:
        if any(circle_intersects_convex_polygon((chair['x_cm'],chair['y_cm']),CHAIR_RADIUS_CM,footprints[tid])
               for tid in parked):
            raise LayoutConstraintError('Geparkter Tisch blockiert Discussion-Chair.')


def _attach_parking(state, plan, parking_cache):
    from aisi.app.sim_layout_rules import _compact_park_targets
    from aisi.generation.adaptive_layout_v1 import _parking_candidates
    active = plan.active_table_ids or tuple(t.table_id for t in plan.targets)
    by_id = {t.table_id:t for t in state.tables}
    parked = sorted((t for t in state.tables if t.table_id not in active),key=lambda t:t.table_id)
    regions = (list(plan.regions.values()) if plan.topology=='pair' else
        [r for t in plan.targets for r in singleton_long_side_clearance_regions(
            t,by_id[t.table_id],clearance_depth_cm=DISCUSSION_SEAT_CLEARANCE_DEPTH_CM)])
    if plan.topology=='ring':
        regions.extend(r for key,r in plan.regions.items() if key.startswith('corner:'))
    # Swapping the two initial table bindings leaves occupied geometry and
    # parked identities unchanged. Reuse the canonical parking solve locally.
    occupied = tuple(sorted(table_world_footprint(by_id[t.table_id],
        (t.target_x,t.target_y),t.target_rot_deg) for t in plan.targets))
    parking_key = (tuple(sorted(active)),occupied,tuple(sorted(regions)))
    if parking_key not in parking_cache:
        try:
            parking_cache[parking_key] = _compact_park_targets(state,parked,plan.targets,_parking_candidates(None),
                exclusion_regions=regions,edge_aligned=True,min_active_gap_cm=PARK_ACTIVE_CLEARANCE_CM,
                prefer_short_movement=True)
        except ValueError:
            parking_cache[parking_key] = None
    extra = deepcopy(parking_cache[parking_key])
    if extra is None:
        raise LayoutConstraintError('Keine zulässigen Discussion-Parkbuchten.')
    result = replace(plan,targets=[*plan.targets,*extra],active_table_ids=tuple(active),
                     parked_table_ids=tuple(t.table_id for t in parked))
    validate_discussion_chairs(state,result)
    return result


def _pair_candidates(state,participants):
    tables = sorted(state.tables,key=lambda t:t.table_id)
    g = resolve_table_state_geometry(tables[0]); cx,cy = state.roi.center
    for rotation in (0.,90.):
        angle = math.radians(rotation); normal = (-math.sin(angle),math.cos(angle))
        targets = [TableTarget(t.table_id,cx+sign*normal[0]*g.nominal_depth/2,
                   cy+sign*normal[1]*g.nominal_depth/2,t.rot_deg,rotation)
                   for t,sign in zip(tables,(-1.,1.))]
        yield _assemble_pair(state,targets,participants)
        swapped = [replace(targets[1],table_id=tables[0].table_id,source_rot_deg=tables[0].rot_deg),
                   replace(targets[0],table_id=tables[1].table_id,source_rot_deg=tables[1].rot_deg)]
        yield _assemble_pair(state,swapped,participants)


def _four_candidates(state,participants):
    key = tuple((t.table_id,t.x,t.y,t.rot_deg,t.width,t.height,t.table_type)
                for t in sorted(state.tables,key=lambda t:t.table_id))
    roi = (state.roi.x_min,state.roi.y_min,state.roi.x_max,state.roi.y_max)
    baseline = _assemble(state,deepcopy(_ring_targets(roi,key)),participants,validate=False)
    yield baseline
    cx = math.fsum(t.target_x for t in baseline.targets)/4
    cy = math.fsum(t.target_y for t in baseline.targets)/4
    radius = math.hypot(baseline.targets[0].target_x-cx,baseline.targets[0].target_y-cy)
    tables = _tables_in_source_angular_order(state.tables,state.roi.center)
    by_id = {t.table_id:t for t in tables}
    for degrees in range(0,360,15):
        targets = _rect_discussion_ring_targets(tables,(0.,0.),radius,math.radians(degrees))
        relative = _assemble(state,targets,participants,validate=False)
        points = [p for t in targets for r in singleton_long_side_clearance_regions(t,by_id[t.table_id],
                  clearance_depth_cm=DISCUSSION_SEAT_CLEARANCE_DEPTH_CM) for p in r]
        points.extend(p for key,r in relative.regions.items() if key.startswith('corner:') for p in r)
        points.extend((c['x_cm']+dx,c['y_cm']+dy) for c in relative.chairs
                      for dx,dy in ((-25,0),(25,0),(0,-25),(0,25)))
        x0=state.roi.x_min-min(x for x,y in points); x1=state.roi.x_max-max(x for x,y in points)
        y0=state.roi.y_min-min(y for x,y in points); y1=state.roi.y_max-max(y for x,y in points)
        if x0>x1 or y0>y1:
            continue
        center = (max(x0,min(x1,state.roi.center[0])),max(y0,min(y1,state.roi.center[1])))
        for x,y in dict.fromkeys((center,(x0,y0),(x0,y1),(x1,y0),(x1,y1))):
            shifted = [replace(t,target_x=t.target_x+x,target_y=t.target_y+y,
                       facing_target_x=x,facing_target_y=y) for t in targets]
            yield _assemble(state,shifted,participants,validate=False)


def _solve_topology(state,participants):
    required = _required_tables(participants)
    selections = combinations(sorted(state.tables,key=lambda t:t.table_id),required)
    best = None
    parking_cache = {}
    for tables in selections:
        active_state = replace(state,tables=list(tables))
        if required==2:
            candidates = _pair_candidates(active_state,participants)
        elif required==4:
            candidates = _four_candidates(active_state,participants)
        else:
            key = tuple((t.table_id,t.x,t.y,t.rot_deg,t.width,t.height,t.table_type)
                        for t in sorted(tables,key=lambda t:t.table_id))
            roi = (state.roi.x_min,state.roi.y_min,state.roi.x_max,state.roi.y_max)
            candidates = (deepcopy(_cached_ring_plan(roi,key,participants)),)
        for candidate in candidates:
            try:
                complete = _attach_parking(state,candidate,parking_cache)
            except ValueError:
                continue
            targets = {t.table_id:t for t in complete.targets}
            distances = [math.dist((t.x,t.y),(targets[t.table_id].target_x,targets[t.table_id].target_y))
                         for t in state.tables]
            rotations = math.fsum(abs((targets[t.table_id].target_rot_deg-t.rot_deg+90)%180-90) for t in state.tables)
            score = (math.fsum(distances),max(distances),rotations,tuple(sorted(complete.active_table_ids)))
            if best is None or score<best[0]:
                best = (score,complete)
    if best is None:
        raise LayoutConstraintError('Keine gültige gemeinsame Discussion-Anordnung mit Parktischen gefunden.')
    plan = best[1];by_id = {t.table_id:t for t in plan.targets}
    return replace(plan,targets=[by_id[t.table_id] for t in state.tables])


@lru_cache(maxsize=64)
def _cached_plan(roi,key,participants):
    state = SceneState(ROI(*roi),[TableState(*t[:6],table_type=t[6]) for t in key],'discussion')
    # Keep table identities and poses stable within a tier. Reserve its maximum
    # seating geometry once; subsequent changes only adjust occupied chairs.
    capacity = 6 if participants<=6 else 12 if participants<=12 else 15
    full = deepcopy(_cached_topology_geometry(roi,key,capacity))
    active_targets = [t for t in full.targets if t.table_id in full.active_table_ids]
    active_state = _active_state(state,full.active_table_ids)
    seated = (_assemble_pair(active_state,active_targets,participants) if capacity==6
              else _assemble(active_state,active_targets,participants,validate=False))
    result = replace(seated,targets=full.targets,active_table_ids=full.active_table_ids,
                     parked_table_ids=full.parked_table_ids)
    validate_discussion_chairs(state,result)
    return result


@lru_cache(maxsize=48)
def _cached_topology_geometry(roi,key,capacity):
    state = SceneState(ROI(*roi),[TableState(*t[:6],table_type=t[6]) for t in key],'discussion')
    return _solve_topology(state,capacity)


def plan_discussion_chairs(state,participants):
    if type(participants) is not int or not 1<=participants<=15:
        raise LayoutConstraintError('Discussion benötigt eine ganzzahlige Teilnehmerzahl von 1 bis 15.')
    required = _required_tables(participants)
    if len(state.tables)>5 or any(t.table_type!='rect' for t in state.tables):
        raise LayoutConstraintError('Discussion-Chairs benötigen höchstens fünf Rect-Tische.')
    if len(state.tables)<required:
        raise LayoutConstraintError(f'Discussion benötigt für {participants} Personen {required} Tische; nur {len(state.tables)} verfügbar.')
    key = tuple((t.table_id,t.x,t.y,t.rot_deg,t.width,t.height,t.table_type)
                for t in sorted(state.tables,key=lambda t:t.table_id))
    roi = (state.roi.x_min,state.roi.y_min,state.roi.x_max,state.roi.y_max)
    plan = deepcopy(_cached_plan(roi,key,participants))
    by_id = {t.table_id:t for t in plan.targets}
    return replace(plan,targets=[by_id[t.table_id] for t in state.tables])


def transform_discussion_plan(state,plan,strength):
    blended = _blend_targets_with_source(state,plan.targets,strength)
    # Final topology and active/parked identities are fixed before blending.
    active_state = _active_state(state,plan.active_table_ids)
    active_targets = [t for t in blended if t.table_id in plan.active_table_ids]
    try:
        if plan.topology=='pair':
            partial = _assemble_pair(active_state,active_targets,len(plan.chairs))
        else:
            partial = _assemble(active_state,active_targets,len(plan.chairs),validate=False)
        partial = replace(partial,targets=blended,active_table_ids=plan.active_table_ids,
                          parked_table_ids=plan.parked_table_ids)
        validate_discussion_chairs(state,partial)
        return partial
    except ValueError as exc:
        raise LayoutConstraintError('Discussion-Chairs passen bei dieser Teilstärke nicht; '
                                    'Topologie und Tischrollen bleiben gebunden. Für Zielprüfung 100 % verwenden.') from exc
