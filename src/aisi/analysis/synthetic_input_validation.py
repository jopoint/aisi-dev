"""Offline checks of the complete Input target, using canonical footprints."""

from __future__ import annotations

import math
from itertools import combinations

from aisi.app.sim_layout_rules import _normalize_scene_for_aisi
from aisi.core.models import TableTarget
from aisi.core.table_geometry import (
    circle_inside_convex_polygon, circle_intersects_convex_polygon,
    convex_polygons_intersect, polygon_inside_roi, table_world_footprint,
)
from aisi.generation.layout_synthesizer import _rect_input_clearance_regions, _rect_input_presenter_and_axis
from aisi.input.scene_loader import build_scene_state_from_dict


def input_target_geometry(scene, output, presentation_side=None):
    state = build_scene_state_from_dict(_normalize_scene_for_aisi(scene), learning_format="input")
    targets = {table.table_id: TableTarget(table.table_id, item["x_cm"], item["y_cm"], table.rot_deg, item["rotation_deg"])
               for table, item in zip(state.tables, output.table_targets)}
    active = [table for table in state.tables if table.table_id in output.active_table_ids]
    presenter, axis = _rect_input_presenter_and_axis(active, presentation_side or output.presentation_side)
    regions = _rect_input_clearance_regions([targets[table.table_id] for table in active], active, presenter.table_id, axis)
    footprints = {table.table_id: table_world_footprint(table, (targets[table.table_id].target_x, targets[table.table_id].target_y), targets[table.table_id].target_rot_deg)
                  for table in state.tables}
    return state, targets, footprints, dict(zip((table.table_id for table in active), regions))


def validate_synthetic_input(scene, output, participants, presentation_side=None):
    """Return named violations, independently of the planner's validity claim."""
    errors = []
    raw_ids = [str(table["id"]) for table in scene["tables"]]
    active, parked = set(output.active_table_ids), set(output.parked_table_ids)
    if len(output.table_targets) != len(raw_ids) or len(set(raw_ids)) != len(raw_ids) or active & parked or active | parked != set(raw_ids):
        return ["identity/order topology"]
    expected_active = min(len(raw_ids), math.ceil(participants / 2))
    if len(active) != expected_active or len(output.chairs) != participants:
        errors.append("capacity/count")
    state, _, footprints, regions = input_target_geometry(scene, output, presentation_side)
    roi = dict(x_min=state.roi.x_min, y_min=state.roi.y_min, x_max=state.roi.x_max, y_max=state.roi.y_max)
    for table_id, polygon in footprints.items():
        if not polygon_inside_roi(polygon, **roi):
            errors.append(f"table ROI: {table_id}")
    for first, second in combinations(footprints, 2):
        if convex_polygons_intersect(footprints[first], footprints[second]):
            errors.append(f"table collision: {first}/{second}")
    for table_id, region in regions.items():
        if not polygon_inside_roi(region, **roi):
            errors.append(f"surface ROI: {table_id}")
        for other, polygon in footprints.items():
            if other != table_id and convex_polygons_intersect(region, polygon):
                errors.append(f"blocked surface: {table_id}/{other}")
    for first, second in combinations(regions, 2):
        if convex_polygons_intersect(regions[first], regions[second]):
            errors.append(f"surface collision: {first}/{second}")
    counts = {table_id: 0 for table_id in active}
    for index, chair in enumerate(output.chairs):
        center = (float(chair["x_cm"]), float(chair["y_cm"]))
        radius = float(chair["radius_cm"])
        table_id = chair["table_id"]
        if table_id not in regions:
            errors.append(f"chair identity: {index}")
            continue
        counts[table_id] += 1
        if radius != 25 or not polygon_inside_roi(((center[0] - radius, center[1] - radius), (center[0] + radius, center[1] + radius)), **roi):
            errors.append(f"chair ROI/radius: {index}")
        if not circle_inside_convex_polygon(center, radius, regions[table_id]):
            errors.append(f"chair outside seat surface: {index}")
        for other, polygon in footprints.items():
            if circle_intersects_convex_polygon(center, radius, polygon):
                errors.append(f"chair/table collision: {index}/{other}")
        for other, region in regions.items():
            if other != table_id and circle_intersects_convex_polygon(center, radius, region):
                errors.append(f"chair blocks other surface: {index}/{other}")
        for previous in output.chairs[:index]:
            if math.dist(center, (float(previous["x_cm"]), float(previous["y_cm"]))) < radius + float(previous["radius_cm"]) - 1e-7:
                errors.append(f"chair collision: {index}")
    if any(count < 1 or count > (3 if len(active) == len(raw_ids) else 2) for count in counts.values()):
        errors.append("per-table capacity")
    return errors
