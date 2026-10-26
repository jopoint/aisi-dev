"""Compute once on explicit activation; freeze targets and chairs together."""
from dataclasses import dataclass
import copy
import math

from td_builders.motion_design import Pose


@dataclass(frozen=True)
class MotionProposal:
    targets: tuple
    chairs: tuple
    show_chairs: bool
    learning_format: str


def generate_proposal(tables, settings, generator=None):
    """Use the existing planner in scene order, without a silent fallback."""
    from aisi.app.sim_room_editor import scene_payload
    from aisi.core.table_geometry import (
        world_footprint, polygon_inside_roi, convex_polygons_intersect,
    )
    if generator is None:
        from aisi.app.sim_layout_rules import (
            compute_synthetic_layout, _compute_with_aisi_pipeline, SyntheticLayoutOutput,
        )
        if settings.get('adaptive_layout_preview') is True:
            generator = compute_synthetic_layout
        else:
            # The legacy compute_target_layout wrapper catches planner errors
            # and falls back. Explicit activation must report them instead.
            def generator(scene, fmt, strength, activity_parameters):
                return SyntheticLayoutOutput(_compute_with_aisi_pipeline(scene,fmt,strength),[])
    tables = copy.deepcopy(tables)
    ids = [t['id'] for t in tables]
    if (not 1 <= len(ids) <= 5 or len(set(ids)) != len(ids)
            or any(not isinstance(i, str) or not i.strip() for i in ids)
            or any(t['type'] != 'rect' for t in tables)):
        raise ValueError('Ein Vorschlag benötigt 1–5 eindeutig identifizierte Rect-Tische.')
    for t in tables:
        if not all(math.isfinite(float(t[k])) for k in ('x_cm','y_cm','rotation_deg')):
            raise ValueError('Ungültige Istpose.')
    fmt = settings.get('learning_format')
    strength = float(settings.get('transformation_strength', 1.0))
    if fmt not in ('input','groupwork','discussion') or not math.isfinite(strength) or not 0 <= strength <= 1:
        raise ValueError('Ungültiges Lernformat oder ungültige Umbauintensität.')
    # Respect the existing opt-in and all participant/presentation settings.
    layout = generator(scene_payload(tables, [], []), fmt, strength,
                       activity_parameters=copy.deepcopy(settings))
    if len(layout.table_targets) != len(ids):
        raise ValueError('Der Generator muss alle Tischziele in Scene Order liefern.')
    targets = tuple((identity, Pose(*(float(t[k]) for k in ('x_cm','y_cm','rotation_deg'))))
                    for identity,t in zip(ids,layout.table_targets))
    if any(not all(math.isfinite(v) for v in pose) for _,pose in targets):
        raise ValueError('Ungültige Zielpose.')
    polygons = [world_footprint('rect', *pose) for _,pose in targets]
    if any(not polygon_inside_roi(p) for p in polygons) or any(
            convex_polygons_intersect(a,b) for i,a in enumerate(polygons) for b in polygons[i+1:]):
        raise ValueError('Zielvorschlag verletzt ROI oder Tisch-Kollisionsfreiheit.')
    chairs = tuple((float(c['x_cm']), float(c['y_cm']), float(c['radius_cm']), str(c['table_id']))
                   for c in layout.chairs)
    if len(chairs) > 15:
        raise ValueError('Mehr als 15 Stuhlmarker sind nicht unterstützt.')
    for x,y,r,identity in chairs:
        if (identity not in ids or not all(math.isfinite(v) for v in (x,y,r)) or r <= 0
                or not r <= x <= 500-r or not r <= y <= 500-r):
            raise ValueError('Ungültige Stuhlmarker im Vorschlag.')
    # Seating/contact semantics remain in the canonical format planners.
    # Discussion chairs may intentionally touch their own table contour.
    return MotionProposal(targets, chairs, settings.get('show_chairs', True) is True, fmt)
