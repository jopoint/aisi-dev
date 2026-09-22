"""Reusable Study source-outline geometry.

These visual twins deliberately replace only projected source contours. They
do not affect floor/table masks, poses, or any Vision/OSC state.
"""

from __future__ import annotations

from dataclasses import dataclass
import builtins
import sys


TD_UNITS_PER_CM = 0.0052
DEFAULT_BRACKET_LENGTH_CM = 20.0
DEFAULT_OUTLINE_THICKNESS_CM = 2.5
DEFAULT_TABLETOP_RENDER_PATH = "/project1/comp_layout_proposal/render_tabletop"
DEFAULT_FLOOR_RENDER_PATH = "/project1/comp_layout_proposal/render_floor"
RECT_WIDTH_CM = 160.0
RECT_DEPTH_CM = 80.0
FLOOR_SOURCE_PADDING_CM = 5.0
FLOOR_BRACKET_WIDTH_CM = RECT_WIDTH_CM + 2.0 * FLOOR_SOURCE_PADDING_CM
FLOOR_BRACKET_DEPTH_CM = RECT_DEPTH_CM + 2.0 * FLOOR_SOURCE_PADDING_CM
SOURCE_MATERIAL_NAME = "mat_study_source"


def _td_symbol(name: str):
    """Resolve a TouchDesigner operator type in Textport or injected modules."""

    symbol = (
        globals().get(name)
        or getattr(builtins, name, None)
        or getattr(sys.modules.get("__main__"), name, None)
    )
    if symbol is None:
        raise RuntimeError(f"TouchDesigner symbol is unavailable: {name}")
    return symbol


def remove_default_primitives(geo) -> None:
    """Remove TD's incidental default primitives from an authored bracket Geo."""

    for child in tuple(geo.children):
        if child.name == "torus1" or child.name.startswith(("torus", "donut", "sphere")):
            child.destroy()


def replace_geometry_path_once(expression: str, old_path: str, new_path: str) -> str:
    """Return a safe single-path render-expression update without duplicates."""

    if old_path not in expression:
        raise ValueError("expected source geometry path is absent from render expression")
    if new_path in expression:
        raise ValueError("replacement source geometry path already exists in render expression")
    return expression.replace(old_path, new_path)


@dataclass(frozen=True)
class CornerBracketSegment:
    """One filled local bar belonging to a named rectangle corner."""

    corner: str
    axis: str
    width_td: float
    depth_td: float
    x_td: float
    y_td: float


@dataclass(frozen=True)
class ContinuousOutlineSegment:
    """One filled bar in a continuous rectangular outline."""

    side: str
    width_td: float
    depth_td: float
    x_td: float
    y_td: float


def rect_corner_bracket_segments(
    width_cm: float,
    depth_cm: float,
    *,
    bracket_length_cm: float = DEFAULT_BRACKET_LENGTH_CM,
    thickness_cm: float = DEFAULT_OUTLINE_THICKNESS_CM,
) -> tuple[CornerBracketSegment, ...]:
    """Return eight inside-footprint bars: two orthogonal bars per corner."""

    if width_cm <= 0.0 or depth_cm <= 0.0:
        raise ValueError("rectangle dimensions must be positive")
    if bracket_length_cm <= 0.0 or bracket_length_cm > min(width_cm, depth_cm):
        raise ValueError("bracket_length_cm must be positive and fit both rectangle dimensions")
    if thickness_cm <= 0.0 or thickness_cm > min(width_cm, depth_cm):
        raise ValueError("thickness_cm must be positive and fit both rectangle dimensions")

    width_td = width_cm * TD_UNITS_PER_CM
    depth_td = depth_cm * TD_UNITS_PER_CM
    length_td = bracket_length_cm * TD_UNITS_PER_CM
    thickness_td = thickness_cm * TD_UNITS_PER_CM
    half_width = width_td / 2.0
    half_depth = depth_td / 2.0

    segments: list[CornerBracketSegment] = []
    for corner, x_sign, y_sign in (
        ("bottom_left", -1.0, -1.0),
        ("bottom_right", 1.0, -1.0),
        ("top_right", 1.0, 1.0),
        ("top_left", -1.0, 1.0),
    ):
        segments.extend((
            CornerBracketSegment(
                corner, "horizontal", length_td, thickness_td,
                x_sign * (half_width - length_td / 2.0),
                y_sign * (half_depth - thickness_td / 2.0),
            ),
            CornerBracketSegment(
                corner, "vertical", thickness_td, length_td,
                x_sign * (half_width - thickness_td / 2.0),
                y_sign * (half_depth - length_td / 2.0),
            ),
        ))
    return tuple(segments)


def rect_continuous_outline_segments(
    width_cm: float,
    depth_cm: float,
    *,
    thickness_cm: float = DEFAULT_OUTLINE_THICKNESS_CM,
) -> tuple[ContinuousOutlineSegment, ...]:
    """Return four filled bars whose exterior is the requested footprint."""

    if width_cm <= 0.0 or depth_cm <= 0.0:
        raise ValueError("rectangle dimensions must be positive")
    if thickness_cm <= 0.0 or thickness_cm > min(width_cm, depth_cm):
        raise ValueError("thickness_cm must be positive and fit both rectangle dimensions")
    width_td = width_cm * TD_UNITS_PER_CM
    depth_td = depth_cm * TD_UNITS_PER_CM
    thickness_td = thickness_cm * TD_UNITS_PER_CM
    return (
        ContinuousOutlineSegment("top", width_td, thickness_td, 0.0, depth_td / 2.0 - thickness_td / 2.0),
        ContinuousOutlineSegment("bottom", width_td, thickness_td, 0.0, -depth_td / 2.0 + thickness_td / 2.0),
        ContinuousOutlineSegment("left", thickness_td, depth_td, -width_td / 2.0 + thickness_td / 2.0, 0.0),
        ContinuousOutlineSegment("right", thickness_td, depth_td, width_td / 2.0 - thickness_td / 2.0, 0.0),
    )


def create_corner_bracket_sops(geo, *, width_cm: float, depth_cm: float, name: str = "merge_corner_brackets"):
    """Create a local TD SOP merge containing the eight reusable brackets.

    The caller owns the Geometry COMP transform/material.  This keeps the
    same source/target pose behavior while changing only the local contour.
    """

    if geo.op(name) is not None:
        raise ValueError(f"Refusing to replace existing operator: {geo.path}/{name}")
    remove_default_primitives(geo)
    merge = geo.create(_td_symbol("mergeSOP"), name)
    for index, segment in enumerate(rect_corner_bracket_segments(width_cm, depth_cm)):
        bar = geo.create(_td_symbol("rectangleSOP"), f"corner_{segment.corner}_{segment.axis}")
        bar.par.sizex = segment.width_td
        bar.par.sizey = segment.depth_td
        bar.par.tx = segment.x_td
        bar.par.ty = segment.y_td
        bar.display = False
        bar.render = False
        merge.inputConnectors[index].connect(bar)
    merge.display = True
    merge.render = True
    return merge


def create_continuous_outline_sops(
    geo,
    *,
    width_cm: float,
    depth_cm: float,
    name: str = "merge_continuous_outline",
):
    """Create the four Rectangle SOP bars for a continuous source outline."""

    if geo.op(name) is not None:
        raise ValueError(f"Refusing to replace existing operator: {geo.path}/{name}")
    remove_default_primitives(geo)
    merge = geo.create(_td_symbol("mergeSOP"), name)
    for index, segment in enumerate(rect_continuous_outline_segments(width_cm, depth_cm)):
        bar = geo.create(_td_symbol("rectangleSOP"), f"outline_{segment.side}")
        bar.par.sizex = segment.width_td
        bar.par.sizey = segment.depth_td
        bar.par.tx = segment.x_td
        bar.par.ty = segment.y_td
        bar.display = False
        bar.render = False
        merge.inputConnectors[index].connect(bar)
    merge.display = True
    merge.render = True
    return merge


def _copy_parameter(source_parameter, destination_parameter) -> None:
    """Copy a TD parameter's expression when present, otherwise its value."""

    expression = getattr(source_parameter, "expr", "")
    if expression:
        destination_parameter.expr = expression
    else:
        destination_parameter.val = source_parameter.eval()


def create_study_tabletop_source_bracket_geo(
    study_component_path: str = "/project1/comp_study_visualization",
    *,
    source_geometry_name: str = "rect_tabletop_inner_geo",
    geometry_name: str = "rect_tabletop_inner_brackets_geo",
    width_cm: float = 150.0,
    depth_cm: float = 70.0,
    disable_original_render: bool = True,
):
    """Create a bracket-only visual twin of the existing tabletop source geo.

    The existing source Geo remains intact for its filled ``table_surface``
    mask consumer.  Its transform/material/visibility parameters are copied
    to a new visual-only Geometry COMP.  Setting ``disable_original_render``
    replaces only its render contribution and is reversible by toggling its
    ``render`` flag back on.
    """

    td_op = globals().get("op") or getattr(builtins, "op", None)
    if td_op is None:
        raise RuntimeError("TouchDesigner op() is unavailable")
    parent = td_op(study_component_path)
    if parent is None:
        raise ValueError(f"Study component not found: {study_component_path}")
    source = parent.op(source_geometry_name)
    if source is None:
        raise ValueError(f"Source tabletop geometry not found: {parent.path}/{source_geometry_name}")
    if parent.op(geometry_name) is not None:
        raise ValueError(f"Refusing to replace existing operator: {parent.path}/{geometry_name}")

    geo = parent.create(_td_symbol("geometryCOMP"), geometry_name)
    create_corner_bracket_sops(geo, width_cm=width_cm, depth_cm=depth_cm)
    for parameter_name in ("tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz"):
        if hasattr(source.par, parameter_name) and hasattr(geo.par, parameter_name):
            _copy_parameter(getattr(source.par, parameter_name), getattr(geo.par, parameter_name))
    if hasattr(source.par, "material") and hasattr(geo.par, "material"):
        _copy_parameter(source.par.material, geo.par.material)
    geo.display = True
    geo.render = True
    geo.nodeX = source.nodeX + 250
    geo.nodeY = source.nodeY
    if disable_original_render:
        source.render = False
    return geo


def create_study_floor_source_bracket_geo(
    study_component_path: str = "/project1/comp_study_visualization",
    *,
    source_geometry_name: str = "rect_floor_outer_geo",
    geometry_name: str = "rect_floor_outer_brackets_geo",
    disable_original_render: bool = True,
):
    """Create the padded 170 x 90 cm corner-bracket twin of the live source."""

    td_op = globals().get("op") or getattr(builtins, "op", None)
    if td_op is None:
        raise RuntimeError("TouchDesigner op() is unavailable")
    parent = td_op(study_component_path)
    if parent is None:
        raise ValueError(f"Study component not found: {study_component_path}")
    source = parent.op(source_geometry_name)
    if source is None:
        raise ValueError(f"Source floor geometry not found: {parent.path}/{source_geometry_name}")
    if parent.op(geometry_name) is not None:
        raise ValueError(f"Refusing to replace existing operator: {parent.path}/{geometry_name}")

    geo = parent.create(_td_symbol("geometryCOMP"), geometry_name)
    create_corner_bracket_sops(
        geo, width_cm=FLOOR_BRACKET_WIDTH_CM, depth_cm=FLOOR_BRACKET_DEPTH_CM
    )
    for parameter_name in ("tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz"):
        if hasattr(source.par, parameter_name) and hasattr(geo.par, parameter_name):
            _copy_parameter(getattr(source.par, parameter_name), getattr(geo.par, parameter_name))
    geo.display = True
    geo.render = True
    geo.nodeX = source.nodeX + 250
    geo.nodeY = source.nodeY - 100
    if disable_original_render:
        source.render = False
    return geo


def _disable_geometry_render(parent, geometry_name: str) -> None:
    """Disable a superseded visual twin without deleting its authored SOPs."""

    old_geo = parent.op(geometry_name)
    if old_geo is not None:
        old_geo.display = False
        old_geo.render = False


def create_study_tabletop_source_outline_geo(
    study_component_path: str = "/project1/comp_study_visualization",
    *,
    source_geometry_name: str = "rect_tabletop_inner_geo",
    geometry_name: str = "rect_tabletop_inner_outline_geo",
    width_cm: float = 150.0,
    depth_cm: float = 70.0,
    material_path: str = SOURCE_MATERIAL_NAME,
    disable_bracket_render: bool = True,
):
    """Create the 150 x 70 cm continuous-tabletop source outline."""

    td_op = globals().get("op") or getattr(builtins, "op", None)
    if td_op is None:
        raise RuntimeError("TouchDesigner op() is unavailable")
    parent = td_op(study_component_path)
    if parent is None:
        raise ValueError(f"Study component not found: {study_component_path}")
    source = parent.op(source_geometry_name)
    if source is None:
        raise ValueError(f"Source tabletop geometry not found: {parent.path}/{source_geometry_name}")
    if parent.op(geometry_name) is not None:
        raise ValueError(f"Refusing to replace existing operator: {parent.path}/{geometry_name}")
    geo = parent.create(_td_symbol("geometryCOMP"), geometry_name)
    create_continuous_outline_sops(geo, width_cm=width_cm, depth_cm=depth_cm)
    for parameter_name in ("tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz"):
        if hasattr(source.par, parameter_name) and hasattr(geo.par, parameter_name):
            _copy_parameter(getattr(source.par, parameter_name), getattr(geo.par, parameter_name))
    if hasattr(geo.par, "material"):
        geo.par.material = material_path
    geo.display = True
    geo.render = True
    geo.nodeX = source.nodeX + 350
    geo.nodeY = source.nodeY
    if disable_bracket_render:
        _disable_geometry_render(parent, "rect_tabletop_inner_brackets_geo")
    return geo


def create_study_floor_source_outline_geo(
    study_component_path: str = "/project1/comp_study_visualization",
    *,
    source_geometry_name: str = "rect_floor_outer_geo",
    geometry_name: str = "rect_floor_outer_outline_geo",
    material_path: str = SOURCE_MATERIAL_NAME,
    disable_bracket_render: bool = True,
):
    """Create the padded 170 x 90 cm continuous-floor source outline."""

    td_op = globals().get("op") or getattr(builtins, "op", None)
    if td_op is None:
        raise RuntimeError("TouchDesigner op() is unavailable")
    parent = td_op(study_component_path)
    if parent is None:
        raise ValueError(f"Study component not found: {study_component_path}")
    source = parent.op(source_geometry_name)
    if source is None:
        raise ValueError(f"Source floor geometry not found: {parent.path}/{source_geometry_name}")
    if parent.op(geometry_name) is not None:
        raise ValueError(f"Refusing to replace existing operator: {parent.path}/{geometry_name}")
    geo = parent.create(_td_symbol("geometryCOMP"), geometry_name)
    create_continuous_outline_sops(
        geo, width_cm=FLOOR_BRACKET_WIDTH_CM, depth_cm=FLOOR_BRACKET_DEPTH_CM
    )
    for parameter_name in ("tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz"):
        if hasattr(source.par, parameter_name) and hasattr(geo.par, parameter_name):
            _copy_parameter(getattr(source.par, parameter_name), getattr(geo.par, parameter_name))
    if hasattr(geo.par, "material"):
        geo.par.material = material_path
    geo.display = True
    geo.render = True
    geo.nodeX = source.nodeX + 350
    geo.nodeY = source.nodeY - 100
    if disable_bracket_render:
        _disable_geometry_render(parent, "rect_floor_outer_brackets_geo")
    return geo


def replace_study_tabletop_render_source(
    render_path: str = DEFAULT_TABLETOP_RENDER_PATH,
    *,
    old_geometry_path: str = "/project1/comp_study_visualization/rect_tabletop_inner_geo",
    new_geometry_path: str = "/project1/comp_study_visualization/rect_tabletop_inner_brackets_geo",
) -> None:
    """Replace only the Study source path in an existing Render TOP expression."""

    td_op = globals().get("op") or getattr(builtins, "op", None)
    if td_op is None:
        raise RuntimeError("TouchDesigner op() is unavailable")
    render = td_op(render_path)
    if render is None:
        raise ValueError(f"Tabletop Render TOP not found: {render_path}")
    expression = str(render.par.geometry.expr)
    try:
        render.par.geometry.expr = replace_geometry_path_once(
            expression, old_geometry_path, new_geometry_path
        )
    except ValueError as error:
        raise ValueError(f"{render.path}.par.geometry.expr: {error}") from error


def replace_study_floor_render_source(
    render_path: str = DEFAULT_FLOOR_RENDER_PATH,
    *,
    old_geometry_path: str = "/project1/comp_study_visualization/rect_floor_outer_geo",
    new_geometry_path: str = "/project1/comp_study_visualization/rect_floor_outer_brackets_geo",
) -> None:
    """Replace only the Study source path in the existing floor Render TOP."""

    td_op = globals().get("op") or getattr(builtins, "op", None)
    if td_op is None:
        raise RuntimeError("TouchDesigner op() is unavailable")
    render = td_op(render_path)
    if render is None:
        raise ValueError(f"Floor Render TOP not found: {render_path}")
    expression = str(render.par.geometry.expr)
    try:
        render.par.geometry.expr = replace_geometry_path_once(
            expression, old_geometry_path, new_geometry_path
        )
    except ValueError as error:
        raise ValueError(f"{render.path}.par.geometry.expr: {error}") from error


def replace_study_tabletop_brackets_with_outline_render_source(
    render_path: str = DEFAULT_TABLETOP_RENDER_PATH,
    *,
    old_geometry_path: str = "/project1/comp_study_visualization/rect_tabletop_inner_brackets_geo",
    new_geometry_path: str = "/project1/comp_study_visualization/rect_tabletop_inner_outline_geo",
) -> None:
    """Replace the visual-only tabletop brackets path exactly once."""

    td_op = globals().get("op") or getattr(builtins, "op", None)
    if td_op is None:
        raise RuntimeError("TouchDesigner op() is unavailable")
    render = td_op(render_path)
    if render is None:
        raise ValueError(f"Tabletop Render TOP not found: {render_path}")
    try:
        render.par.geometry.expr = replace_geometry_path_once(
            str(render.par.geometry.expr), old_geometry_path, new_geometry_path
        )
    except ValueError as error:
        raise ValueError(f"{render.path}.par.geometry.expr: {error}") from error


def replace_study_floor_brackets_with_outline_render_source(
    render_path: str = DEFAULT_FLOOR_RENDER_PATH,
    *,
    old_geometry_path: str = "/project1/comp_study_visualization/rect_floor_outer_brackets_geo",
    new_geometry_path: str = "/project1/comp_study_visualization/rect_floor_outer_outline_geo",
) -> None:
    """Replace the visual-only padded floor brackets path exactly once."""

    td_op = globals().get("op") or getattr(builtins, "op", None)
    if td_op is None:
        raise RuntimeError("TouchDesigner op() is unavailable")
    render = td_op(render_path)
    if render is None:
        raise ValueError(f"Floor Render TOP not found: {render_path}")
    try:
        render.par.geometry.expr = replace_geometry_path_once(
            str(render.par.geometry.expr), old_geometry_path, new_geometry_path
        )
    except ValueError as error:
        raise ValueError(f"{render.path}.par.geometry.expr: {error}") from error
