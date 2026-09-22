"""Build fixed-capacity live Rect outlines for TouchDesigner TRACKING mode.

The geometry is deliberately independent of Study bindings and guidance.  Each
slot reads only the current ``/vision/table/<index>/*`` occupancy OSC stream.
The render helpers replace only the ``study/mode == 0`` result, preserving the
manual Study and AISI branches already present in the protected TD project.
"""

from __future__ import annotations

import builtins
import sys

from td_builders.study_tabletop_brackets import (
    FLOOR_BRACKET_DEPTH_CM,
    FLOOR_BRACKET_WIDTH_CM,
    TD_UNITS_PER_CM,
    create_continuous_outline_sops,
)


DEFAULT_TRACKING_COMPONENT_PATH = "/project1/comp_study_visualization"
DEFAULT_OSC_PATH = "/project1/comp_io/null_osc_raw"
DEFAULT_FLOOR_RENDER_PATH = "/project1/comp_layout_proposal/render_floor"
DEFAULT_TABLETOP_RENDER_PATH = "/project1/comp_layout_proposal/render_tabletop"
TRACKING_MATERIAL_NAME = "mat_tracking_table"
DEFAULT_TRACKING_MATERIAL_PATH = f"{DEFAULT_TRACKING_COMPONENT_PATH}/{TRACKING_MATERIAL_NAME}"
TRACKING_TABLE_CAPACITY = 6
TABLETOP_WIDTH_CM = 150.0
TABLETOP_DEPTH_CM = 70.0
TRACKING_RENDER_SENTINEL = "tracking_table_outlines_mode_0"


def _td_symbol(name: str):
    """Resolve TD globals from a Textport import or injected test module."""

    return globals().get(name) or getattr(builtins, name, None) or getattr(
        sys.modules.get("__main__"), name, None
    )


def tracking_floor_geometry_names() -> tuple[str, ...]:
    """Return fixed floor-outline names coupled to live occupancy indices."""

    return tuple(f"rect_tracking_floor_geo_{index:02d}" for index in range(TRACKING_TABLE_CAPACITY))


def tracking_tabletop_geometry_names() -> tuple[str, ...]:
    """Return fixed tabletop-outline names coupled to live occupancy indices."""

    return tuple(
        f"rect_tracking_tabletop_geo_{index:02d}" for index in range(TRACKING_TABLE_CAPACITY)
    )


def create_tracking_table_material(
    tracking_component_path: str = DEFAULT_TRACKING_COMPONENT_PATH,
    *,
    material_name: str = TRACKING_MATERIAL_NAME,
):
    """Create or refresh the dedicated white material for Tracking outlines.

    It deliberately never reads or alters ``mat_study_source``.  Re-running
    this function is safe: an existing dedicated material is reused and reset
    to the specified white diffuse colour.
    """

    td_op = _td_symbol("op")
    phong_mat = _td_symbol("phongMAT")
    if td_op is None or phong_mat is None:
        raise RuntimeError("TouchDesigner symbols op() and phongMAT are required")
    parent = td_op(tracking_component_path)
    if parent is None:
        raise ValueError(f"Tracking component not found: {tracking_component_path}")
    material = parent.op(material_name)
    if material is None:
        material = parent.create(phong_mat, material_name)
        material.nodeX = parent.nodeX + 900
        material.nodeY = parent.nodeY + 100
    required = ("diffr", "diffg", "diffb")
    missing = [name for name in required if not hasattr(material.par, name)]
    if missing:
        raise ValueError(f"{material.path} is missing material parameter(s): {', '.join(missing)}")
    material.par.diffr = 1.0
    material.par.diffg = 1.0
    material.par.diffb = 1.0
    return material


def apply_tracking_table_material(
    tracking_component_path: str = DEFAULT_TRACKING_COMPONENT_PATH,
    *,
    material_path: str = DEFAULT_TRACKING_MATERIAL_PATH,
):
    """Assign the dedicated material to every already-created Tracking slot."""

    td_op = _td_symbol("op")
    if td_op is None:
        raise RuntimeError("TouchDesigner op() is unavailable")
    parent = td_op(tracking_component_path)
    if parent is None:
        raise ValueError(f"Tracking component not found: {tracking_component_path}")
    names = (*tracking_floor_geometry_names(), *tracking_tabletop_geometry_names())
    missing = [name for name in names if parent.op(name) is None]
    if missing:
        raise ValueError(f"Missing Tracking geometry operator(s): {', '.join(missing)}")
    for name in names:
        geo = parent.op(name)
        if not hasattr(geo.par, "material"):
            raise ValueError(f"{geo.path} is missing Geometry material parameter")
        geo.par.material = material_path
    return tuple(parent.op(name) for name in names)


def _live_tracking_transform_expressions(osc_path: str, index: int) -> tuple[str, str, str]:
    """Return safe world-to-TD transforms for a live occupancy-table slot."""

    raw = repr(osc_path)
    channel = (
        f"raw['vision/table/{index}/%s'] if raw is not None and "
        f"raw['vision/table/{index}/%s'] is not None else None"
    )
    return (
        f"(lambda raw: (lambda value: ((250.0 - value.eval()) * {TD_UNITS_PER_CM}) "
        f"if value is not None else 0.0)({channel % ('x', 'x')}))(op({raw}))",
        f"(lambda raw: (lambda value: ((value.eval() - 250.0) * {TD_UNITS_PER_CM}) "
        f"if value is not None else 0.0)({channel % ('y', 'y')}))(op({raw}))",
        f"(lambda raw: (lambda value: (-(value.eval())) if value is not None else 0.0)"
        f"({channel % ('rot', 'rot')}))(op({raw}))",
    )


def _tracking_visibility_expression(osc_path: str, index: int) -> str:
    """Return count/availability gating isolated to TRACKING mode."""

    raw = repr(osc_path)
    return (
        "(lambda raw: float(raw is not None and raw['study/mode'] is not None "
        "and raw['study/mode'].eval() == 0 and raw['vision/table/count'] is not None "
        f"and raw['vision/table/count'].eval() > {index} and "
        f"raw['vision/table/{index}/available'] is not None and "
        f"raw['vision/table/{index}/available'].eval() == 1))(op({raw}))"
    )


def _create_tracking_outline_geo(
    parent,
    name: str,
    *,
    index: int,
    width_cm: float,
    depth_cm: float,
    osc_path: str,
    material_path: str,
):
    """Create one visual-only four-bar outline with no default primitive."""

    geometry_comp = _td_symbol("geometryCOMP")
    if geometry_comp is None:
        raise RuntimeError("TouchDesigner symbol is unavailable: geometryCOMP")
    geo = parent.create(geometry_comp, name)
    create_continuous_outline_sops(geo, width_cm=width_cm, depth_cm=depth_cm)
    geo.par.tx.expr, geo.par.ty.expr, geo.par.rz.expr = _live_tracking_transform_expressions(
        osc_path, index
    )
    geo.par.sx.expr = _tracking_visibility_expression(osc_path, index)
    if hasattr(geo.par, "material"):
        geo.par.material = material_path
    geo.display = True
    geo.render = True
    return geo


def create_tracking_table_outline_geos(
    tracking_component_path: str = DEFAULT_TRACKING_COMPONENT_PATH,
    *,
    osc_path: str = DEFAULT_OSC_PATH,
    material_path: str = DEFAULT_TRACKING_MATERIAL_PATH,
):
    """Create six live floor and tabletop outlines, refusing replacement.

    The names and OSC slots are identical by index.  Existing Study source,
    target, motion, mask, and setup geometries are never touched.
    """

    td_op = _td_symbol("op")
    if td_op is None:
        raise RuntimeError("TouchDesigner op() is unavailable")
    parent = td_op(tracking_component_path)
    if parent is None:
        raise ValueError(f"Tracking component not found: {tracking_component_path}")
    floor_names = tracking_floor_geometry_names()
    tabletop_names = tracking_tabletop_geometry_names()
    existing = [name for name in (*floor_names, *tabletop_names) if parent.op(name) is not None]
    if existing:
        raise ValueError(f"Refusing to replace existing operator(s): {', '.join(existing)}")

    floor_geos = tuple(
        _create_tracking_outline_geo(
            parent, name, index=index, width_cm=FLOOR_BRACKET_WIDTH_CM,
            depth_cm=FLOOR_BRACKET_DEPTH_CM, osc_path=osc_path, material_path=material_path,
        )
        for index, name in enumerate(floor_names)
    )
    tabletop_geos = tuple(
        _create_tracking_outline_geo(
            parent, name, index=index, width_cm=TABLETOP_WIDTH_CM,
            depth_cm=TABLETOP_DEPTH_CM, osc_path=osc_path, material_path=material_path,
        )
        for index, name in enumerate(tabletop_names)
    )
    for index, geo in enumerate((*floor_geos, *tabletop_geos)):
        geo.nodeX = parent.nodeX + 1100 + (250 if index >= TRACKING_TABLE_CAPACITY else 0)
        geo.nodeY = parent.nodeY - 100 - (index % TRACKING_TABLE_CAPACITY) * 100
    return floor_geos, tabletop_geos


def tracking_render_geometry_list(
    *, tracking_component_path: str = DEFAULT_TRACKING_COMPONENT_PATH, tabletop: bool
) -> str:
    """Return the unique fixed geometry list for one TRACKING render surface."""

    names = tracking_tabletop_geometry_names() if tabletop else tracking_floor_geometry_names()
    return " ".join(f"{tracking_component_path}/{name}" for name in names)


def tracking_mode_render_expression(existing_expression: str, *, tracking_geometry_list: str, osc_path: str = DEFAULT_OSC_PATH) -> str:
    """Wrap an existing TD render expression, overriding only mode zero.

    ``existing_expression`` remains verbatim in the non-TRACKING branch, so
    manual Study and AISI routing cannot be accidentally reconstructed here.
    """

    if not existing_expression.strip():
        raise ValueError("existing render Geometry expression is required")
    if TRACKING_RENDER_SENTINEL in existing_expression:
        raise ValueError("Tracking render expression is already patched")
    raw = repr(osc_path)
    return (
        f"# {TRACKING_RENDER_SENTINEL}\n"
        f"(lambda raw: {tracking_geometry_list!r} if raw is not None and "
        "raw['study/mode'] is not None and raw['study/mode'].eval() == 0 "
        f"else ({existing_expression}))(op({raw}))"
    )


def configure_tracking_mode_render_paths(
    *,
    floor_render_path: str = DEFAULT_FLOOR_RENDER_PATH,
    tabletop_render_path: str = DEFAULT_TABLETOP_RENDER_PATH,
    tracking_component_path: str = DEFAULT_TRACKING_COMPONENT_PATH,
    osc_path: str = DEFAULT_OSC_PATH,
):
    """Patch the two Render TOP Geometry expressions for mode-zero outlines."""

    td_op = _td_symbol("op")
    if td_op is None:
        raise RuntimeError("TouchDesigner op() is unavailable")
    configured = []
    for render_path, tabletop in ((floor_render_path, False), (tabletop_render_path, True)):
        render = td_op(render_path)
        if render is None:
            raise ValueError(f"Render TOP not found: {render_path}")
        if not hasattr(render.par, "geometry"):
            raise ValueError(f"{render.path} is missing Render TOP parameter: geometry")
        existing_expression = str(getattr(render.par.geometry, "expr", ""))
        if not existing_expression:
            existing_expression = str(render.par.geometry.eval())
        render.par.geometry.expr = tracking_mode_render_expression(
            existing_expression,
            tracking_geometry_list=tracking_render_geometry_list(
                tracking_component_path=tracking_component_path, tabletop=tabletop
            ),
            osc_path=osc_path,
        )
        configured.append(render)
    return tuple(configured)
