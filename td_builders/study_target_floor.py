"""Create isolated Study target geometries in TouchDesigner.

This module is intentionally a small manual-project helper, not a builder for
the protected ``AISI_v2.toe``.  Run it from a Text DAT or the TouchDesigner
Python console after importing/pasting it into the active project.

It can create a 170 x 90 cm dashed floor target and an overlap-gated 150 x
70 cm dashed tabletop target below ``comp_study_visualization``. Their
transforms read the existing target OSC channels from
``/project1/comp_io/null_osc_raw``.
"""

from __future__ import annotations

from dataclasses import dataclass

from td_builders.study_tabletop_brackets import (
    FLOOR_BRACKET_DEPTH_CM,
    FLOOR_BRACKET_WIDTH_CM,
    remove_default_primitives,
)



TD_UNITS_PER_CM = 0.0052
RECT_WIDTH_CM = 160.0
RECT_DEPTH_CM = 80.0
FLOOR_TARGET_WIDTH_CM = FLOOR_BRACKET_WIDTH_CM
FLOOR_TARGET_DEPTH_CM = FLOOR_BRACKET_DEPTH_CM
TABLETOP_INNER_WIDTH_CM = 150.0
TABLETOP_INNER_DEPTH_CM = 70.0
OUTLINE_THICKNESS_CM = 2.5
# A small positive offset eliminates z-fighting and makes target contours win
# depth testing over their coplanar source outlines without visible movement.
TARGET_DEPTH_OFFSET_TD = 0.001


@dataclass(frozen=True)
class DashSegment:
    """One local, axis-aligned filled bar forming part of the dashed contour."""

    width_td: float
    depth_td: float
    x_td: float
    y_td: float


def rect_target_floor_dash_segments() -> tuple[DashSegment, ...]:
    """Return dashed bars matching the padded 170 x 90 cm floor source outline."""

    return rect_target_dash_segments(FLOOR_TARGET_WIDTH_CM, FLOOR_TARGET_DEPTH_CM)


def rect_target_tabletop_dash_segments() -> tuple[DashSegment, ...]:
    """Return the established full dashed 150 x 70 cm inner target contour."""

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
    """Return target expressions in the established Source world-to-TD axes.

    The mirrored world-to-TD X axis also reverses target yaw, matching the
    corrected HOME setup-table convention.
    """

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
        f"(lambda raw: -(raw[{rot_channel}].eval()) if raw is not None and "
        f"raw[{rot_channel}] is not None else 0.0)(op({raw}))"
    )
    return x_expr, y_expr, rot_expr


def target_world_to_td(target_x_cm: float, target_y_cm: float) -> tuple[float, float]:
    """Map a target World pose using the established Source TD convention."""

    return (
        (250.0 - target_x_cm) * TD_UNITS_PER_CM,
        (target_y_cm - 250.0) * TD_UNITS_PER_CM,
    )


def target_world_rotation_to_td(rotation_deg: float) -> float:
    """Map Study target yaw into TouchDesigner's mirrored world axes."""

    return -rotation_deg


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
    remove_default_primitives(geo)
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
    geo.par.tz = TARGET_DEPTH_OFFSET_TD
    geo.par.sx.expr = _active_study_visibility_expression(osc_path)
    if material_path is not None and hasattr(geo.par, "material"):
        geo.par.material = material_path
    geo.nodeX = parent.nodeX + 250
    geo.nodeY = parent.nodeY - 150
    return geo


def _overlap_visibility_expression(
    overlap_chop_path: str,
    osc_path: str,
) -> str:
    """Return the active-Study/Dual/overlap gate for the tabletop target."""

    return (
        "(lambda state, raw: float("
        "state is not None and state['overlap'] is not None and state['overlap'].eval() == 1 "
        "and raw is not None and raw['study_mode'] is not None and raw['study_mode'].eval() == 1 "
        "and raw['study_condition'] is not None and raw['study_condition'].eval() == 1 "
        "and raw['study_phase'] is not None and raw['study_phase'].eval() == 2"
        "))(op(%r), op(%r))" % (overlap_chop_path, osc_path)
    )


def study_tabletop_target_visible(
    study_mode: int, study_condition: int, overlap: float, study_phase: int = 2
) -> bool:
    """Return the same gate semantics as the target Geometry COMP expression."""

    return study_mode == 1 and study_condition == 1 and study_phase == 2 and overlap == 1


def _active_study_visibility_expression(osc_path: str) -> str:
    """Return the direct STUDY/ACTIVE gate for the floor target Geometry."""

    return (
        "(lambda raw: float(raw is not None and raw['study_mode'] is not None "
        "and raw['study_mode'].eval() == 1 and raw['study_phase'] is not None "
        "and raw['study_phase'].eval() == 2))(op(%r))" % osc_path
    )


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


STUDY_TABLETOP_VISIBILITY_CALLBACKS_DAT_SOURCE = '''def _first_channel_sample(chop, *channel_names):
    """Return one input sample, accepting TD's slash/underscore OSC aliases."""

    if chop is None:
        return None
    for channel_name in channel_names:
        channel = chop[channel_name]
        if channel is not None and len(channel) >= 1:
            return channel[0]
    return None


def onCook(scriptOp):
    """Publish the native-export gate for the Study tabletop target."""

    inputs = scriptOp.inputs
    state = inputs[0] if len(inputs) > 0 else None
    mode = _first_channel_sample(state, 'study/mode', 'study_mode')
    condition = _first_channel_sample(state, 'study/condition', 'study_condition')
    phase = _first_channel_sample(state, 'study/phase', 'study_phase')
    overlap = _first_channel_sample(state, 'overlap')
    visible = float(mode == 1 and condition == 1 and phase == 2 and overlap == 1)
    scriptOp.clear()
    channel = scriptOp.appendChan('rect_target_tabletop_geo:sx')
    channel[0] = visible
'''


POSE_CHANNEL_NAMES = ("tx", "ty", "rz")


def _configure_pose_object_chop(object_chop, geometry_path: str, reference_path: str) -> None:
    """Configure a native Object CHOP as a Geo-transform dependency bridge.

    Object CHOP owns real dependencies on both Object COMP transforms. Using
    the Study parent as its reference makes the emitted transform equivalent to
    the sibling Geo COMP's local ``tx``, ``ty``, and ``rz`` values. This avoids
    relying on an imperative parameter read inside a source-less Script CHOP.
    """

    required = ("target", "reference", "compute", "nameformat", "outputrange")
    missing = [name for name in required if not hasattr(object_chop.par, name)]
    if missing:
        operator_name = getattr(object_chop, "path", "<new Object CHOP>")
        raise ValueError(
            f"{operator_name} cannot configure Object CHOP transform dependency; "
            f"missing parameter(s): {', '.join(missing)}"
        )
    object_chop.par.target = geometry_path
    object_chop.par.reference = reference_path
    object_chop.par.compute = "transform"
    object_chop.par.nameformat = "channel"
    object_chop.par.outputrange = "currentframe"


def _configure_visibility_export_chop(export_chop, export_root_path: str) -> None:
    """Configure CHOP-name export to the fixed tabletop target ``sx`` Par."""

    required = ("exportmethod", "autoexportroot")
    missing = [name for name in required if not hasattr(export_chop.par, name)]
    if missing:
        operator_name = getattr(export_chop, "path", "<new visibility Null CHOP>")
        raise ValueError(
            f"{operator_name} cannot configure CHOP export; "
            f"missing parameter(s): {', '.join(missing)}"
        )
    export_chop.par.exportmethod = "autoname"
    export_chop.par.autoexportroot = export_root_path
    export_chop.export = True


def _configure_visibility_state_select_chop(select_chop, osc_chop_path: str) -> None:
    """Select the three Study-state channels needed by the visibility gate."""

    required = ("chop", "channames")
    missing = [name for name in required if not hasattr(select_chop.par, name)]
    if missing:
        operator_name = getattr(select_chop, "path", "<new visibility Select CHOP>")
        raise ValueError(
            f"{operator_name} cannot configure Study-state selection; "
            f"missing parameter(s): {', '.join(missing)}"
        )
    select_chop.par.chop = osc_chop_path
    select_chop.par.channames = "study/mode study/condition study/phase"


def create_study_target_tabletop_visibility_state(
    study_component_path: str = "/project1/comp_study_visualization",
    *,
    osc_path: str = "/project1/comp_io/null_osc_raw",
    overlap_chop_name: str = "study_overlap_state",
    geometry_name: str = "rect_target_tabletop_geo",
    state_chop_name: str = "study_target_tabletop_visibility_state",
    inputs_name: str = "study_target_tabletop_visibility_inputs",
    callbacks_name: str = "study_target_tabletop_visibility_callbacks",
    visibility_chop_name: str = "study_target_tabletop_visibility",
    export_chop_name: str = "study_target_tabletop_visibility_export",
):
    """Create the input-driven CHOP export that owns tabletop-target visibility.

    The Script CHOP receives a Merge CHOP input containing both the live Study
    OSC state and the native overlap result. A local Select CHOP establishes
    the OSC dependency and limits it to exactly ``study/mode``,
    ``study/condition``, and ``study/phase``. The final Null CHOP exports its
    only channel, ``rect_target_tabletop_geo:sx``, directly to the Geometry
    COMP parameter. No Geometry parameter expression is involved.
    """

    parent = op(study_component_path)
    if parent is None:
        raise ValueError(f"Study component not found: {study_component_path}")
    geo = parent.op(geometry_name)
    overlap_state = parent.op(overlap_chop_name)
    raw_state = op(osc_path)
    required = {
        f"{parent.path}/{geometry_name}": geo,
        f"{parent.path}/{overlap_chop_name}": overlap_state,
        osc_path: raw_state,
    }
    missing = [path for path, operator in required.items() if operator is None]
    if missing:
        raise ValueError(f"Missing required Study operator(s): {', '.join(missing)}")
    created_names = (state_chop_name, inputs_name, callbacks_name, visibility_chop_name, export_chop_name)
    existing = [name for name in created_names if parent.op(name) is not None]
    if existing:
        raise ValueError(f"Refusing to replace existing operator(s): {', '.join(existing)}")

    # Remove the opaque pull expression before the CHOP export becomes owner
    # of the same parameter. The constant fallback is inactive while export is
    # enabled, but leaves a safe hidden default if the export is ever disabled.
    geo.par.sx.expr = ""
    geo.par.sx = 0.0
    visibility_state = parent.create(selectCHOP, state_chop_name)
    _configure_visibility_state_select_chop(visibility_state, raw_state.path)
    visibility_inputs = parent.create(mergeCHOP, inputs_name)
    visibility_inputs.inputConnectors[0].connect(visibility_state)
    visibility_inputs.inputConnectors[1].connect(overlap_state)
    callbacks = parent.create(textDAT, callbacks_name)
    callbacks.text = STUDY_TABLETOP_VISIBILITY_CALLBACKS_DAT_SOURCE
    visibility = parent.create(scriptCHOP, visibility_chop_name)
    visibility.inputConnectors[0].connect(visibility_inputs)
    visibility.par.callbacks = callbacks
    visibility_export = parent.create(nullCHOP, export_chop_name)
    visibility_export.inputConnectors[0].connect(visibility)
    _configure_visibility_export_chop(visibility_export, parent.path)
    visibility_state.nodeX = parent.nodeX + 250
    visibility_state.nodeY = parent.nodeY - 550
    visibility_inputs.nodeX = parent.nodeX + 425
    visibility_inputs.nodeY = parent.nodeY - 550
    callbacks.nodeX = parent.nodeX + 425
    callbacks.nodeY = parent.nodeY - 625
    visibility.nodeX = parent.nodeX + 600
    visibility.nodeY = parent.nodeY - 550
    visibility_export.nodeX = parent.nodeX + 775
    visibility_export.nodeY = parent.nodeY - 550
    return visibility_export


def create_study_overlap_state(
    study_component_path: str = "/project1/comp_study_visualization",
    *,
    source_geometry_name: str = "rect_floor_outer_geo",
    target_floor_geometry_name: str = "rect_target_floor_geo",
    motion_math_name: str = "study_motion_math",
    source_pose_name: str = "study_source_pose",
    target_pose_name: str = "study_target_pose",
    pose_merge_name: str = "study_overlap_pose_inputs",
    callbacks_name: str = "study_overlap_callbacks",
    overlap_chop_name: str = "study_overlap_state",
):
    """Create a CHOP-cooked public overlap state for Study target visibility.

    Two Object CHOPs natively depend on the source and target Geo COMP
    transforms. Their merged output drives the Script CHOP, which invokes the
    existing Study Motion SAT function and publishes a single ``overlap``
    channel. This deliberately moves the dynamic dependency out of a Geometry
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
        callbacks_name,
        overlap_chop_name,
    )
    existing = [name for name in created_names if parent.op(name) is not None]
    if existing:
        raise ValueError(f"Refusing to replace existing operator(s): {', '.join(existing)}")

    source_geometry_path = f"{parent.path}/{source_geometry_name}"
    target_geometry_path = f"{parent.path}/{target_floor_geometry_name}"
    source_pose = parent.create(objectCHOP, source_pose_name)
    _configure_pose_object_chop(source_pose, source_geometry_path, parent.path)
    target_pose = parent.create(objectCHOP, target_pose_name)
    _configure_pose_object_chop(target_pose, target_geometry_path, parent.path)
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
    callbacks.nodeX = parent.nodeX + 225
    callbacks.nodeY = parent.nodeY - 550
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
    _build_target_tabletop_dashes(geo)

    geo.display = True
    geo.render = True
    x_expr, y_expr, rot_expr = _target_transform_expressions("/project1/comp_io/null_osc_raw")
    geo.par.tx.expr = x_expr
    geo.par.ty.expr = y_expr
    geo.par.rz.expr = rot_expr
    geo.par.tz = TARGET_DEPTH_OFFSET_TD
    if material_path is not None and hasattr(geo.par, "material"):
        geo.par.material = material_path
    geo.nodeX = parent.nodeX + 250
    geo.nodeY = parent.nodeY - 260
    create_study_target_tabletop_visibility_state(
        study_component_path,
        overlap_chop_name=overlap_state.name,
        geometry_name=geometry_name,
    )
    return geo


def _build_target_tabletop_dashes(geo) -> None:
    """Populate a target Geo with its established full dashed contour."""

    remove_default_primitives(geo)
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


def restore_study_target_tabletop_dashes(
    study_component_path: str = "/project1/comp_study_visualization",
    *,
    geometry_name: str = "rect_target_tabletop_geo",
):
    """Restore an existing target tabletop Geo's local dashed contour.

    The target Geo's transforms, visibility CHOP export, material, and all
    other Study operators remain in place. This is the restart-safe update
    path for an already built ``.toe``.
    """

    parent = op(study_component_path)
    if parent is None:
        raise ValueError(f"Study component not found: {study_component_path}")
    geo = parent.op(geometry_name)
    if geo is None:
        raise ValueError(f"Target tabletop geometry not found: {parent.path}/{geometry_name}")
    legacy_nodes = list(geo.ops("bracket_*"))
    legacy_merge = geo.op("merge_corner_brackets")
    if legacy_merge is not None:
        legacy_nodes.append(legacy_merge)
    for node in legacy_nodes:
        node.destroy()
    if geo.op("merge_dashes") is not None:
        raise ValueError(f"Dashed target contour already installed: {geo.path}/merge_dashes")
    _build_target_tabletop_dashes(geo)
    return geo


# Compatibility for the immediately preceding pilot experiment. New callers
# should use ``restore_study_target_tabletop_dashes``.
replace_study_target_tabletop_contour_with_brackets = restore_study_target_tabletop_dashes
