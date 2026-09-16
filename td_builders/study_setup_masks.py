"""Create live physical-occupancy table masks without changing mask routing.

The active manual project already renders a filled table surface into the
shared table-mask TOP.  This helper adds only the variable HOME setup-table
instances to that same Render TOP's Geometry list. Each instance is driven
only by the live ``/vision/table/*`` occupancy stream.
"""

from __future__ import annotations

import builtins

from td_builders.study_tabletop_brackets import remove_default_primitives
import sys

from td_builders.study_start_pose import TD_UNITS_PER_CM


DEFAULT_STUDY_COMPONENT_PATH = "/project1/comp_study_visualization"
DEFAULT_OSC_PATH = "/project1/comp_io/null_osc_raw"
DEFAULT_MASK_RENDER_PATH = "/project1/comp_layout_proposal/render_table_mask"
DEFAULT_TRACKING_MASK_GEOMETRY_PATH = "/project1/comp_tracking_only/rect_table_mask_geo"
DEFAULT_TABLE_SURFACE_PATH = "../rect_tabletop_inner_geo/table_surface"
SETUP_MASK_COUNT = 6


def _td_symbol(name: str):
    """Resolve TD symbols when this module was imported from a Textport."""

    value = globals().get(name, getattr(builtins, name, None))
    return value if value is not None else getattr(sys.modules.get("__main__"), name, None)


def _setup_mask_transform_expressions(osc_path: str, index: int) -> tuple[str, str, str]:
    """Return safe mirrored transforms for one live occupancy-table slot."""

    raw = repr(osc_path)
    channel = f"raw['vision/table/{index}/%s'] if raw is not None and raw['vision/table/{index}/%s'] is not None else None"
    return (
        f"(lambda raw: (lambda channel: ((250.0 - channel.eval()) * {TD_UNITS_PER_CM}) if channel is not None else 0.0)({channel % ('x', 'x')}))(op({raw}))",
        f"(lambda raw: (lambda channel: ((channel.eval() - 250.0) * {TD_UNITS_PER_CM}) if channel is not None else 0.0)({channel % ('y', 'y')}))(op({raw}))",
        f"(lambda raw: (lambda channel: (-(channel.eval())) if channel is not None else 0.0)({channel % ('rot', 'rot')}))(op({raw}))",
    )


def _setup_mask_visibility_expression(osc_path: str, index: int) -> str:
    """Return safe live occupancy count/availability gate."""

    raw = repr(osc_path)
    return (
        "(lambda raw: float(raw is not None and raw['vision/table/count'] is not None "
        f"and raw['vision/table/count'].eval() > {index} and raw['vision/table/{index}/available'] is not None "
        f"and raw['vision/table/{index}/available'].eval() == 1))(op({raw}))"
    )


def setup_mask_geometry_names() -> tuple[str, ...]:
    """Return the six fixed-capacity Study HOME mask Geometry COMP names."""

    return tuple(f"rect_setup_mask_geo_{index:02d}" for index in range(SETUP_MASK_COUNT))


def _configure_table_surface_select(select_sop, surface_path: str) -> None:
    """Point a Select SOP at the existing filled local tabletop surface."""

    parameter_name = "sops" if hasattr(select_sop.par, "sops") else "soppath"
    if not hasattr(select_sop.par, parameter_name):
        operator_name = getattr(select_sop, "path", "<new Select SOP>")
        raise ValueError(f"{operator_name} is missing Select SOP parameter: sops")
    setattr(select_sop.par, parameter_name, surface_path)


def _create_setup_mask_geo(
    parent,
    name: str,
    *,
    osc_path: str,
    index: int,
    table_surface_path: str,
):
    """Create one filled setup-table mask using the shared Study surface."""

    geo = parent.create(_td_symbol("geometryCOMP"), name)
    remove_default_primitives(geo)
    table_surface = geo.create(_td_symbol("selectSOP"), "select_table_surface")
    _configure_table_surface_select(table_surface, table_surface_path)
    table_surface.display = True
    table_surface.render = True
    geo.display = True
    geo.render = True
    geo.par.tx.expr, geo.par.ty.expr, geo.par.rz.expr = _setup_mask_transform_expressions(
        osc_path, index
    )
    geo.par.sx.expr = _setup_mask_visibility_expression(osc_path, index)
    return geo


def create_study_setup_mask_geos(
    study_component_path: str = DEFAULT_STUDY_COMPONENT_PATH,
    *,
    osc_path: str = DEFAULT_OSC_PATH,
    table_surface_path: str = DEFAULT_TABLE_SURFACE_PATH,
):
    """Create six count-gated filled HOME setup-table mask geometries.

    ``table_surface_path`` intentionally defaults to the same local filled
    tabletop surface selected by the existing active-table mask geometry.
    The helper never touches the shared render/mask/composite chain.
    """

    parent = _td_symbol("op")(study_component_path)
    if parent is None:
        raise ValueError(f"Study component not found: {study_component_path}")
    names = setup_mask_geometry_names()
    existing = [name for name in names if parent.op(name) is not None]
    if existing:
        raise ValueError(f"Refusing to replace existing operator(s): {', '.join(existing)}")
    geos = tuple(
        _create_setup_mask_geo(
            parent,
            name,
            osc_path=osc_path,
            index=index,
            table_surface_path=table_surface_path,
        )
        for index, name in enumerate(names)
    )
    for index, geo in enumerate(geos):
        geo.nodeX = parent.nodeX + 750
        geo.nodeY = parent.nodeY - 375 - index * 80
    return geos


def study_setup_mask_render_geometry_expression(
    *,
    osc_path: str = DEFAULT_OSC_PATH,
    study_component_path: str = DEFAULT_STUDY_COMPONENT_PATH,
    tracking_mask_geometry_path: str = DEFAULT_TRACKING_MASK_GEOMETRY_PATH,
) -> str:
    """Return the fixed Geometry list for all six live occupancy masks."""

    home_mask_geometries = " ".join(
        f"{study_component_path}/{name}" for name in setup_mask_geometry_names()
    )
    return home_mask_geometries


def configure_study_setup_mask_render(
    render_path: str = DEFAULT_MASK_RENDER_PATH,
    *,
    osc_path: str = DEFAULT_OSC_PATH,
    study_component_path: str = DEFAULT_STUDY_COMPONENT_PATH,
    tracking_mask_geometry_path: str = DEFAULT_TRACKING_MASK_GEOMETRY_PATH,
):
    """Patch only the shared mask Render TOP's fixed Geometry list."""

    render = _td_symbol("op")(render_path)
    if render is None:
        raise ValueError(f"Mask Render TOP not found: {render_path}")
    if not hasattr(render.par, "geometry"):
        raise ValueError(f"{render.path} is missing Render TOP parameter: geometry")
    render.par.geometry.expr = ""
    render.par.geometry = study_setup_mask_render_geometry_expression(
        osc_path=osc_path,
        study_component_path=study_component_path,
        tracking_mask_geometry_path=tracking_mask_geometry_path,
    )
    return render
