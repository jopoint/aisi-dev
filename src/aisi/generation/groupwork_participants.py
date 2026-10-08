"""Teilnehmergruppen, Tischcluster und kanonische Groupwork-Sitzgeometrie."""
from __future__ import annotations

from dataclasses import dataclass, replace
from copy import deepcopy
from collections import OrderedDict
from functools import lru_cache
from itertools import combinations, permutations, product
import math

from aisi.core.models import ROI, SceneState, TableState, TableTarget
from aisi.core.table_geometry import (
    circle_inside_convex_polygon, circle_intersects_convex_polygon,
    polygon_inside_roi, resolve_table_state_geometry, table_world_footprint,
    required_table_center_separation,
)
from aisi.analysis.rect_groupwork_adaptive_prototype import (
    SEAT_CLEARANCE_DEPTH_CM, PAIR_SEAM_CM, _pair_clearance_ellipse,
    _polygons_overlap_with_positive_area, singleton_end_clearance_regions,
    singleton_long_side_clearance_regions,
    solve_rect_groupwork_prototype, _singleton_options, _fit_option_to_roi,
)
from aisi.generation.adaptive_layout_v1 import ActivityParameters, LayoutConstraintError, evenly_distribute

CHAIR_RADIUS_CM = 25.0


@dataclass(frozen=True)
class ParticipantCluster:
    cluster_id: str
    group_id: str
    table_ids: tuple[str, ...]
    participants: int


@dataclass
class GroupworkPlan:
    targets: list[TableTarget]
    chairs: list[dict]
    clusters: tuple[ParticipantCluster, ...]
    group_sizes: tuple[int, ...]
    regions: dict[str, tuple]
    parked_table_ids: tuple[str, ...] = ()


def cluster_seating(state, targets, cluster, *, reserved_regions=()):
    """Regular long rows, regular ends, then dense long rows; no occupied seam seats."""
    by_id = {table.table_id: table for table in state.tables}
    members = [target for target in targets if target.table_id in cluster.table_ids]
    if len(members) not in (1, 2) or len(members) != len(cluster.table_ids):
        raise LayoutConstraintError("Ein Tischcluster benötigt einen Singleton oder ein Pair.")
    angle = math.radians(members[0].target_rot_deg % 180)
    tangent, normal = (math.cos(angle), math.sin(angle)), (-math.sin(angle), math.cos(angle))
    members.sort(key=lambda target: (target.target_x * normal[0] + target.target_y * normal[1], target.table_id))
    center = (math.fsum(target.target_x for target in members)/len(members),
              math.fsum(target.target_y for target in members)/len(members))
    geometry = resolve_table_state_geometry(by_id[members[0].table_id])
    end_capacity = 2 if len(members) == 1 else 4
    regular_capacity = 4 + end_capacity
    count = cluster.participants
    if not 1 <= count <= regular_capacity + 2:
        raise LayoutConstraintError("Clusterbelegung überschreitet die verfügbaren Sitzpositionen.")
    ends_needed = min(max(0, count - 4), end_capacity)
    long_count = count - ends_needed
    row_counts = evenly_distribute(long_count, 2)
    roi = dict(x_min=state.roi.x_min, y_min=state.roi.y_min,
               x_max=state.roi.x_max, y_max=state.roi.y_max)
    base_regions = (singleton_long_side_clearance_regions(members[0], by_id[members[0].table_id])
                    if len(members) == 1 else (_pair_clearance_ellipse(members, by_id),))
    end_regions = (singleton_end_clearance_regions(members[0], by_id[members[0].table_id])
                   if len(members) == 1 else ())
    foreign = [table_world_footprint(by_id[t.table_id],(t.target_x,t.target_y),t.target_rot_deg)
               for t in targets if t.table_id not in cluster.table_ids]

    def chair(point, table_id, kind, seat_id):
        return dict(x_cm=point[0], y_cm=point[1], radius_cm=CHAIR_RADIUS_CM,
                    table_id=table_id, group_id=cluster.group_id,
                    cluster_id=cluster.cluster_id, seat_id=seat_id, seat_kind=kind)

    rows = []
    for index, (sign, n) in enumerate(zip((-1, 1), row_counts)):
        if not n:
            continue
        owner = members[0] if sign == -1 else members[-1]
        width = resolve_table_state_geometry(by_id[owner.table_id]).nominal_width
        offsets = {1: (0.,), 2: (-width/4, width/4),
                   3: (-(width/2-CHAIR_RADIUS_CM-3), 0., width/2-CHAIR_RADIUS_CM-3)}[n]
        # A pair's ellipse narrows towards the corners. Try the canonical
        # strip midpoint first, then move inward while keeping a >25-cm gap.
        for distance in (SEAT_CLEARANCE_DEPTH_CM/2-step for step in range(5)):
            seats = [chair((owner.target_x+tangent[0]*offset+sign*normal[0]*(geometry.nominal_depth/2+distance),
                            owner.target_y+tangent[1]*offset+sign*normal[1]*(geometry.nominal_depth/2+distance)),
                           owner.table_id, 'dense_long' if n == 3 and position == 1 else 'regular_long',
                           f'{cluster.cluster_id}:long:{index}:{position}')
                     for position, offset in enumerate(offsets)]
            if all(any(circle_inside_convex_polygon((s['x_cm'],s['y_cm']), CHAIR_RADIUS_CM, region)
                       for region in base_regions) for s in seats):
                rows.extend(seats)
                break
        else:
            raise LayoutConstraintError("Die Chair-Kreise passen nicht in die Cluster-Sitzfläche.")
    end_offsets = (0.,) if len(members) == 1 else (-SEAT_CLEARANCE_DEPTH_CM/2, SEAT_CLEARANCE_DEPTH_CM/2)
    options = [(sign, offset) for sign in (-1, 1) for offset in end_offsets]
    for selected in combinations(options, ends_needed):
        regions = (*base_regions, *(end_regions[0 if sign == 1 else 1]
                    for sign in sorted({sign for sign, _ in selected}))) if end_regions else base_regions
        # end_regions are ordered along rotated strip normals: index 0 is +tangent.
        if not all(polygon_inside_roi(region, **roi) for region in regions):
            continue
        if any(_polygons_overlap_with_positive_area(region,other)
               for region in regions for other in (*foreign,*reserved_regions)):
            continue
        ends = []
        for index, (sign, offset) in enumerate(selected):
            point = (center[0]+sign*tangent[0]*(geometry.nominal_width/2+SEAT_CLEARANCE_DEPTH_CM/2)+normal[0]*offset,
                     center[1]+sign*tangent[1]*(geometry.nominal_width/2+SEAT_CLEARANCE_DEPTH_CM/2)+normal[1]*offset)
            owner = min(members, key=lambda target: (math.dist(point,(target.target_x,target.target_y)),target.table_id))
            ends.append(chair(point,owner.table_id,'regular_end',f'{cluster.cluster_id}:end:{index}'))
        seats = rows + ends
        if all(any(circle_inside_convex_polygon((s['x_cm'],s['y_cm']),CHAIR_RADIUS_CM,region)
                   for region in regions) for s in seats):
            return seats, tuple(regions)
    raise LayoutConstraintError("Die belegten Stirnseiten-Sitzflächen liegen außerhalb der ROI.")


def validate_groupwork_plan(state: SceneState, plan: GroupworkPlan):
    """Validate complete targets, parked furniture, chairs and occupied movement zones."""
    by_id = {table.table_id: table for table in state.tables}
    if len(plan.targets) != len(by_id) or {t.table_id for t in plan.targets} != set(by_id):
        raise LayoutConstraintError("Groupwork-Ziele müssen alle Tischidentitäten erhalten.")
    active = [tid for cluster in plan.clusters for tid in cluster.table_ids]
    if len(set(active)) != len(active) or set(active) & set(plan.parked_table_ids) or set(active)|set(plan.parked_table_ids) != set(by_id):
        raise LayoutConstraintError("Ungültige aktive/geparkte Groupwork-Tischzuordnung.")
    if len(plan.chairs) != sum(plan.group_sizes):
        raise LayoutConstraintError("Groupwork-Chair-Count stimmt nicht mit participants überein.")
    groups = {f'group_{i}': count for i,count in enumerate(plan.group_sizes)}
    for group_id,count in groups.items():
        if sum(c.participants for c in plan.clusters if c.group_id == group_id) != count:
            raise LayoutConstraintError("Ungültige Teilnehmergruppen-/Clusterbelegung.")
    footprints = {t.table_id:table_world_footprint(by_id[t.table_id],(t.target_x,t.target_y),t.target_rot_deg) for t in plan.targets}
    roi = dict(x_min=state.roi.x_min,y_min=state.roi.y_min,x_max=state.roi.x_max,y_max=state.roi.y_max)
    if any(not polygon_inside_roi(p,**roi) for p in footprints.values()) or any(
            _polygons_overlap_with_positive_area(a,b) for a,b in combinations(footprints.values(),2)):
        raise LayoutConstraintError("Groupwork-Tischkollision oder ROI-Verletzung.")
    for cluster in plan.clusters:
        if len(cluster.table_ids) == 2:
            members = {t.table_id:t for t in plan.targets}
            first,second = (members[tid] for tid in cluster.table_ids)
            angle = math.radians(first.target_rot_deg)
            tangent,normal = (math.cos(angle),math.sin(angle)),(-math.sin(angle),math.cos(angle))
            delta = (second.target_x-first.target_x,second.target_y-first.target_y)
            expected = required_table_center_separation(by_id[first.table_id],first.target_rot_deg,
                         by_id[second.table_id],second.target_rot_deg,normal,gap=PAIR_SEAM_CM)
            if (abs((second.target_rot_deg-first.target_rot_deg+90)%180-90)>1e-6
                or abs(delta[0]*tangent[0]+delta[1]*tangent[1])>1e-6
                or abs(abs(delta[0]*normal[0]+delta[1]*normal[1])-expected)>1e-6):
                raise LayoutConstraintError("Ein Pair muss seine gemeinsame Achse und 8-cm-Seam erhalten.")
        seats = [s for s in plan.chairs if s['cluster_id'] == cluster.cluster_id]
        if len(seats) != cluster.participants or any(s['group_id'] != cluster.group_id or s['table_id'] not in cluster.table_ids for s in seats):
            raise LayoutConstraintError("Chair gehört nicht zur vorgesehenen Gruppe/Clusterbelegung.")
        for region in plan.regions[cluster.cluster_id]:
            if not polygon_inside_roi(region,**roi) or any(
                    _polygons_overlap_with_positive_area(region,p) for tid,p in footprints.items() if tid not in cluster.table_ids):
                raise LayoutConstraintError("Blockierte Groupwork-Sitz-/Bewegungsfläche.")
        if any(not any(circle_inside_convex_polygon((s['x_cm'],s['y_cm']),s['radius_cm'],region)
                       for region in plan.regions[cluster.cluster_id]) for s in seats):
            raise LayoutConstraintError("Chair liegt nicht vollständig in seiner Cluster-Sitzfläche.")
    for first,second in combinations(plan.clusters,2):
        if any(_polygons_overlap_with_positive_area(a,b) for a in plan.regions[first.cluster_id] for b in plan.regions[second.cluster_id]):
            raise LayoutConstraintError("Groupwork-Clusterflächen überschneiden sich.")
    for s in plan.chairs:
        if any(circle_intersects_convex_polygon((s['x_cm'],s['y_cm']),s['radius_cm'],p) for p in footprints.values()):
            raise LayoutConstraintError("Groupwork-Chair kollidiert mit einem Tisch.")
    if any(math.dist((a['x_cm'],a['y_cm']),(b['x_cm'],b['y_cm'])) <= a['radius_cm']+b['radius_cm']+1e-9 for a,b in combinations(plan.chairs,2)):
        raise LayoutConstraintError("Groupwork-Chairs kollidieren.")
    if not groups_are_spatially_distinct(plan):
        raise LayoutConstraintError("Teilnehmergruppen sind räumlich nicht eindeutig zugeordnet.")


def groups_are_spatially_distinct(plan):
    """A group's cluster MST must be shorter than every intergroup center distance."""
    by_id = {t.table_id:t for t in plan.targets}
    centers = {c.cluster_id:(sum(by_id[tid].target_x for tid in c.table_ids)/len(c.table_ids),
                            sum(by_id[tid].target_y for tid in c.table_ids)/len(c.table_ids)) for c in plan.clusters}
    external = [math.dist(centers[a.cluster_id],centers[b.cluster_id])
                for a,b in combinations(plan.clusters,2) if a.group_id != b.group_id]
    if not external:
        return True
    for group_id in {c.group_id for c in plan.clusters}:
        remaining = {c.cluster_id for c in plan.clusters if c.group_id == group_id}
        connected = {min(remaining)};remaining -= connected
        while remaining:
            distance, next_id = min((math.dist(centers[a],centers[b]),b) for a in connected for b in remaining)
            if distance >= min(external)-1e-8:
                return False
            connected.add(next_id);remaining.remove(next_id)
    return True


def cluster_profiles(people, tables, lower=(1, 1)):
    """Enumerate bounded occupancy profiles; geometry decides actual feasibility."""
    if people == 0:
        yield ()
        return
    for size in (1, 2):
        capacity = 8 if size == 1 else 10
        if size > tables:
            continue
        for seats in range(1, min(people, capacity)+1):
            descriptor = (size, seats)
            if descriptor < lower:
                continue
            for tail in cluster_profiles(people-seats, tables-size, descriptor):
                yield (descriptor, *tail)


def _profile_key(profile, policy):
    dense = sum(max(0, count-(6 if size == 1 else 8)) for _,size,count in profile)
    ends = sum(min(max(0,count-4),2 if size == 1 else 4) for _,size,count in profile)
    tables = sum(size for _,size,_ in profile)
    rank = (dense,ends,tables) if policy == 'regular_seats' else (tables,dense,ends)
    return rank, max(count for _,_,count in profile), profile


def _attach_clusters(state, targets, islands, profile, sizes, bound_clusters=None):
    islands = sorted((tuple(sorted(ids)) for ids in islands))
    assignments = ((profile,) if len({(size,count) for _,size,count in profile}) == 1
                   and len(profile) == len(sizes) else sorted(set(permutations(profile))))
    if bound_clusters is not None:
        by_island = {tuple(sorted(c.table_ids)): c for c in bound_clusters}
        if set(islands) != set(by_island):
            return None
        assignments = (tuple((int(by_island[ids].group_id.split("_")[-1]), len(ids),
                              by_island[ids].participants) for ids in islands),)
    for assignment in assignments:
        if any(len(ids) != descriptor[1] for ids,descriptor in zip(islands,assignment)):
            continue
        clusters = tuple(ParticipantCluster(f'cluster_{i}',f'group_{g}',ids,count)
                         for i,(ids,(g,_,count)) in enumerate(zip(islands,assignment)))
        plan = GroupworkPlan(list(targets),[],clusters,sizes,{})
        try:
            for cluster in clusters:
                seats,regions = cluster_seating(state,targets,cluster,
                    reserved_regions=tuple(r for rs in plan.regions.values() for r in rs))
                plan.chairs.extend(seats);plan.regions[cluster.cluster_id] = regions
            validate_groupwork_plan(state,plan)
        except LayoutConstraintError:
            continue
        return plan
    return None


def _solve_profile(active_state, profile, sizes, bound_clusters=None):
    cluster_sizes = tuple(sorted(descriptor[1] for descriptor in profile))
    if len(cluster_sizes) >= 4 and all(n == 1 for n in cluster_sizes):
        plan = _repair_singleton_profile(active_state,profile,sizes,bound_clusters)
        if plan is not None:
            return plan
    if len(active_state.tables) == 1:
        for refined in (False,True):
            for option in _singleton_options(active_state.tables[0],refined=refined,expanded=True):
                fitted = _fit_option_to_roi(active_state,option)
                plan = _attach_clusters(active_state,fitted.targets,((active_state.tables[0].table_id,),),profile,sizes,bound_clusters)
                if plan is not None:
                    return plan
        return None
    def accept(candidate):
        return _attach_clusters(active_state,candidate.table_targets,candidate.groups,profile,sizes,bound_clusters) is not None
    try:
        result = solve_rect_groupwork_prototype(active_state,selection='clearance',
                    cluster_sizes=cluster_sizes,candidate_filter=accept)
    except ValueError:
        return _repair_singleton_profile(active_state,profile,sizes,bound_clusters)
    return _attach_clusters(active_state,result.table_targets,result.groups,profile,sizes,bound_clusters)


def _repair_singleton_profile(state, profile, sizes, bound_clusters=None):
    """Repair conservative envelopes derived from actual canonical seat regions."""
    from aisi.generation.layout_constraints import repair_layout_hard_constraints
    if any(n != 1 for _,n,_ in profile):
        return None
    islands = tuple((t.table_id,) for t in state.tables)
    # Local candidates need not contain the small diagonal shifts required by
    # five singleton islands. Try a continuous shared repair before rejecting.
    for rotations in (tuple(t.rot_deg for t in state.tables), (0.,)*len(state.tables), (90.,)*len(state.tables)):
        proxies=[];seeds=[]
        for table,rotation in zip(state.tables,rotations):
            origin=TableTarget(table.table_id,0.,0.,source_rot_deg=table.rot_deg,target_rot_deg=0.)
            polygons=(*singleton_long_side_clearance_regions(origin,table),
                      table_world_footprint(table,(0.,0.),0.))
            # This fallback currently covers long-side-only singleton profiles.
            # End occupancy stays in the dedicated cluster search above.
            if any(count>4 for _,_,count in profile):
                return None
            x0=min(x for p in polygons for x,y in p);x1=max(x for p in polygons for x,y in p)
            y0=min(y for p in polygons for x,y in p);y1=max(y for p in polygons for x,y in p)
            proxies.append(TableState(table.table_id,table.x,table.y,rotation,x1-x0,y1-y0,table_type=None))
            seeds.append(TableTarget(table.table_id,table.x,table.y,source_rot_deg=table.rot_deg,target_rot_deg=rotation))
        occupied_state=SceneState(state.roi,proxies,'groupwork')
        repaired=repair_layout_hard_constraints(occupied_state,seeds,max_iterations=100,
                    overlap_gap=0.,clearance_depth_factor=None)
        # Envelopes are conservative and can touch where the actual rounded
        # regions do not overlap. Only the full canonical final guard decides.
        plan=_attach_clusters(state,repaired.table_targets,islands,profile,sizes,bound_clusters)
        if plan is not None:
            return plan
    return None


def _complete_parking(state, plan):
    from aisi.app.sim_layout_rules import _compact_park_targets
    from aisi.generation.adaptive_layout_v1 import _parking_candidates
    active = {tid for cluster in plan.clusters for tid in cluster.table_ids}
    parked = sorted((table for table in state.tables if table.table_id not in active),key=lambda table:table.table_id)
    try:
        extra = _compact_park_targets(state,parked,plan.targets,_parking_candidates(None),
                  exclusion_regions=[r for regions in plan.regions.values() for r in regions])
    except ValueError:
        return None
    plan.targets.extend(extra)
    plan.parked_table_ids = tuple(table.table_id for table in parked)
    try:
        validate_groupwork_plan(state,plan)
    except LayoutConstraintError:
        return None
    return plan


def plan_participant_groupwork(state, participants, number_of_groups, *, table_policy="few_tables"):
    """Offline full-strength plan; policy explicitly resolves table-use preference."""
    if type(participants) is not int or type(number_of_groups) is not int:
        raise LayoutConstraintError("Teilnehmerzahl und Gruppenzahl müssen ganze Zahlen sein.")
    ActivityParameters(participants,number_of_groups).validate('groupwork')
    if table_policy not in ('regular_seats','few_tables'):
        raise LayoutConstraintError("Unbekannte Groupwork-Tischpräferenz.")
    if not 1 <= len(state.tables) <= 5 or any(t.table_type != 'rect' for t in state.tables):
        raise LayoutConstraintError("Teilnehmendenbasierte Groupwork-Planung benötigt ein bis fünf Rect-Tische.")
    if number_of_groups > len(state.tables):
        raise LayoutConstraintError("Es stehen weniger Tische als Teilnehmergruppen zur Verfügung.")
    if participants > 8 * len(state.tables):
        raise LayoutConstraintError("Die Anfrage überschreitet bereits die theoretische Sitzpositions-Obergrenze.")
    key = tuple((t.table_id,t.x,t.y,t.rot_deg,t.width,t.height,t.table_type)
                for t in sorted(state.tables,key=lambda t:t.table_id))
    roi = (state.roi.x_min,state.roi.y_min,state.roi.x_max,state.roi.y_max)
    plan = deepcopy(_cached_plan(roi,key,participants,number_of_groups,table_policy))
    by_id = {target.table_id:target for target in plan.targets}
    plan.targets = [by_id[table.table_id] for table in state.tables]
    parked = set(plan.parked_table_ids)
    plan.parked_table_ids = tuple(table.table_id for table in state.tables if table.table_id in parked)
    return plan


@lru_cache(maxsize=32)
def _cached_plan(roi,key,participants,number_of_groups,policy):
    state = SceneState(ROI(*roi),[TableState(*t[:6],table_type=t[6]) for t in key],'groupwork')
    sizes = evenly_distribute(participants,number_of_groups)
    profiles = set()
    for grouped in product(*(tuple(cluster_profiles(count,len(key))) for count in sizes)):
        profile = tuple((i,n,p) for i,clusters in enumerate(grouped) for n,p in clusters)
        if sum(n for _,n,_ in profile) <= len(key):
            profiles.add(profile)
    ordered = sorted(profiles,key=lambda profile:_profile_key(profile,policy))
    best = None;best_rank = None
    for profile in ordered:
        rank = _profile_key(profile,policy)[0]
        if best is not None and rank > best_rank:
            break
        required = sum(n for _,n,_ in profile)
        for active in combinations(state.tables,required):
            active_state = SceneState(state.roi,list(active),'groupwork')
            plan = _solve_profile(active_state,profile,sizes)
            if plan is None:
                continue
            plan = _complete_parking(state,plan)
            if plan is None:
                continue
            targets = {t.table_id:t for t in plan.targets}
            distances = [math.dist((t.x,t.y),(targets[t.table_id].target_x,targets[t.table_id].target_y)) for t in state.tables]
            objective = (max(distances),math.fsum(distances),
                         tuple((t.table_id,targets[t.table_id].target_x,targets[t.table_id].target_y) for t in state.tables))
            if best is None or objective < best[0]:
                best = (objective,plan);best_rank = rank
    if best is None:
        raise LayoutConstraintError("Keine gemeinsame Groupwork-Geometrie für Teilnehmergruppen, Chairs und Parktische gefunden.")
    return best[1]


_transform_cache = OrderedDict()


def transform_groupwork_plan(state, plan, strength):
    """Return independent cached copies for the OSC resend cadence."""
    key = (tuple((t.table_id,t.x,t.y,t.rot_deg,t.width,t.height,t.table_type) for t in state.tables),
           (state.roi.x_min,state.roi.y_min,state.roi.x_max,state.roi.y_max),
           tuple((t.table_id,t.target_x,t.target_y,t.target_rot_deg) for t in plan.targets),
           plan.clusters,plan.group_sizes,plan.parked_table_ids,strength)
    if key not in _transform_cache:
        _transform_cache[key] = _transform_groupwork_plan(state,plan,strength)
        if len(_transform_cache) > 32:
            _transform_cache.popitem(last=False)
    _transform_cache.move_to_end(key)
    return deepcopy(_transform_cache[key])


def _transform_groupwork_plan(state, plan, strength):
    """Blend first, then repair complete geometry with fixed table/group roles."""
    from aisi.generation.layout_synthesizer import _blend_targets_with_source
    blended = _blend_targets_with_source(state, plan.targets, strength)
    try:
        result = deepcopy(plan)
        result.targets = blended
        result.chairs = []; result.regions = {}
        for cluster in result.clusters:
            chairs, regions = cluster_seating(state, blended, cluster,
                reserved_regions=tuple(r for rs in result.regions.values() for r in rs))
            result.chairs.extend(chairs); result.regions[cluster.cluster_id] = regions
        validate_groupwork_plan(state, result)
        return result
    except LayoutConstraintError:
        pass
    poses = {t.table_id: t for t in blended}
    intermediate = SceneState(state.roi, [replace(t, x=poses[t.table_id].target_x,
        y=poses[t.table_id].target_y, rot_deg=poses[t.table_id].target_rot_deg)
        for t in state.tables], 'groupwork')
    active = {tid for c in plan.clusters for tid in c.table_ids}
    active_state = SceneState(state.roi, [t for t in intermediate.tables if t.table_id in active], 'groupwork')
    profile = tuple((int(c.group_id.split('_')[-1]),len(c.table_ids),c.participants) for c in plan.clusters)
    result = _solve_profile(active_state, profile, plan.group_sizes, plan.clusters)
    if result is not None:
        result = _complete_parking(intermediate, result)
    if result is None:
        raise LayoutConstraintError('Keine gültige Groupwork-Reparatur bei dieser Transformationsstärke; Rollen bleiben gebunden.')
    originals = {t.table_id:t for t in state.tables}
    targets = {t.table_id:replace(t,source_rot_deg=originals[t.table_id].rot_deg) for t in result.targets}
    result.targets = [targets[t.table_id] for t in state.tables]
    result.parked_table_ids = plan.parked_table_ids
    validate_groupwork_plan(state, result)
    return result
