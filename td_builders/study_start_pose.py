"""Create isolated neutral HOME/READY setup guides for Study Mode.

All table setup contours use identical solid 160 x 80 cm outlines. The helper
does not label or style the future task-relevant table differently from any
distractor, and never edits shared render, mask, calibration, or projector
operators.
"""

from __future__ import annotations

from dataclasses import dataclass
import math


TD_UNITS_PER_CM = 0.0052
RECT_WIDTH_CM = 160.0
RECT_DEPTH_CM = 80.0
OUTLINE_THICKNESS_CM = 2.5


@dataclass(frozen=True)
class OutlineSegment:
    """One local bar in a continuous outer-Rect outline."""

    width_td: float
    depth_td: float
    x_td: float
    y_td: float


def rect_start_floor_solid_segments() -> tuple[OutlineSegment, ...]:
    """Return four touching bars forming a solid canonical outer Rect."""

    width, depth = RECT_WIDTH_CM * TD_UNITS_PER_CM, RECT_DEPTH_CM * TD_UNITS_PER_CM
    thickness = OUTLINE_THICKNESS_CM * TD_UNITS_PER_CM
    return (
        OutlineSegment(width, thickness, 0.0, -depth / 2.0 + thickness / 2.0),
        OutlineSegment(width, thickness, 0.0, depth / 2.0 - thickness / 2.0),
        OutlineSegment(thickness, depth - 2.0 * thickness, -width / 2.0 + thickness / 2.0, 0.0),
        OutlineSegment(thickness, depth - 2.0 * thickness, width / 2.0 - thickness / 2.0, 0.0),
    )


def _setup_table_transform_expressions(osc_path: str, index: int) -> tuple[str, str, str]:
    """Return a neutral setup-table pose from the variable Study-owned list."""

    raw, prefix = repr(osc_path), f"study/setup_table/{index}"
    return (
        f"(lambda raw: ((250.0 - raw[{prefix + '/x'!r}].eval()) * {TD_UNITS_PER_CM}) if raw is not None and raw[{prefix + '/x'!r}] is not None else 0.0)(op({raw}))",
        f"(lambda raw: ((raw[{prefix + '/y'!r}].eval() - 250.0) * {TD_UNITS_PER_CM}) if raw is not None and raw[{prefix + '/y'!r}] is not None else 0.0)(op({raw}))",
        f"(lambda raw: raw[{prefix + '/rot'!r}].eval() if raw is not None and raw[{prefix + '/rot'!r}] is not None else 0.0)(op({raw}))",
    )


def _home_ready_visibility_expression(osc_path: str, count_channel: str, index: int) -> str:
    """Return a STUDY/HOME-or-READY gate with a variable-list count guard."""

    return (
        "(lambda raw: float(raw is not None and raw['study/mode'] is not None "
        "and raw['study/mode'].eval() == 1 and raw['study/phase'] is not None "
        "and raw['study/phase'].eval() in (0, 1) and raw[%r] is not None "
        "and raw[%r].eval() > %d))(op(%r))" % (count_channel, count_channel, index, osc_path)
    )


def _marker_value_expression(
    osc_path: str,
    index: int,
    field: str,
    *,
    world_axis: str | None = None,
    cm_to_td: bool = False,
    clamp_positive: bool = False,
) -> str:
    """Read a marker value, optionally mapping world centimetres into TD."""

    channel, raw = f"study/participant_start/{index}/{field}", repr(osc_path)
    value = f"raw[{channel!r}].eval()"
    if clamp_positive:
        value = f"max({value}, 0.0)"
    if world_axis == "x":
        value = f"(250.0 - ({value})) * {TD_UNITS_PER_CM}"
    elif world_axis == "y":
        value = f"(({value}) - 250.0) * {TD_UNITS_PER_CM}"
    elif world_axis is not None:
        raise ValueError("world_axis must be 'x', 'y', or None")
    elif cm_to_td:
        value = f"({value}) * {TD_UNITS_PER_CM}"
    return f"(lambda raw: {value} if raw is not None and raw[{channel!r}] is not None else 0.0)(op({raw}))"


def _create_setup_table_geo(parent, name: str, *, osc_path: str, index: int, material_path: str | None):
    geo = parent.create(geometryCOMP, name)
    merge = geo.create(mergeSOP, "merge_solid_outline")
    for segment_index, segment in enumerate(rect_start_floor_solid_segments()):
        bar = geo.create(rectangleSOP, f"outline_{segment_index:02d}")
        bar.par.sizex, bar.par.sizey = segment.width_td, segment.depth_td
        bar.par.tx, bar.par.ty = segment.x_td, segment.y_td
        bar.display = False; bar.render = False
        merge.inputConnectors[segment_index].connect(bar)
    merge.display = True; merge.render = True; geo.display = True; geo.render = True
    geo.par.tx.expr, geo.par.ty.expr, geo.par.rz.expr = _setup_table_transform_expressions(osc_path, index)
    geo.par.sx.expr = _home_ready_visibility_expression(osc_path, "study/setup_table_count", index)
    geo.par.tz = 0.03
    if material_path is not None and hasattr(geo.par, "material"):
        geo.par.material = material_path
    return geo


def _create_participant_marker_geo(parent, name: str, *, osc_path: str, index: int, material_path: str | None):
    """Create a neutral dashed floor ring without a participant/table label."""

    geo = parent.create(geometryCOMP, name)
    merge = geo.create(mergeSOP, "merge_dashed_marker")
    dash_count = 12
    radius_expr = _marker_value_expression(
        osc_path, index, "radius", cm_to_td=True, clamp_positive=True
    )
    for dash_index in range(dash_count):
        angle = 2.0 * math.pi * dash_index / dash_count
        dash = geo.create(rectangleSOP, f"marker_dash_{dash_index:02d}")
        dash_xform = geo.create(transformSOP, f"marker_dash_xform_{dash_index:02d}")
        dash_xform.inputConnectors[0].connect(dash)
        dash.par.sizex.expr = f"({radius_expr}) * {2.0 * math.pi / (dash_count * 1.7)}"
        dash.par.sizey = OUTLINE_THICKNESS_CM * TD_UNITS_PER_CM
        dash_xform.par.tx.expr = f"({radius_expr}) * {math.cos(angle)}"
        dash_xform.par.ty.expr = f"({radius_expr}) * {math.sin(angle)}"
        dash_xform.par.rz = math.degrees(angle) + 90.0
        dash.display = False; dash.render = False; dash_xform.display = False; dash_xform.render = False
        merge.inputConnectors[dash_index].connect(dash_xform)
    merge.display = True; merge.render = True; geo.display = True; geo.render = True
    geo.par.tx.expr = _marker_value_expression(osc_path, index, "x", world_axis="x")
    geo.par.ty.expr = _marker_value_expression(osc_path, index, "y", world_axis="y")
    geo.par.sx.expr = _home_ready_visibility_expression(osc_path, "study/participant_start_count", index)
    geo.par.tz = 0.025
    if material_path is not None and hasattr(geo.par, "material"):
        geo.par.material = material_path
    return geo


def create_study_home_setup_geos(
    study_component_path: str = "/project1/comp_study_visualization",
    *,
    osc_path: str = "/project1/comp_io/null_osc_raw",
    max_table_count: int = 6,
    max_participant_count: int = 4,
    material_path: str | None = None,
):
    """Create neutral variable-capacity HOME setup tables and person markers.

    Index zero deliberately retains the historic ``rect_start_floor_geo`` name;
    it is visually identical to every ``rect_setup_floor_geo_XX`` distractor.
    """

    if max_table_count < 1 or max_participant_count < 0:
        raise ValueError("max_table_count must be >= 1 and max_participant_count must be >= 0")
    parent = op(study_component_path)
    if parent is None:
        raise ValueError(f"Study component not found: {study_component_path}")
    # Keep each TD operator's suffix coupled to its OSC-list index. Do not use
    # a shared/fallback setup pose for the additional geometries.
    table_specs = (("rect_start_floor_geo", 0),) + tuple(
        (f"rect_setup_floor_geo_{index:02d}", index)
        for index in range(1, max_table_count)
    )
    table_names = tuple(name for name, _ in table_specs)
    marker_names = tuple(f"study_participant_start_marker_geo_{index:02d}" for index in range(max_participant_count))
    existing = [name for name in table_names + marker_names if parent.op(name) is not None]
    if existing:
        raise ValueError(f"Refusing to replace existing operator(s): {', '.join(existing)}")
    tables = tuple(
        _create_setup_table_geo(
            parent, name, osc_path=osc_path, index=index, material_path=material_path
        )
        for name, index in table_specs
    )
    markers = tuple(_create_participant_marker_geo(parent, name, osc_path=osc_path, index=index, material_path=material_path) for index, name in enumerate(marker_names))
    for index, geo in enumerate(tables): geo.nodeX, geo.nodeY = parent.nodeX + 250, parent.nodeY - 375 - index * 80
    for index, geo in enumerate(markers): geo.nodeX, geo.nodeY = parent.nodeX + 500, parent.nodeY - 375 - index * 80
    return tables, markers


def create_study_start_floor_geo(study_component_path: str = "/project1/comp_study_visualization", **kwargs):
    """Create just index-zero's solid setup outline for backward compatibility."""

    return create_study_home_setup_geos(study_component_path, max_table_count=1, max_participant_count=0, **kwargs)[0][0]
