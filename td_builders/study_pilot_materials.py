"""Study visual material references used by the pilot builders.

The live ``.toe`` owns the actual palette. This module only assigns the
established source material name and never creates or recolours a TD material.
"""

from __future__ import annotations

import builtins


SOURCE_MATERIAL_NAME = "mat_study_source"
TARGET_MATERIAL_NAME = "mat_study_target"
SOURCE_OUTLINE_GEOMETRIES = (
    "rect_tabletop_inner_outline_geo",
    "rect_floor_outer_outline_geo",
)


def apply_study_source_outline_material(
    study_component_path: str = "/project1/comp_study_visualization",
    *,
    material_path: str = SOURCE_MATERIAL_NAME,
):
    """Bind only the two new source outlines to ``mat_study_source``.

    Targets and motion are deliberately left untouched, retaining the
    project's existing ``mat_study_target``/motion material and colours.
    """

    td_op = globals().get("op") or getattr(builtins, "op", None)
    if td_op is None:
        raise RuntimeError("TouchDesigner op() is unavailable")
    parent = td_op(study_component_path)
    if parent is None:
        raise ValueError(f"Study component not found: {study_component_path}")
    for geometry_name in SOURCE_OUTLINE_GEOMETRIES:
        geo = parent.op(geometry_name)
        if geo is not None and hasattr(geo.par, "material"):
            geo.par.material = material_path
