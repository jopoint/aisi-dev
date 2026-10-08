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
    solve_rect_groupwork_prototype, _singleton_options, _fit_option_to_roi, _polygon_distance, _GroupOption,
)
from aisi.generation.adaptive_layout_v1 import ActivityParameters, LayoutConstraintError, evenly_distribute

CHAIR_RADIUS_CM = 25.0
PARK_ACTIVE_CLEARANCE_CM = 60.0
# Existing Study-style floor contours are 170 x 90 around physical 160 x 80.
FLOOR_CONTOUR_PADDING_CM = 5.0


def floor_contour_footprint(table, target):
    geometry = resolve_table_state_geometry(table)
    envelope = replace(table, table_type=None,
        width=geometry.nominal_width+2*FLOOR_CONTOUR_PADDING_CM,
        height=geometry.nominal_depth+2*FLOOR_CONTOUR_PADDING_CM)
    return table_world_footprint(envelope,(target.target_x,target.target_y),target.target_rot_deg)


def intergroup_floor_gap(state, plan):
    by_id = {t.table_id:t for t in state.tables}
    groups = {tid:c.group_id for c in plan.clusters for tid in c.table_ids}
    polygons = {t.table_id:floor_contour_footprint(by_id[t.table_id],t) for t in plan.targets}
    gaps = [_polygon_distance(polygons[a.table_id],polygons[b.table_id])
            for a,b in combinations(plan.targets,2)
            if a.table_id in groups and b.table_id in groups and groups[a.table_id] != groups[b.table_id]]
    return min(gaps) if gaps else 0.0


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


def validate_groupwork_plan(state: SceneState, plan: GroupworkPlan, *, check_floor_contours=True):
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
    if any(_polygon_distance(footprints[parked],footprints[tid]) < PARK_ACTIVE_CLEARANCE_CM-1e-7
           for parked in plan.parked_table_ids for tid in active):
        raise LayoutConstraintError("Geparkter Groupwork-Tisch unterschreitet 60 cm Abstand zu aktivem Tisch.")
    contours = {t.table_id:floor_contour_footprint(by_id[t.table_id],t) for t in plan.targets}
    cluster_by_table = {tid:c.cluster_id for c in plan.clusters for tid in c.table_ids}
    for a,b in combinations(plan.targets,2):
        # The existing 8-cm pair seam deliberately lies inside two 5-cm
        # visual margins. It remains a physical seam, not two social clusters.
        same_cluster = (a.table_id in cluster_by_table and
                        cluster_by_table[a.table_id] == cluster_by_table.get(b.table_id))
        if check_floor_contours and not same_cluster and _polygons_overlap_with_positive_area(contours[a.table_id],contours[b.table_id]):
            raise LayoutConstraintError("Groupwork-Bodenkonturen verschiedener Cluster überlappen.")
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
    if policy == 'group_capacity':
        # Three is the preferred singleton occupancy, not a hard capacity.
        # Larger social groups should first receive a pair when it fits.
        singleton_excess = sum(max(0,count-3) for _,size,count in profile if size == 1)
        group_totals = {g:sum(count for owner,_,count in profile if owner == g)
                        for g,_,_ in profile}
        missing_pair = sum(total > 3 and not any(owner == g and size == 2
                           for owner,size,_ in profile) for g,total in group_totals.items())
        # Keep a social group together before adding a disconnected island.
        # If parking fails, a spare table can form a pair even for <=3 people.
        extra_clusters = len(profile)-len(group_totals)
        # With equal topology/table use, give the pair to the larger group.
        pair_occupancy = sum(count for _,size,count in profile if size == 2)
        rank = (singleton_excess,missing_pair,extra_clusters,dense,tables,ends,-pair_occupancy)
    else:
        rank = (dense,ends,tables) if policy == 'regular_seats' else (tables,dense,ends)
    return rank, max(count for _,_,count in profile), profile


def _cached_cluster_seating(state, targets, cluster, reserved_regions, cache):
    """Reuse identical physical checks within one solve, retaining fresh labels."""
    if cache is None:
        return cluster_seating(state,targets,cluster,reserved_regions=reserved_regions)
    key = ((state.roi.x_min,state.roi.y_min,state.roi.x_max,state.roi.y_max),
           tuple((t.table_id,t.width,t.height,t.table_type) for t in state.tables),
           tuple((t.table_id,t.target_x,t.target_y,t.target_rot_deg) for t in targets),
           cluster.table_ids,cluster.cluster_id,cluster.participants,reserved_regions)
    if key not in cache:
        try:
            cache[key] = cluster_seating(state,targets,cluster,reserved_regions=reserved_regions)
        except LayoutConstraintError:
            cache[key] = None
        if len(cache) > 4096:
            cache.popitem(last=False)
    result = cache[key]
    cache.move_to_end(key)
    if result is None:
        raise LayoutConstraintError('Keine gültige Sitzgeometrie für diesen Kandidaten.')
    seats,regions = result
    return [dict(seat,group_id=cluster.group_id) for seat in seats],regions


def _attach_clusters(state, targets, islands, profile, sizes, bound_clusters=None, seating_cache=None):
    islands = sorted((tuple(sorted(ids)) for ids in islands))
    assignments = ((profile,) if len({(size,count) for _,size,count in profile}) == 1
                   and len(profile) == len(sizes) else sorted(set(permutations(profile))))
    if bound_clusters is not None:
        by_island = {tuple(sorted(c.table_ids)): c for c in bound_clusters}
        if set(islands) != set(by_island):
            return None
        assignments = (tuple((int(by_island[ids].group_id.split("_")[-1]), len(ids),
                              by_island[ids].participants) for ids in islands),)
    # With exactly one cluster per group, exchanging labels of equally sized
    # groups cannot change seating feasibility or spatial distinctness. Keep
    # the first (existing deterministic) assignment, avoiding duplicate checks.
    single_cluster_groups = len({g for g,_,_ in profile}) == len(profile)
    checked_seating = set()
    for assignment in assignments:
        if any(len(ids) != descriptor[1] for ids,descriptor in zip(islands,assignment)):
            continue
        seating_key = tuple((size,count) for _,size,count in assignment)
        if single_cluster_groups:
            if seating_key in checked_seating:
                continue
            checked_seating.add(seating_key)
        clusters = tuple(ParticipantCluster(f'cluster_{i}',f'group_{g}',ids,count)
                         for i,(ids,(g,_,count)) in enumerate(zip(islands,assignment)))
        plan = GroupworkPlan(list(targets),[],clusters,sizes,{})
        try:
            for cluster in clusters:
                seats,regions = _cached_cluster_seating(state,targets,cluster,
                    tuple(r for rs in plan.regions.values() for r in rs),seating_cache)
                plan.chairs.extend(seats);plan.regions[cluster.cluster_id] = regions
            validate_groupwork_plan(state,plan,check_floor_contours=False)
        except LayoutConstraintError:
            continue
        return plan
    return None


def _solve_profile(active_state, profile, sizes, bound_clusters=None, seating_cache=None, *, angle_fallback=True):
    cluster_sizes = tuple(sorted(descriptor[1] for descriptor in profile))
    if len(cluster_sizes) >= 4 and all(n == 1 for n in cluster_sizes):
        plan = _repair_singleton_profile(active_state,profile,sizes,bound_clusters)
        if plan is not None:
            return plan
    if len(active_state.tables) == 1:
        for refined in (False,True):
            for option in _singleton_options(active_state.tables[0],refined=refined,expanded=True):
                fitted = _fit_option_to_roi(active_state,option)
                plan = _attach_clusters(active_state,fitted.targets,((active_state.tables[0].table_id,),),profile,sizes,bound_clusters,seating_cache)
                if plan is not None:
                    return plan
        return None
    def accept(candidate):
        return _attach_clusters(active_state,candidate.table_targets,candidate.groups,profile,sizes,bound_clusters,seating_cache) is not None
    try:
        result = solve_rect_groupwork_prototype(active_state,selection='source_movement',
                    cluster_sizes=cluster_sizes,candidate_filter=accept,disjoint_regions=True)
    except ValueError:
        plan = _repair_singleton_profile(active_state,profile,sizes,bound_clusters)
        if plan is not None or not angle_fallback or cluster_sizes != (1,1,1,2):
            return plan
        # A spare table should join a social group's pair when edge parking
        # cannot fit. Keep source positions and relax only the search angles.
        originals = {t.table_id:t for t in active_state.tables}
        axis = min((0.,90.),key=lambda angle: sum(
            abs((angle-t.rot_deg+90.) % 180.-90.) for t in active_state.tables))
        for fraction in (.5,.75,1.):
            relaxed = SceneState(active_state.roi,[replace(t,
                rot_deg=t.rot_deg+fraction*((axis-t.rot_deg+90.) % 180.-90.))
                for t in active_state.tables],'groupwork')
            plan = _solve_profile(relaxed,profile,sizes,bound_clusters,seating_cache,
                                  angle_fallback=False)
            if plan is not None:
                for target in plan.targets:
                    target.source_rot_deg = originals[target.table_id].rot_deg
                validate_groupwork_plan(active_state,plan,check_floor_contours=False)
                return plan
        return None
    return _attach_clusters(active_state,result.table_targets,result.groups,profile,sizes,bound_clusters,seating_cache)


def _repair_singleton_profile(state, profile, sizes, bound_clusters=None):
    """Repair source-derived singleton poses using complete canonical regions."""
    if any(n != 1 for _,n,_ in profile):
        return None
    islands = tuple((t.table_id,) for t in state.tables)
    if any(count > 4 for _, _, count in profile):
        return None
    # Keep source angles whenever the existing conservative repair succeeds.
    # Otherwise relax towards ROI edge axes progressively, rather than jumping
    # all five tables to 0/90 degrees. Every trial uses canonical seat polygons.
    source_angles = tuple(t.rot_deg for t in state.tables)
    axes = sorted((0., 90.), key=lambda angle: sum(
        abs((angle-r+90.) % 180.-90.) for r in source_angles))
    variants = [source_angles]
    variants.extend(tuple(r+fraction*((axis-r+90.) % 180.-90.) for r in source_angles)
        for fraction in (.25, .5, .75, .875, .9375, 1.) for axis in axes)
    for rotations in variants:
        targets = _repair_singleton_regions(state, rotations)
        plan = _attach_clusters(state, targets, islands, profile, sizes, bound_clusters)
        if plan is None:
            continue
        try:
            validate_groupwork_plan(state,plan)
        except LayoutConstraintError:
            continue
        if rotations != source_angles:
            # Restore individual source angles as far as complete geometry fits.
            # Existing group/table roles and centers seed each bounded trial.
            for fraction in (.5, .25, .125):
                for i, source in enumerate(source_angles):
                    angles = [t.target_rot_deg for t in plan.targets]
                    angles[i] += fraction*((source-angles[i]+90.) % 180.-90.)
                    targets = _repair_singleton_regions(state, angles, plan.targets)
                    trial = _attach_clusters(state, targets, islands, profile, sizes, bound_clusters)
                    if trial is not None:
                        try:
                            validate_groupwork_plan(state,trial)
                        except LayoutConstraintError:
                            continue
                        plan = trial
        return plan
    if len(state.tables) == 5:
        # Escape a jammed source ordering without assigning fixed room slots:
        # retain one source-near-center anchor and expand the other source
        # vectors. Canonical ROI fitting and region repair determine positions.
        cx=(state.roi.x_min+state.roi.x_max)/2
        cy=(state.roi.y_min+state.roi.y_max)/2
        anchors=sorted(state.tables,key=lambda t:(math.dist((t.x,t.y),(cx,cy)),t.table_id))
        for rotations in variants:
            for anchor in anchors:
                for scale in (2.,4.):
                    seeds=[TableTarget(t.table_id,cx if t.table_id==anchor.table_id else cx+scale*(t.x-cx),
                        cy if t.table_id==anchor.table_id else cy+scale*(t.y-cy),
                        source_rot_deg=t.rot_deg,target_rot_deg=r) for t,r in zip(state.tables,rotations)]
                    targets=_repair_singleton_regions(state,rotations,seeds)
                    plan=_attach_clusters(state,targets,islands,profile,sizes,bound_clusters)
                    if plan is not None:
                        try:
                            validate_groupwork_plan(state,plan)
                        except LayoutConstraintError:
                            continue
                        return plan
    # Retain the earlier feasible last resort when rounded repair gets stuck.
    # Contour spacing can still repair this candidate after parking is attached.
    from aisi.generation.layout_constraints import repair_layout_hard_constraints
    for rotation in axes:
        proxies=[]
        for table in state.tables:
            origin=TableTarget(table.table_id,0.,0.,target_rot_deg=0.)
            points=tuple(point for polygon in singleton_long_side_clearance_regions(origin,table)
                         for point in polygon)
            proxies.append(replace(table,rot_deg=rotation,table_type=None,
                width=max(x for x,y in points)-min(x for x,y in points),
                height=max(y for x,y in points)-min(y for x,y in points)))
        seeds=[TableTarget(t.table_id,t.x,t.y,source_rot_deg=t.rot_deg,target_rot_deg=rotation)
               for t in state.tables]
        repaired=repair_layout_hard_constraints(SceneState(state.roi,proxies,'groupwork'),
            seeds,max_iterations=100,overlap_gap=0.,clearance_depth_factor=None)
        plan=_attach_clusters(state,repaired.table_targets,islands,profile,sizes,bound_clusters)
        if plan is not None:
            return plan
    return None


def _repair_singleton_regions(state, rotations, seeds=None):
    """Bounded translation repair of canonical rounded occupied polygons.

    Projection intervals include the table, contour and both long-side regions.
    Rectangular proxies only seed positions; rounded regions govern repair. The complete final guard
    still decides whether a trial is usable.
    """
    if seeds is None:
        from aisi.generation.layout_constraints import repair_layout_hard_constraints
        proxies=[]
        for table,rotation in zip(state.tables,rotations):
            origin=TableTarget(table.table_id,0.,0.,target_rot_deg=0.)
            polygons=(*singleton_long_side_clearance_regions(origin,table),
                      floor_contour_footprint(table,origin))
            points=tuple(point for polygon in polygons for point in polygon)
            proxies.append(replace(table,rot_deg=rotation,table_type=None,
                width=max(x for x,y in points)-min(x for x,y in points),
                height=max(y for x,y in points)-min(y for x,y in points)))
        initial=[TableTarget(t.table_id,t.x,t.y,source_rot_deg=t.rot_deg,target_rot_deg=r)
                 for t,r in zip(state.tables,rotations)]
        seeds=repair_layout_hard_constraints(SceneState(state.roi,proxies,'groupwork'),
            initial,max_iterations=100,overlap_gap=0.,clearance_depth_factor=None).table_targets
    targets = [TableTarget(t.table_id, seed.target_x if seeds else t.x,
        seed.target_y if seeds else t.y, source_rot_deg=t.rot_deg, target_rot_deg=r)
        for t,r,seed in zip(state.tables, rotations, seeds or state.tables)]
    shapes=[]; axes=[]; bounds=[]
    for table,rotation in zip(state.tables,rotations):
        origin=TableTarget(table.table_id,0.,0.,target_rot_deg=rotation)
        polygons=(*singleton_long_side_clearance_regions(origin,table),
                  table_world_footprint(table,(0.,0.),rotation),
                  floor_contour_footprint(table,origin))
        points=tuple(point for polygon in polygons for point in polygon)
        shapes.append(points)
        normals=set()
        for polygon in polygons:
            for a,b in zip(polygon,polygon[1:]+polygon[:1]):
                dx,dy=b[0]-a[0],b[1]-a[1]; length=math.hypot(dx,dy)
                if length>1e-9:
                    normals.add((-dy/length,dx/length))
        axes.append(normals)
        bounds.append((state.roi.x_min-min(x for x,y in points),
            state.roi.y_min-min(y for x,y in points),
            state.roi.x_max-max(x for x,y in points),
            state.roi.y_max-max(y for x,y in points)))
    projections={}
    for i,j in combinations(range(len(targets)),2):
        data=[]
        for axis in sorted(axes[i]|axes[j]):
            values=[[x*axis[0]+y*axis[1] for x,y in shapes[k]] for k in (i,j)]
            data.append((axis,min(values[0]),max(values[0]),min(values[1]),max(values[1])))
        projections[i,j]=data

    def clamp(i):
        target=targets[i]; x0,y0,x1,y1=bounds[i]
        target.target_x=min(max(target.target_x,x0),x1)
        target.target_y=min(max(target.target_y,y0),y1)

    for _ in range(200):
        for i in range(len(targets)):
            clamp(i)
        conflicts=0
        for (i,j),data in projections.items():
            a,b=targets[i],targets[j]; best=None
            for axis,amin,amax,bmin,bmax in data:
                delta=(b.target_x-a.target_x)*axis[0]+(b.target_y-a.target_y)*axis[1]
                forward=amax-bmin-delta; backward=bmax+delta-amin
                if min(forward,backward)<=1e-7:
                    break
                shift=forward if forward<backward else -backward
                if best is None or abs(shift)<abs(best[0]):
                    best=(shift,axis)
            else:
                conflicts+=1
                shift,axis=best; shift+=math.copysign(.001,shift)
                a.target_x-=axis[0]*shift/2; a.target_y-=axis[1]*shift/2
                b.target_x+=axis[0]*shift/2; b.target_y+=axis[1]*shift/2
                clamp(i); clamp(j)
        if not conflicts:
            break
    return targets


def _complete_parking(state, plan):
    from aisi.app.sim_layout_rules import _compact_park_targets
    from aisi.generation.adaptive_layout_v1 import _parking_candidates
    active = {tid for cluster in plan.clusters for tid in cluster.table_ids}
    parked = sorted((table for table in state.tables if table.table_id not in active),key=lambda table:table.table_id)
    try:
        extra = _compact_park_targets(state,parked,plan.targets,_parking_candidates(None),
                  exclusion_regions=[r for regions in plan.regions.values() for r in regions],
                  edge_aligned=True,min_active_gap_cm=PARK_ACTIVE_CLEARANCE_CM,prefer_short_movement=True)
    except ValueError:
        return None
    plan.targets.extend(extra)
    plan.parked_table_ids = tuple(table.table_id for table in parked)
    try:
        validate_groupwork_plan(state,plan,check_floor_contours=False)
    except LayoutConstraintError:
        return None
    return plan


def plan_participant_groupwork(state, participants, number_of_groups, *, table_policy="group_capacity"):
    """Offline full-strength plan; policy explicitly resolves table-use preference."""
    if type(participants) is not int or type(number_of_groups) is not int:
        raise LayoutConstraintError("Teilnehmerzahl und Gruppenzahl müssen ganze Zahlen sein.")
    ActivityParameters(participants,number_of_groups).validate('groupwork')
    if table_policy not in ('regular_seats','few_tables','group_capacity'):
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
    seating_cache = OrderedDict()
    best = None;best_rank = None
    seen_single_cluster_profiles = set()
    for profile in ordered:
        rank = _profile_key(profile,policy)[0]
        if best is not None and rank > best_rank:
            break
        if len(profile) == len(sizes):
            # Equivalent labels of equal-sized groups have identical geometry;
            # _attach_clusters already enumerates all physical assignments.
            physical_profile = tuple(sorted((size,count) for _,size,count in profile))
            if physical_profile in seen_single_cluster_profiles:
                continue
            seen_single_cluster_profiles.add(physical_profile)
        required = sum(n for _,n,_ in profile)
        for active in combinations(state.tables,required):
            active_state = SceneState(state.roi,list(active),'groupwork')
            plan = _solve_profile(active_state,profile,sizes,seating_cache=seating_cache)
            if plan is None:
                continue
            plan = _complete_parking(state,plan)
            if plan is None:
                continue
            targets = {t.table_id:t for t in plan.targets}
            objective = (*_movement_priority(state,plan.targets,plan.parked_table_ids),
                         tuple((t.table_id,targets[t.table_id].target_x,targets[t.table_id].target_y) for t in state.tables))
            if best is None or objective < best[0]:
                best = (objective,plan);best_rank = rank
    if best is None:
        raise LayoutConstraintError("Keine gemeinsame Groupwork-Geometrie für Teilnehmergruppen, Chairs und Parktische gefunden.")
    return _improve_floor_spacing(state,best[1])


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
    return _improve_floor_spacing(state,result)


def _movement_priority(state, targets, parked_ids):
    """Minimize total movement; active movement breaks equal-total ties."""
    by_id={t.table_id:t for t in state.tables}
    active=[]; parked=[]
    for target in targets:
        source=by_id[target.table_id]
        distance=math.dist((source.x,source.y),(target.target_x,target.target_y))
        (parked if target.table_id in parked_ids else active).append(distance)
    return math.fsum(active+parked),max(active,default=0.),math.fsum(active),max(parked,default=0.)


def _improve_floor_spacing(state, plan):
    """Move existing clusters rigidly; protect seating and table/group identities."""
    by_id = {t.table_id:t for t in state.tables}
    units = [c.table_ids for c in plan.clusters]

    def displacement(targets):
        return tuple(round(value,6) for value in _movement_priority(state,targets,plan.parked_table_ids))

    def score(candidate):
        cluster_by_id = {tid:c.cluster_id for c in candidate.clusters for tid in c.table_ids}
        polygons = {t.table_id:floor_contour_footprint(by_id[t.table_id],t) for t in candidate.targets}
        overlaps = sum(_polygons_overlap_with_positive_area(polygons[a.table_id],polygons[b.table_id])
            for a,b in combinations(candidate.targets,2)
            if a.table_id not in cluster_by_id or cluster_by_id[a.table_id] != cluster_by_id.get(b.table_id))
        return (overlaps, *displacement(candidate.targets),
                -round(intergroup_floor_gap(state,candidate),6))

    def rebuild(targets):
        # After contour conflicts are solved, a strictly worse source path
        # cannot win, even with more intergroup space. Keep equal paths for
        # the unchanged gap tie-break and retain full repair while conflicts remain.
        if best_score[0] == 0 and displacement(targets) > best_score[1:5]:
            return None
        candidate=GroupworkPlan(targets,[],plan.clusters,plan.group_sizes,{},plan.parked_table_ids)
        try:
            for c in candidate.clusters:
                chairs,regions=cluster_seating(state,targets,c,
                    reserved_regions=tuple(r for rs in candidate.regions.values() for r in rs))
                candidate.chairs.extend(chairs);candidate.regions[c.cluster_id]=regions
            validate_groupwork_plan(state,candidate,check_floor_contours=False)
            return candidate
        except LayoutConstraintError:
            return None

    best=deepcopy(plan);best_score=score(best)
    if best_score[0]:
        # Escape a crowded row together: displace one island and push islands
        # ahead outwards, clipping each whole island with the existing ROI fit.
        # This retains topology and derives positions from the current poses.
        for ids in units:
            anchor=next(t for t in plan.targets if t.table_id==ids[0])
            source=replace(by_id[ids[0]],x=anchor.target_x,y=anchor.target_y,rot_deg=anchor.target_rot_deg)
            for option in _singleton_options(source,refined=True,expanded=True):
                dx=option.targets[0].target_x-anchor.target_x;dy=option.targets[0].target_y-anchor.target_y
                distance=math.hypot(dx,dy)
                if distance<1e-9:continue
                translated=[]
                for island in units:
                    members=[t for t in plan.targets if t.table_id in island]
                    cx=sum(t.target_x for t in members)/len(members);cy=sum(t.target_y for t in members)/len(members)
                    mx,my=(dx,dy) if island==ids else (0.,0.)
                    if island!=ids and (cx-anchor.target_x)*dx+(cy-anchor.target_y)*dy>1e-8:
                        side=1 if (cx-anchor.target_x)*(-dy)+(cy-anchor.target_y)*dx>=0 else -1
                        mx=3*(dx-side*dy);my=3*(dy+side*dx)
                    moved=tuple(replace(t,target_x=t.target_x+mx,target_y=t.target_y+my) for t in members)
                    translated.extend(_fit_option_to_roi(state,_GroupOption(moved,tuple(island),None,True)).targets)
                targets_by_id={t.table_id:t for t in translated}
                targets_by_id.update((t.table_id,t) for t in plan.targets if t.table_id in plan.parked_table_ids)
                candidate=rebuild([targets_by_id[t.table_id] for t in plan.targets])
                if candidate is not None and score(candidate)<best_score:
                    best=candidate;best_score=score(candidate)
    # Reuse existing source-relative translation candidates at decreasing
    # scales. No new fixed room slots or table permutation are introduced.
    for scale in (1.,.5,.25,.125):
        for _ in range(2):
            changed=False
            for ids in units:
                anchor=next(t for t in best.targets if t.table_id==ids[0])
                source=replace(by_id[ids[0]],x=anchor.target_x,y=anchor.target_y,rot_deg=anchor.target_rot_deg)
                for option in _singleton_options(source,refined=True,expanded=True):
                    delta=(scale*(option.targets[0].target_x-anchor.target_x),
                           scale*(option.targets[0].target_y-anchor.target_y))
                    if abs(delta[0])+abs(delta[1])<1e-9:continue
                    targets=[replace(t,target_x=t.target_x+delta[0],target_y=t.target_y+delta[1])
                             if t.table_id in ids else t for t in best.targets]
                    candidate=rebuild(targets)
                    if candidate is not None and score(candidate)<best_score:
                        best=candidate;best_score=score(candidate);changed=True
            if not changed:break
    validate_groupwork_plan(state,best)
    return best
