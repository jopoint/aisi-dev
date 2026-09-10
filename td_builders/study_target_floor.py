"""Create isolated Study target geometries in TouchDesigner.

This module is intentionally a small manual-project helper, not a builder for
the protected ``AISI_v2.toe``.  Run it from a Text DAT or the TouchDesigner
Python console after importing/pasting it into the active project.

It can create a 160 x 80 cm dashed floor target and an overlap-gated 150 x
70 cm dashed tabletop target below ``comp_study_visualization``. Their
transforms read the existing target OSC channels from
``/project1/comp_io/null_osc_raw``.
"""

from __future__ import annotations

from dataclasses import dataclass


TD_UNITS_PER_CM = 0.0052
RECT_WIDTH_CM = 160.0
RECT_DEPTH_CM = 80.0
TABLETOP_INNER_WIDTH_CM = 150.0
TABLETOP_INNER_DEPTH_CM = 70.0
OUTLINE_THICKNESS_CM = 2.5


@dataclass(frozen=True)
class DashSegment:
    """One local, axis-aligned filled bar forming part of the dashed contour."""

    width_td: float
    depth_td: float
    x_td: float
    y_td: float


def rect_target_floor_dash_segments() -> tuple[DashSegment, ...]:
    """Return local dashed-outline bars for the established 160 x 80 cm Rect."""

    return rect_target_dash_segments(RECT_WIDTH_CM, RECT_DEPTH_CM)


def rect_target_tabletop_dash_segments() -> tuple[DashSegment, ...]:
    """Return local dashed bars for the established 150 x 70 cm inner contour."""

    return rect_target_dash_segments(TABLETOP_INNER_WIDTH_CM, TABLETOP_INNER_DEPTH_CM)


def rect_target_dash_segments(width_cm: float, depth_cm: float) -> tuple[DashSegment, ...]:
    """Return the shared dashed-Rect style for a target contour.

    The returned SOP bars stay inside the nominal footprint.  Four dashes on
    each long side and two on each short side make the full outer perimeter
    visible without adding an orientation mark or a second pose data path.
    """

    width_td = width_cm * TD_UNITS_PER_CM
    depth_td = depth_cm * TD_UNITS_PER_CM
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
    """Return target expressions in the established Source world-to-TD axes."""

    raw = repr(osc_path)
    x_channel = repr("study/target_x")
    y_channel = repr("study/target_y")
    rot_channel = repr("study/target_rot")
    x_expr = (
        f"(lambda raw: ((250.0 - raw[{x_channel}].eval()) * {TD_UNITS_PER_CM}) "
        f"if raw is not None and raw[{x_channel}] is not None else 0.0)(op({raw}))"
    )
    y_expr = (
        f"(lambda raw: ((raw[{y_channel}].eval() - 250.0) * {TD_UNITS_PER_CM}) "
        f"if raw is not None and raw[{y_channel}] is not None else 0.0)(op({raw}))"
    )
    rot_expr = (
        f"(lambda raw: raw[{rot_channel}].eval() if raw is not None and "
        f"raw[{rot_channel}] is not None else 0.0)(op({raw}))"
    )
    return x_expr, y_expr, rot_expr


def target_world_to_td(target_x_cm: float, target_y_cm: float) -> tuple[float, float]:
    """Map a target World pose using the established Source TD convention."""

    return (
        (250.0 - target_x_cm) * TD_UNITS_PER_CM,
        (target_y_cm - 250.0) * TD_UNITS_PER_CM,
    )


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


def _overlap_visibility_expression(
    overlap_chop_path: str,
    osc_path: str,
) -> str:
    """Return the Study/Dual/overlap gate for the tabletop target Geometry."""

    return (
        "(lambda state, raw: float("
        "state is not None and state['overlap'] is not None and state['overlap'].eval() == 1 "
        "and raw is not None and raw['study_mode'] is not None and raw['study_mode'].eval() == 1 "
        "and raw['study_condition'] is not None and raw['study_condition'].eval() == 1"
        "))(op(%r), op(%r))" % (overlap_chop_path, osc_path)
    )


def study_tabletop_target_visible(study_mode: int, study_condition: int, overlap: float) -> bool:
    """Return the same gate semantics as the target Geometry COMP expression."""

    return study_mode == 1 and study_condition == 1 and overlap == 1


STUDY_OVERLAP_CALLBACKS_DAT_SOURCE = '''def _first_channel_sample(chop, channel_name):
    """Return a first CHOP sample, or None while TD is still initializing."""

    if chop is None:
        return None
    channel = chop[channel_name]
    if channel is None or len(channel) < 1:
        return None
    return channel[0]


def onCook(scriptOp):
    """Publish Study Motion's existing SAT result as a dependency-driven CHOP."""

    parent = scriptOp.parent()
    source = parent.op('study_source_pose')
    target = parent.op('study_target_pose')
    motion_math = parent.op('study_motion_math')
    source_values = tuple(_first_channel_sample(source, name) for name in ('tx', 'ty', 'rz'))
    target_values = tuple(_first_channel_sample(target, name) for name in ('tx', 'ty', 'rz'))
    overlap = 0.0
    if (motion_math is not None and
            all(value is not None for value in source_values) and
            all(value is not None for value in target_values)):
        values = motion_math.module.rect_motion_segments(
            source_values[0], source_values[1], source_values[2],
            target_values[0], target_values[1], target_values[2],
        )
        overlap = values['overlap']
    scriptOp.clear()
    channel = scriptOp.appendChan('overlap')
    channel[0] = overlap
'''


POSE_CHANNEL_NAMES = ("tx", "ty", "rz")


def study_pose_callbacks_dat_source(
    source_pose_name: str,
    source_geometry_path: str,
    target_pose_name: str,
    target_geometry_path: str,
) -> str:
    """Return shared Script CHOP callbacks for the two Study pose extractors."""

    pose_paths = repr({source_pose_name: source_geometry_path, target_pose_name: target_geometry_path})
    return f'''POSE_GEOMETRY_PATHS = {pose_paths}
POSE_CHANNEL_NAMES = ('tx', 'ty', 'rz')

def _geo_parameter_value(geometry_path, parameter_name):
    geo = op(geometry_path)
    if geo is None or not hasattr(geo.par, parameter_name):
        return 0.0
    return getattr(geo.par, parameter_name).eval()

def onCook(scriptOp):
    geometry_path = POSE_GEOMETRY_PATHS.get(scriptOp.name)
    scriptOp.clear()
    for parameter_name in POSE_CHANNEL_NAMES:
        channel = scriptOp.appendChan(parameter_name)
        channel[0] = (_geo_parameter_value(geometry_path, parameter_name)
                      if geometry_path is not None else 0.0)
'''


def create_study_overlap_state(
    study_component_path: str = "/project1/comp_study_visualization",
    *,
    source_geometry_name: str = "rect_floor_outer_geo",
    target_floor_geometry_name: str = "rect_target_floor_geo",
    motion_math_name: str = "study_motion_math",
    source_pose_name: str = "study_source_pose",
    target_pose_name: str = "study_target_pose",
    pose_merge_name: str = "study_overlap_pose_inputs",
    pose_callbacks_name: str = "study_pose_callbacks",
    callbacks_name: str = "study_overlap_callbacks",
    overlap_chop_name: str = "study_overlap_state",
):
    """Create a CHOP-cooked public overlap state for Study target visibility.

    Two Script CHOPs explicitly extract the source and target Geo COMP
    transforms.  Their merged output drives the Script CHOP, which invokes the
    existing Study Motion SAT function and publishes a single ``overlap``
    channel.  This deliberately moves the dynamic dependency out of a Geometry
    parameter expression, without introducing a second overlap algorithm.
    """

    parent = op(study_component_path)
    if parent is None:
        raise ValueError(f"Study component not found: {study_component_path}")
    required = (source_geometry_name, target_floor_geometry_name, motion_math_name)
    missing = [name for name in required if parent.op(name) is None]
    if missing:
        raise ValueError(f"Missing required Study operator(s): {', '.join(missing)}")
    created_names = (
        source_pose_name,
        target_pose_name,
        pose_merge_name,
        pose_callbacks_name,
        callbacks_name,
        overlap_chop_name,
    )
    existing = [name for name in created_names if parent.op(name) is not None]
    if existing:
        raise ValueError(f"Refusing to replace existing operator(s): {', '.join(existing)}")

    source_geometry_path = f"{parent.path}/{source_geometry_name}"
    target_geometry_path = f"{parent.path}/{target_floor_geometry_name}"
    pose_callbacks = parent.create(textDAT, pose_callbacks_name)
    pose_callbacks.text = study_pose_callbacks_dat_source(
        source_pose_name,
        source_geometry_path,
        target_pose_name,
        target_geometry_path,
    )
    source_pose = parent.create(scriptCHOP, source_pose_name)
    source_pose.par.callbacks = pose_callbacks
    target_pose = parent.create(scriptCHOP, target_pose_name)
    target_pose.par.callbacks = pose_callbacks
    pose_merge = parent.create(mergeCHOP, pose_merge_name)
    pose_merge.inputConnectors[0].connect(source_pose)
    pose_merge.inputConnectors[1].connect(target_pose)
    callbacks = parent.create(textDAT, callbacks_name)
    callbacks.text = STUDY_OVERLAP_CALLBACKS_DAT_SOURCE
    overlap_state = parent.create(scriptCHOP, overlap_chop_name)
    overlap_state.inputConnectors[0].connect(pose_merge)
    overlap_state.par.callbacks = callbacks
    source_pose.nodeX = parent.nodeX + 75
    source_pose.nodeY = parent.nodeY - 430
    target_pose.nodeX = parent.nodeX + 75
    target_pose.nodeY = parent.nodeY - 510
    pose_merge.nodeX = parent.nodeX + 225
    pose_merge.nodeY = parent.nodeY - 465
    pose_callbacks.nodeX = parent.nodeX + 225
    pose_callbacks.nodeY = parent.nodeY - 550
    callbacks.nodeX = parent.nodeX + 225
    callbacks.nodeY = parent.nodeY - 625
    overlap_state.nodeX = parent.nodeX + 400
    overlap_state.nodeY = parent.nodeY - 465
    return overlap_state


def create_study_target_tabletop_geo(
    study_component_path: str = "/project1/comp_study_visualization",
    *,
    source_geometry_name: str = "rect_floor_outer_geo",
    target_floor_geometry_name: str = "rect_target_floor_geo",
    motion_math_name: str = "study_motion_math",
    overlap_chop_name: str = "study_overlap_state",
    geometry_name: str = "rect_target_tabletop_geo",
    material_path: str | None = None,
):
    """Create the overlap-gated dashed inner target Geometry COMP.

    The target pose stays on the existing target OSC contract. Visibility is
    delegated to the same ``study_motion_math.rect_motion_segments(...)
    ['overlap']`` SAT result used by Study Motion; it is intentionally not a
    separate overlap implementation.
    """

    parent = op(study_component_path)
    if parent is None:
        raise ValueError(f"Study component not found: {study_component_path}")
    required = (source_geometry_name, target_floor_geometry_name, motion_math_name)
    missing = [name for name in required if parent.op(name) is None]
    if missing:
        raise ValueError(f"Missing required Study operator(s): {', '.join(missing)}")
    if parent.op(geometry_name) is not None:
        raise ValueError(f"Refusing to replace existing operator: {parent.path}/{geometry_name}")
    overlap_state = create_study_overlap_state(
        study_component_path,
        source_geometry_name=source_geometry_name,
        target_floor_geometry_name=target_floor_geometry_name,
        motion_math_name=motion_math_name,
        overlap_chop_name=overlap_chop_name,
    )

    geo = parent.create(geometryCOMP, geometry_name)
    merge = geo.create(mergeSOP, "merge_dashes")
    for index, segment in enumerate(rect_target_tabletop_dash_segments()):
        dash = geo.create(rectangleSOP, f"dash_{index:02d}")
        dash.par.sizex = segment.width_td
        dash.par.sizey = segment.depth_td
        dash.par.tx = segment.x_td
        dash.par.ty = segment.y_td
        dash.display = False
        dash.render = False
        merge.inputConnectors[index].connect(dash)

    merge.display = True
    merge.render = True
    geo.display = True
    geo.render = True
    x_expr, y_expr, rot_expr = _target_transform_expressions("/project1/comp_io/null_osc_raw")
    geo.par.tx.expr = x_expr
    geo.par.ty.expr = y_expr
    geo.par.rz.expr = rot_expr
    geo.par.sx.expr = _overlap_visibility_expression(
        overlap_state.path,
        "/project1/comp_io/null_osc_raw",
    )
    if material_path is not None and hasattr(geo.par, "material"):
        geo.par.material = material_path
    geo.nodeX = parent.nodeX + 250
    geo.nodeY = parent.nodeY - 260
    return geo
