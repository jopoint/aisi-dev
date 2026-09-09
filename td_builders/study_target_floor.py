"""Create the isolated Study floor-target geometry in TouchDesigner.

This module is intentionally a small manual-project helper, not a builder for
the protected ``AISI_v2.toe``.  Run it from a Text DAT or the TouchDesigner
Python console after importing/pasting it into the active project.

It creates only ``rect_target_floor_geo`` below ``comp_study_visualization``.
The geometry is a 160 x 80 cm Rect-table outer footprint represented by
dashed, thin SOP rectangles.  Its transform reads the existing target OSC
channels from ``/project1/comp_io/null_osc_raw``.
"""

from __future__ import annotations

from dataclasses import dataclass


TD_UNITS_PER_CM = 0.0052
RECT_WIDTH_CM = 160.0
RECT_DEPTH_CM = 80.0
OUTLINE_THICKNESS_CM = 2.5


@dataclass(frozen=True)
class DashSegment:
    """One local, axis-aligned filled bar forming part of the dashed contour."""

    width_td: float
    depth_td: float
    x_td: float
    y_td: float


def rect_target_floor_dash_segments() -> tuple[DashSegment, ...]:
    """Return local dashed-outline bars for the established 160 x 80 cm Rect.

    The returned SOP bars stay inside the nominal footprint.  Four dashes on
    each long side and two on each short side make the full outer perimeter
    visible without adding an orientation mark or a second pose data path.
    """

    width_td = RECT_WIDTH_CM * TD_UNITS_PER_CM
    depth_td = RECT_DEPTH_CM * TD_UNITS_PER_CM
    thickness_td = OUTLINE_THICKNESS_CM * TD_UNITS_PER_CM
    half_width = width_td / 2.0
    half_depth = depth_td / 2.0

    long_count = 4
    short_count = 2
    long_dash = width_td / (long_count * 2 - 1)
    short_dash = depth_td / (short_count * 2 - 1)
    long_step = (width_td - long_dash) / (long_count - 1)
    short_step = (depth_td - short_dash) / (short_count - 1)

    segments: list[DashSegment] = []
    for side_y in (-half_depth + thickness_td / 2.0, half_depth - thickness_td / 2.0):
        for index in range(long_count):
            x_td = -half_width + long_dash / 2.0 + index * long_step
            segments.append(DashSegment(long_dash, thickness_td, x_td, side_y))
    for side_x in (-half_width + thickness_td / 2.0, half_width - thickness_td / 2.0):
        for index in range(short_count):
            y_td = -half_depth + short_dash / 2.0 + index * short_step
            segments.append(DashSegment(thickness_td, short_dash, side_x, y_td))
    return tuple(segments)


def _target_transform_expressions(osc_path: str) -> tuple[str, str, str]:
    """Return TD parameter expressions for the existing target OSC contract."""

    raw = repr(osc_path)
    x_channel = repr("table/0/target_x")
    y_channel = repr("table/0/target_y")
    rot_channel = repr("table/0/target_rot")
    x_expr = (
        f"(lambda raw: ((raw[{x_channel}].eval() - 250.0) * {TD_UNITS_PER_CM}) "
        f"if raw is not None and raw[{x_channel}] is not None else 0.0)(op({raw}))"
    )
    y_expr = (
        f"(lambda raw: -((raw[{y_channel}].eval() - 250.0) * {TD_UNITS_PER_CM}) "
        f"if raw is not None and raw[{y_channel}] is not None else 0.0)(op({raw}))"
    )
    rot_expr = (
        f"(lambda raw: raw[{rot_channel}].eval() if raw is not None and "
        f"raw[{rot_channel}] is not None else 0.0)(op({raw}))"
    )
    return x_expr, y_expr, rot_expr


def create_study_target_floor_geo(
    study_component_path: str = "/project1/comp_study_visualization",
    *,
    osc_path: str = "/project1/comp_io/null_osc_raw",
    geometry_name: str = "rect_target_floor_geo",
    material_path: str | None = None,
):
    """Create and return the dedicated dashed Rect target Geometry COMP.

    TouchDesigner-only function.  It deliberately refuses to replace an
    existing operator and leaves all render, mask, calibration, and projector
    operators untouched.  Assign the desired existing floor material manually
    to the returned Geometry COMP if its parent does not provide a default.
    """

    parent = op(study_component_path)
    if parent is None:
        raise ValueError(f"Study component not found: {study_component_path}")
    if parent.op(geometry_name) is not None:
        raise ValueError(f"Refusing to replace existing operator: {parent.path}/{geometry_name}")

    geo = parent.create(geometryCOMP, geometry_name)
    merge = geo.create(mergeSOP, "merge_dashes")
    for index, segment in enumerate(rect_target_floor_dash_segments()):
        dash = geo.create(rectangleSOP, f"dash_{index:02d}")
        dash.par.sizex = segment.width_td
        dash.par.sizey = segment.depth_td
        dash.par.tx = segment.x_td
        dash.par.ty = segment.y_td
        merge.inputConnectors[index].connect(dash)

    merge.display = True
    merge.render = True
    geo.display = True
    geo.render = True
    x_expr, y_expr, rot_expr = _target_transform_expressions(osc_path)
    geo.par.tx.expr = x_expr
    geo.par.ty.expr = y_expr
    geo.par.rz.expr = rot_expr
    if material_path is not None and hasattr(geo.par, "material"):
        geo.par.material = material_path
    geo.nodeX = parent.nodeX + 250
    geo.nodeY = parent.nodeY - 150
    return geo
