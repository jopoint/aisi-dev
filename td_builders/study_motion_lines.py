"""Build isolated Study Source-to-Target motion geometries for TouchDesigner.

This is a helper for the manual, protected TouchDesigner project.  It creates
only two Geometry COMPs and one local Text DAT below
``comp_study_visualization``; it never rebuilds or edits shared rendering,
masking, calibration, or projector operators.
"""

from __future__ import annotations

import math
from typing import Final


TD_UNITS_PER_CM: Final = 0.0052
RECT_WIDTH_TD: Final = 160.0 * TD_UNITS_PER_CM
RECT_DEPTH_TD: Final = 80.0 * TD_UNITS_PER_CM
TABLETOP_INNER_WIDTH_TD: Final = 150.0 * TD_UNITS_PER_CM
TABLETOP_INNER_DEPTH_TD: Final = 70.0 * TD_UNITS_PER_CM
LINE_THICKNESS_TD: Final = 0.012
MIN_VISIBLE_LENGTH_TD: Final = 0.002
ARROW_HEAD_LENGTH_TD: Final = 0.075
ARRIVAL_TRANSLATION_TOLERANCE_CM: Final = 8.0
ARRIVAL_ROTATION_TOLERANCE_DEG: Final = 5.0
ARRIVAL_TRANSLATION_TOLERANCE_TD: Final = ARRIVAL_TRANSLATION_TOLERANCE_CM * TD_UNITS_PER_CM


def rect_motion_segments(
    source_x_td: float,
    source_y_td: float,
    source_rot_deg: float,
    target_x_td: float,
    target_y_td: float,
    target_rot_deg: float,
) -> dict[str, float]:
    """Return edge-to-edge and centre-to-edge segments for a rotated Rect.

    All values are in TouchDesigner world units/degrees.  The floor line spans
    the open space from the source boundary towards the target to the target
    boundary towards the source.  The tabletop cue points centre-to-centre and
    stops at whichever comes first: the target centre or the source's 150 x
    70 cm inner-tabletop contour.  A short move therefore has a tabletop cue
    but no artificial negative/zero-length floor line.
    """

    dx = target_x_td - source_x_td
    dy = target_y_td - source_y_td
    center_distance = math.hypot(dx, dy)
    rotation_delta_deg = _rect_rotation_delta_deg(source_rot_deg, target_rot_deg)
    arrived = (
        center_distance <= ARRIVAL_TRANSLATION_TOLERANCE_TD
        and rotation_delta_deg <= ARRIVAL_ROTATION_TOLERANCE_DEG
    )
    overlap = _rects_overlap(
        source_x_td,
        source_y_td,
        source_rot_deg,
        target_x_td,
        target_y_td,
        target_rot_deg,
    )
    if arrived or center_distance <= MIN_VISIBLE_LENGTH_TD:
        return {
            "floor_start_x": source_x_td,
            "floor_start_y": source_y_td,
            "floor_length": 0.0,
            "floor_visible": 0.0,
            "tabletop_start_x": source_x_td,
            "tabletop_start_y": source_y_td,
            "tabletop_length": 0.0,
            "tabletop_visible": 0.0,
            "floor_arrow_visible": 0.0,
            "tabletop_arrow_visible": 0.0,
            "floor_arrow_head_length": 0.0,
            "tabletop_arrow_head_length": 0.0,
            "floor_arrow_tip_x": source_x_td,
            "floor_arrow_tip_y": source_y_td,
            "tabletop_arrow_tip_x": source_x_td,
            "tabletop_arrow_tip_y": source_y_td,
            "overlap": float(overlap),
            "arrived": float(arrived),
            "floor_angle_deg": 0.0,
            "tabletop_angle_deg": 0.0,
            "tabletop_local_angle_deg": 0.0,
            "tabletop_comp_tx": source_x_td,
            "tabletop_comp_ty": source_y_td,
            "tabletop_comp_rotation_deg": source_rot_deg,
            "angle_deg": 0.0,
        }

    floor_direction_x = dx / center_distance
    floor_direction_y = dy / center_distance
    source_radius = _rect_ray_distance(floor_direction_x, floor_direction_y, source_rot_deg)
    target_radius = _rect_ray_distance(-floor_direction_x, -floor_direction_y, target_rot_deg)
    floor_length = 0.0 if overlap else max(center_distance - source_radius - target_radius, 0.0)
    floor_visible = float(not overlap and floor_length > MIN_VISIBLE_LENGTH_TD)

    # Keep the overlap/tabletop direction self-contained: it is always the
    # freshly normalized Source-centre -> Target-centre vector, never a floor
    # edge vector or a support-derived direction.
    tabletop_direction_x = dx / center_distance
    tabletop_direction_y = dy / center_distance
    source_rotation_rad = math.radians(source_rot_deg)
    tabletop_local_direction_x = (
        math.cos(source_rotation_rad) * tabletop_direction_x
        + math.sin(source_rotation_rad) * tabletop_direction_y
    )
    tabletop_local_direction_y = (
        -math.sin(source_rotation_rad) * tabletop_direction_x
        + math.cos(source_rotation_rad) * tabletop_direction_y
    )
    tabletop_inner_radius = _rect_ray_distance(
        tabletop_local_direction_x,
        tabletop_local_direction_y,
        0.0,
        width_td=TABLETOP_INNER_WIDTH_TD,
        depth_td=TABLETOP_INNER_DEPTH_TD,
    )
    tabletop_visible = 1.0
    # The tabletop cue always points Source-centre -> Target-centre direction.
    # In DUAL_SURFACE this makes motion visibly continue over the source edge;
    # FLOOR_ONLY does not render this Geometry COMP at all.
    floor_arrow_visible = floor_visible
    tabletop_arrow_visible = tabletop_visible
    floor_end_x = source_x_td + floor_direction_x * (source_radius + floor_length)
    floor_end_y = source_y_td + floor_direction_y * (source_radius + floor_length)
    # Stop at the target centre when it is already inside the visible inner
    # contour; otherwise stop at the inner-contour support in that direction.
    tabletop_length = min(center_distance, tabletop_inner_radius)
    tabletop_end_x = source_x_td + tabletop_direction_x * tabletop_length
    tabletop_end_y = source_y_td + tabletop_direction_y * tabletop_length

    return {
        "floor_start_x": source_x_td + floor_direction_x * source_radius,
        "floor_start_y": source_y_td + floor_direction_y * source_radius,
        "floor_length": floor_length,
        "floor_visible": floor_visible,
        "tabletop_start_x": source_x_td,
        "tabletop_start_y": source_y_td,
        "tabletop_length": tabletop_length,
        "tabletop_visible": tabletop_visible,
        "floor_arrow_visible": floor_arrow_visible,
        "tabletop_arrow_visible": tabletop_arrow_visible,
        "floor_arrow_head_length": min(ARROW_HEAD_LENGTH_TD, floor_length / 2.0),
        "tabletop_arrow_head_length": min(
            ARROW_HEAD_LENGTH_TD, tabletop_length / 2.0
        ),
        "floor_arrow_tip_x": floor_end_x,
        "floor_arrow_tip_y": floor_end_y,
        "tabletop_arrow_tip_x": tabletop_end_x,
        "tabletop_arrow_tip_y": tabletop_end_y,
        "overlap": float(overlap),
        "arrived": 0.0,
        "floor_angle_deg": math.degrees(math.atan2(floor_direction_y, floor_direction_x)),
        "tabletop_angle_deg": math.degrees(math.atan2(tabletop_direction_y, tabletop_direction_x)),
        "tabletop_local_angle_deg": math.degrees(
            math.atan2(tabletop_local_direction_y, tabletop_local_direction_x)
        ),
        "tabletop_comp_tx": source_x_td,
        "tabletop_comp_ty": source_y_td,
        "tabletop_comp_rotation_deg": source_rot_deg,
        # Compatibility field for existing callers; each Geometry COMP now
        # consumes its own segment angle above.
        "angle_deg": math.degrees(math.atan2(floor_direction_y, floor_direction_x)),
    }


def _rect_ray_distance(
    unit_x: float,
    unit_y: float,
    rotation_deg: float,
    *,
    width_td: float = RECT_WIDTH_TD,
    depth_td: float = RECT_DEPTH_TD,
) -> float:
    """Return centre-to-boundary distance along a direction for a rotated Rect."""

    rotation_rad = math.radians(rotation_deg)
    local_x = math.cos(rotation_rad) * unit_x + math.sin(rotation_rad) * unit_y
    local_y = -math.sin(rotation_rad) * unit_x + math.cos(rotation_rad) * unit_y
    half_width = width_td / 2.0
    half_depth = depth_td / 2.0
    candidates = []
    if abs(local_x) > 1e-12:
        candidates.append(half_width / abs(local_x))
    if abs(local_y) > 1e-12:
        candidates.append(half_depth / abs(local_y))
    return min(candidates)


def _rect_rotation_delta_deg(source_rot_deg: float, target_rot_deg: float) -> float:
    """Return the smallest Rect-orientation difference (Rect is pi-periodic)."""

    return abs((target_rot_deg - source_rot_deg + 90.0) % 180.0 - 90.0)


def _rects_overlap(
    source_x_td: float,
    source_y_td: float,
    source_rot_deg: float,
    target_x_td: float,
    target_y_td: float,
    target_rot_deg: float,
) -> bool:
    """Return whether rotated Rects overlap or touch, using SAT."""

    first = _rect_corners(source_x_td, source_y_td, source_rot_deg)
    second = _rect_corners(target_x_td, target_y_td, target_rot_deg)
    for polygon in (first, second):
        for index, point in enumerate(polygon):
            next_point = polygon[(index + 1) % len(polygon)]
            axis_x = -(next_point[1] - point[1])
            axis_y = next_point[0] - point[0]
            axis_length = math.hypot(axis_x, axis_y)
            axis_x /= axis_length
            axis_y /= axis_length
            first_projection = [x * axis_x + y * axis_y for x, y in first]
            second_projection = [x * axis_x + y * axis_y for x, y in second]
            if max(first_projection) < min(second_projection) - 1e-12:
                return False
            if max(second_projection) < min(first_projection) - 1e-12:
                return False
    return True


def _rect_corners(center_x: float, center_y: float, rotation_deg: float) -> tuple[tuple[float, float], ...]:
    """Return four clockwise world corners for the local 160 x 80 cm Rect."""

    half_width = RECT_WIDTH_TD / 2.0
    half_depth = RECT_DEPTH_TD / 2.0
    rotation_rad = math.radians(rotation_deg)
    cosine = math.cos(rotation_rad)
    sine = math.sin(rotation_rad)
    return tuple(
        (center_x + cosine * local_x - sine * local_y, center_y + sine * local_x + cosine * local_y)
        for local_x, local_y in (
            (-half_width, -half_depth),
            (half_width, -half_depth),
            (half_width, half_depth),
            (-half_width, half_depth),
        )
    )


# The active TD parameter expressions call this self-contained module through
# Text DAT.module, so it remains valid without a Python import path in TD.
MOTION_MATH_DAT_SOURCE = '''import math

RECT_WIDTH_TD = 0.832
RECT_DEPTH_TD = 0.416
TABLETOP_INNER_WIDTH_TD = 0.780
TABLETOP_INNER_DEPTH_TD = 0.364
MIN_VISIBLE_LENGTH_TD = 0.002
ARROW_HEAD_LENGTH_TD = 0.075
ARRIVAL_TRANSLATION_TOLERANCE_TD = 0.0416
ARRIVAL_ROTATION_TOLERANCE_DEG = 5.0

def _rect_ray_distance(unit_x, unit_y, rotation_deg, width_td=RECT_WIDTH_TD, depth_td=RECT_DEPTH_TD):
    rotation_rad = math.radians(rotation_deg)
    local_x = math.cos(rotation_rad) * unit_x + math.sin(rotation_rad) * unit_y
    local_y = -math.sin(rotation_rad) * unit_x + math.cos(rotation_rad) * unit_y
    candidates = []
    if abs(local_x) > 1e-12:
        candidates.append((width_td / 2.0) / abs(local_x))
    if abs(local_y) > 1e-12:
        candidates.append((depth_td / 2.0) / abs(local_y))
    return min(candidates)

def _rect_rotation_delta_deg(source_rot_deg, target_rot_deg):
    return abs((target_rot_deg - source_rot_deg + 90.0) % 180.0 - 90.0)

def _rect_corners(center_x, center_y, rotation_deg):
    half_width = RECT_WIDTH_TD / 2.0
    half_depth = RECT_DEPTH_TD / 2.0
    rotation_rad = math.radians(rotation_deg)
    cosine = math.cos(rotation_rad)
    sine = math.sin(rotation_rad)
    return tuple(
        (center_x + cosine * local_x - sine * local_y, center_y + sine * local_x + cosine * local_y)
        for local_x, local_y in ((-half_width, -half_depth), (half_width, -half_depth),
                                 (half_width, half_depth), (-half_width, half_depth))
    )

def _rects_overlap(source_x_td, source_y_td, source_rot_deg, target_x_td, target_y_td, target_rot_deg):
    first = _rect_corners(source_x_td, source_y_td, source_rot_deg)
    second = _rect_corners(target_x_td, target_y_td, target_rot_deg)
    for polygon in (first, second):
        for index, point in enumerate(polygon):
            next_point = polygon[(index + 1) % len(polygon)]
            axis_x = -(next_point[1] - point[1])
            axis_y = next_point[0] - point[0]
            axis_length = math.hypot(axis_x, axis_y)
            axis_x /= axis_length
            axis_y /= axis_length
            first_projection = [x * axis_x + y * axis_y for x, y in first]
            second_projection = [x * axis_x + y * axis_y for x, y in second]
            if max(first_projection) < min(second_projection) - 1e-12:
                return False
            if max(second_projection) < min(first_projection) - 1e-12:
                return False
    return True

def rect_motion_segments(source_x_td, source_y_td, source_rot_deg, target_x_td, target_y_td, target_rot_deg):
    dx = target_x_td - source_x_td
    dy = target_y_td - source_y_td
    center_distance = math.hypot(dx, dy)
    rotation_delta_deg = _rect_rotation_delta_deg(source_rot_deg, target_rot_deg)
    arrived = (center_distance <= ARRIVAL_TRANSLATION_TOLERANCE_TD and
               rotation_delta_deg <= ARRIVAL_ROTATION_TOLERANCE_DEG)
    overlap = _rects_overlap(source_x_td, source_y_td, source_rot_deg,
                             target_x_td, target_y_td, target_rot_deg)
    if arrived or center_distance <= MIN_VISIBLE_LENGTH_TD:
        return {
            'floor_start_x': source_x_td, 'floor_start_y': source_y_td,
            'floor_length': 0.0, 'floor_visible': 0.0,
            'tabletop_start_x': source_x_td, 'tabletop_start_y': source_y_td,
            'tabletop_length': 0.0, 'tabletop_visible': 0.0, 'angle_deg': 0.0,
            'floor_arrow_visible': 0.0, 'tabletop_arrow_visible': 0.0,
            'floor_arrow_head_length': 0.0, 'tabletop_arrow_head_length': 0.0,
            'floor_arrow_tip_x': source_x_td, 'floor_arrow_tip_y': source_y_td,
            'tabletop_arrow_tip_x': source_x_td, 'tabletop_arrow_tip_y': source_y_td,
            'overlap': float(overlap), 'arrived': float(arrived),
            'floor_angle_deg': 0.0, 'tabletop_angle_deg': 0.0,
            'tabletop_local_angle_deg': 0.0,
            'tabletop_comp_tx': source_x_td, 'tabletop_comp_ty': source_y_td,
            'tabletop_comp_rotation_deg': source_rot_deg,
        }
    floor_direction_x = dx / center_distance
    floor_direction_y = dy / center_distance
    source_radius = _rect_ray_distance(floor_direction_x, floor_direction_y, source_rot_deg)
    target_radius = _rect_ray_distance(-floor_direction_x, -floor_direction_y, target_rot_deg)
    floor_length = 0.0 if overlap else max(center_distance - source_radius - target_radius, 0.0)
    floor_visible = float(not overlap and floor_length > MIN_VISIBLE_LENGTH_TD)
    tabletop_direction_x = dx / center_distance
    tabletop_direction_y = dy / center_distance
    source_rotation_rad = math.radians(source_rot_deg)
    tabletop_local_direction_x = (math.cos(source_rotation_rad) * tabletop_direction_x +
                                  math.sin(source_rotation_rad) * tabletop_direction_y)
    tabletop_local_direction_y = (-math.sin(source_rotation_rad) * tabletop_direction_x +
                                  math.cos(source_rotation_rad) * tabletop_direction_y)
    tabletop_inner_radius = _rect_ray_distance(
        tabletop_local_direction_x, tabletop_local_direction_y, 0.0,
        TABLETOP_INNER_WIDTH_TD, TABLETOP_INNER_DEPTH_TD)
    tabletop_visible = 1.0
    floor_arrow_visible = floor_visible
    tabletop_arrow_visible = tabletop_visible
    floor_end_x = source_x_td + floor_direction_x * (source_radius + floor_length)
    floor_end_y = source_y_td + floor_direction_y * (source_radius + floor_length)
    tabletop_length = min(center_distance, tabletop_inner_radius)
    tabletop_end_x = source_x_td + tabletop_direction_x * tabletop_length
    tabletop_end_y = source_y_td + tabletop_direction_y * tabletop_length
    return {
        'floor_start_x': source_x_td + floor_direction_x * source_radius,
        'floor_start_y': source_y_td + floor_direction_y * source_radius,
        'floor_length': floor_length,
        'floor_visible': floor_visible,
        'tabletop_start_x': source_x_td, 'tabletop_start_y': source_y_td,
        'tabletop_length': tabletop_length, 'tabletop_visible': tabletop_visible,
        'floor_arrow_visible': floor_arrow_visible,
        'tabletop_arrow_visible': tabletop_arrow_visible,
        'floor_arrow_head_length': min(ARROW_HEAD_LENGTH_TD, floor_length / 2.0),
        'tabletop_arrow_head_length': min(ARROW_HEAD_LENGTH_TD, tabletop_length / 2.0),
        'floor_arrow_tip_x': floor_end_x, 'floor_arrow_tip_y': floor_end_y,
        'tabletop_arrow_tip_x': tabletop_end_x, 'tabletop_arrow_tip_y': tabletop_end_y,
        'overlap': float(overlap), 'arrived': 0.0,
        'floor_angle_deg': math.degrees(math.atan2(floor_direction_y, floor_direction_x)),
        'tabletop_angle_deg': math.degrees(math.atan2(tabletop_direction_y, tabletop_direction_x)),
        'tabletop_local_angle_deg': math.degrees(math.atan2(tabletop_local_direction_y, tabletop_local_direction_x)),
        'tabletop_comp_tx': source_x_td, 'tabletop_comp_ty': source_y_td,
        'tabletop_comp_rotation_deg': source_rot_deg,
        'angle_deg': math.degrees(math.atan2(floor_direction_y, floor_direction_x)),
    }
'''


def _motion_expr(math_dat_path: str, source_geo_path: str, target_geo_path: str, key: str) -> str:
    """Build a safe TD expression retrieving one dynamic motion value."""

    return (
        "(lambda m, s, t: m.module.rect_motion_segments("
        "s.par.tx.eval(), s.par.ty.eval(), s.par.rz.eval(), "
        "t.par.tx.eval(), t.par.ty.eval(), t.par.rz.eval())[%r] "
        "if m is not None and s is not None and t is not None else 0.0)"
        "(op(%r), op(%r), op(%r))" % (key, math_dat_path, source_geo_path, target_geo_path)
    )


def _active_study_visibility_expression(osc_path: str) -> str:
    """Return a direct TD dependency which is one only in STUDY/ACTIVE."""

    return (
        "(lambda raw: float(raw is not None and raw['study_mode'] is not None "
        "and raw['study_mode'].eval() == 1 and raw['study_phase'] is not None "
        "and raw['study_phase'].eval() == 2))(op(%r))" % osc_path
    )


def _create_motion_line_geo(
    parent,
    name: str,
    *,
    math_dat_path: str,
    source_geo_path: str,
    target_geo_path: str,
    segment_prefix: str,
    material_path: str | None,
    study_state_osc_path: str,
):
    """Create one dynamic line Geometry COMP; TouchDesigner-only."""

    geo = parent.create(geometryCOMP, name)
    line = geo.create(rectangleSOP, "line_bar")
    line_xform = geo.create(transformSOP, "line_center")
    line_xform.inputConnectors[0].connect(line)
    merge = geo.create(mergeSOP, "merge_line")
    merge.inputConnectors[0].connect(line_xform)

    length_expr = _motion_expr(math_dat_path, source_geo_path, target_geo_path, f"{segment_prefix}_length")
    line.par.sizex.expr = length_expr
    line.par.sizey = LINE_THICKNESS_TD
    line_xform.par.tx.expr = f"({length_expr}) / 2.0"
    if segment_prefix == "tabletop":
        # Source-attached local path: the COMP applies source rotation once;
        # the shaft and arrow use the corresponding local direction angle.
        geo.par.tx.expr = _motion_expr(math_dat_path, source_geo_path, target_geo_path, "tabletop_comp_tx")
        geo.par.ty.expr = _motion_expr(math_dat_path, source_geo_path, target_geo_path, "tabletop_comp_ty")
        geo.par.rz.expr = _motion_expr(
            math_dat_path, source_geo_path, target_geo_path, "tabletop_comp_rotation_deg"
        )
    else:
        geo.par.tx.expr = _motion_expr(math_dat_path, source_geo_path, target_geo_path, f"{segment_prefix}_start_x")
        geo.par.ty.expr = _motion_expr(math_dat_path, source_geo_path, target_geo_path, f"{segment_prefix}_start_y")
        geo.par.rz.expr = _motion_expr(
            math_dat_path, source_geo_path, target_geo_path, f"{segment_prefix}_angle_deg"
        )
    geo.par.sx.expr = (
        f"({_motion_expr(math_dat_path, source_geo_path, target_geo_path, f'{segment_prefix}_visible')}) "
        f"* ({_active_study_visibility_expression(study_state_osc_path)})"
    )
    geo.par.tz = 0.03

    arrow_length_expr = _motion_expr(
        math_dat_path, source_geo_path, target_geo_path, f"{segment_prefix}_arrow_head_length"
    )
    arrow_visible_expr = _motion_expr(
        math_dat_path, source_geo_path, target_geo_path, f"{segment_prefix}_arrow_visible"
    )
    # Two restrained 35-degree bars form a V whose tip is exactly at the
    # segment end. The enclosing Geometry COMP supplies the Source→Target
    # direction, so no rotation-specific arrow path is needed.
    head_angle_deg = 35.0
    head_projection_factor = math.cos(math.radians(head_angle_deg))
    head_offset_factor = math.sin(math.radians(head_angle_deg)) / 2.0
    for merge_index, (suffix, y_sign, head_rotation) in enumerate((
        ("upper", -1.0, head_angle_deg),
        ("lower", 1.0, -head_angle_deg),
    ), start=1):
        arrow_bar = geo.create(rectangleSOP, f"arrow_{suffix}_bar")
        arrow_xform = geo.create(transformSOP, f"arrow_{suffix}_center")
        arrow_xform.inputConnectors[0].connect(arrow_bar)
        arrow_bar.par.sizex.expr = arrow_length_expr
        arrow_bar.par.sizey = LINE_THICKNESS_TD
        arrow_xform.par.tx.expr = (
            f"({length_expr}) - ({arrow_length_expr}) * {head_projection_factor / 2.0}"
        )
        arrow_xform.par.ty.expr = f"({arrow_length_expr}) * {y_sign * head_offset_factor}"
        arrow_xform.par.rz = head_rotation
        arrow_xform.par.sx.expr = arrow_visible_expr
        arrow_bar.display = False
        arrow_bar.render = False
        arrow_xform.display = False
        arrow_xform.render = False
        merge.inputConnectors[merge_index].connect(arrow_xform)

    line.display = False
    line.render = False
    line_xform.display = False
    line_xform.render = False
    if segment_prefix == "tabletop":
        # Rotate the complete local cue, including both arrowhead bars, before
        # the source-attached Geometry COMP applies its world transform.
        local_direction = geo.create(transformSOP, "source_local_direction")
        local_direction.inputConnectors[0].connect(merge)
        local_direction.par.rz.expr = _motion_expr(
            math_dat_path, source_geo_path, target_geo_path, "tabletop_local_angle_deg"
        )
        merge.display = False
        merge.render = False
        local_direction.display = True
        local_direction.render = True
    else:
        merge.display = True
        merge.render = True
    geo.display = True
    geo.render = True
    if material_path is not None and hasattr(geo.par, "material"):
        geo.par.material = material_path
    return geo


def create_study_motion_line_geos(
    study_component_path: str = "/project1/comp_study_visualization",
    *,
    source_geometry_name: str = "rect_floor_outer_geo",
    target_geometry_name: str = "rect_target_floor_geo",
    floor_geometry_name: str = "rect_motion_line_floor_geo",
    tabletop_geometry_name: str = "rect_motion_line_tabletop_geo",
    math_dat_name: str = "study_motion_math",
    material_path: str | None = None,
    study_state_osc_path: str = "/project1/comp_io/null_osc_raw",
):
    """Create and return ``(floor_geo, tabletop_geo)`` under the Study COMP.

    The source and target paths intentionally reference the already-working
    Study source and target Geometry COMPs, retaining their live OSC poses and
    their existing coordinate/sign conventions.  Existing operators are never
    replaced.
    """

    parent = op(study_component_path)
    if parent is None:
        raise ValueError(f"Study component not found: {study_component_path}")
    required = (source_geometry_name, target_geometry_name)
    missing = [name for name in required if parent.op(name) is None]
    if missing:
        raise ValueError(f"Missing required Study geometry: {', '.join(missing)}")
    created_names = (floor_geometry_name, tabletop_geometry_name, math_dat_name)
    existing = [name for name in created_names if parent.op(name) is not None]
    if existing:
        raise ValueError(f"Refusing to replace existing operator(s): {', '.join(existing)}")

    math_dat = parent.create(textDAT, math_dat_name)
    math_dat.text = MOTION_MATH_DAT_SOURCE
    source_geo_path = f"{parent.path}/{source_geometry_name}"
    target_geo_path = f"{parent.path}/{target_geometry_name}"
    floor_geo = _create_motion_line_geo(
        parent,
        floor_geometry_name,
        math_dat_path=math_dat.path,
        source_geo_path=source_geo_path,
        target_geo_path=target_geo_path,
        segment_prefix="floor",
        material_path=material_path,
        study_state_osc_path=study_state_osc_path,
    )
    tabletop_geo = _create_motion_line_geo(
        parent,
        tabletop_geometry_name,
        math_dat_path=math_dat.path,
        source_geo_path=source_geo_path,
        target_geo_path=target_geo_path,
        segment_prefix="tabletop",
        material_path=material_path,
        study_state_osc_path=study_state_osc_path,
    )
    math_dat.nodeX = parent.nodeX + 175
    math_dat.nodeY = parent.nodeY - 260
    floor_geo.nodeX = parent.nodeX + 375
    floor_geo.nodeY = parent.nodeY - 220
    tabletop_geo.nodeX = parent.nodeX + 375
    tabletop_geo.nodeY = parent.nodeY - 330
    return floor_geo, tabletop_geo
