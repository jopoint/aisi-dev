from __future__ import annotations

import math
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, Polygon, Rectangle

from aisi.core.models import LayoutProposal, SceneState, choose_facing_normal_toward_target
from aisi.core.table_geometry import resolve_table_state_geometry, table_world_footprint


def plot_scene_state(
    scene_state: SceneState,
    save_path: str | Path | None = None,
    show: bool = False,
) -> None:
    """Plot current scene state with ROI and source objects."""
    figure, ax = plt.subplots(figsize=(8, 6))
    _setup_axes(ax, scene_state, title="Scene State")

    for table in scene_state.tables:
        _draw_rotated_table_centered(
            ax,
            table=table,
            x=table.x,
            y=table.y,
            rot_deg=table.rot_deg,
            edgecolor="#2E7D32",
            fillcolor="#2E7D32",
            linestyle="-",
            alpha=0.18,
            label="Ist",
            facing_target=None,
            show_facing_arrow=False,
        )

    for chair in scene_state.chairs:
        _draw_chair(ax, chair.x, chair.y, color="#546E7A", filled=True)

    _finalize_plot(figure, save_path=save_path, show=show)


def plot_layout_proposal(
    scene_state: SceneState,
    layout_proposal: LayoutProposal,
    save_path: str | Path | None = None,
    show: bool = False,
) -> None:
    """Plot only the target layout proposal in ROI coordinates."""
    figure, ax = plt.subplots(figsize=(8, 6))
    _setup_axes(ax, scene_state, title="Layout Proposal")

    source_map = {table.table_id: table for table in scene_state.tables}
    for target in layout_proposal.table_targets:
        source = source_map.get(target.table_id)
        if source is None:
            continue
        _draw_rotated_table_centered(
            ax,
            table=source,
            x=target.target_x,
            y=target.target_y,
            rot_deg=target.target_rot_deg,
            edgecolor="#EF6C00",
            fillcolor="none",
            linestyle="--",
            alpha=1.0,
            label="Soll",
            facing_target=(target.facing_target_x, target.facing_target_y)
            if target.facing_target_x is not None and target.facing_target_y is not None
            else None,
            show_facing_arrow=True,
        )

    _finalize_plot(figure, save_path=save_path, show=show)


def plot_before_after(
    scene_state: SceneState,
    layout_proposal: LayoutProposal,
    save_path: str | Path | None = None,
    show: bool = False,
    show_chairs: bool = False,
) -> None:
    """Plot source and target states together, including mapping lines."""
    figure, ax = plt.subplots(figsize=(9, 7))
    _setup_axes(ax, scene_state, title="Before / After")

    source_map = {table.table_id: table for table in scene_state.tables}

    for table in scene_state.tables:
        _draw_rotated_table_centered(
            ax,
            table=table,
            x=table.x,
            y=table.y,
            rot_deg=table.rot_deg,
            edgecolor="#1E88E5",
            fillcolor="#1E88E5",
            linestyle="-",
            alpha=0.14,
            label="Ist",
            facing_target=None,
            show_facing_arrow=False,
        )

    for target in layout_proposal.table_targets:
        source = source_map.get(target.table_id)
        if source is None:
            continue
        _draw_rotated_table_centered(
            ax,
            table=source,
            x=target.target_x,
            y=target.target_y,
            rot_deg=target.target_rot_deg,
            edgecolor="#E53935",
            fillcolor="none",
            linestyle="--",
            alpha=1.0,
            label="Soll",
            facing_target=(target.facing_target_x, target.facing_target_y)
            if target.facing_target_x is not None and target.facing_target_y is not None
            else None,
            show_facing_arrow=True,
        )
        if source:
            ax.plot([source.x, target.target_x], [source.y, target.target_y], linestyle=":", color="#616161", linewidth=1.0)

    if show_chairs:
        for chair in scene_state.chairs:
            _draw_chair(ax, chair.x, chair.y, color="#607D8B", filled=True)

    _finalize_plot(figure, save_path=save_path, show=show)


def _setup_axes(ax: plt.Axes, scene_state: SceneState, title: str) -> None:
    roi = scene_state.roi
    ax.set_title(title)
    ax.add_patch(
        Rectangle(
            (roi.x_min, roi.y_min),
            roi.width,
            roi.height,
            fill=False,
            linewidth=1.5,
            edgecolor="#212121",
        )
    )
    ax.set_xlim(roi.x_min - 20.0, roi.x_max + 20.0)
    ax.set_ylim(roi.y_max + 20.0, roi.y_min - 20.0)
    ax.set_aspect("equal", adjustable="box")
    ax.grid(alpha=0.15)


def _draw_table(
    ax: plt.Axes,
    x: float,
    y: float,
    theta_deg: float,
    width: float,
    height: float,
    color: str,
    linestyle: str,
) -> None:
    half_w = width / 2.0
    half_h = height / 2.0
    corners = [(-half_w, -half_h), (half_w, -half_h), (half_w, half_h), (-half_w, half_h)]

    theta = math.radians(theta_deg)
    cos_t = math.cos(theta)
    sin_t = math.sin(theta)

    rotated = []
    for px, py in corners:
        rx = x + (px * cos_t - py * sin_t)
        ry = y + (px * sin_t + py * cos_t)
        rotated.append((rx, ry))

    patch = Polygon(rotated, closed=True, fill=False, edgecolor=color, linestyle=linestyle, linewidth=1.8)
    ax.add_patch(patch)
    ax.text(x, y, "T", color=color, fontsize=8, ha="center", va="center")


def _draw_rotated_table_centered(
    ax: plt.Axes,
    table,
    x: float,
    y: float,
    rot_deg: float,
    edgecolor: str,
    fillcolor: str,
    linestyle: str,
    alpha: float,
    label: str,
    facing_target: tuple[float, float] | None,
    show_facing_arrow: bool,
) -> None:
    """Draw table geometry and optional facing-normal arrow."""
    footprint = table_world_footprint(table, (x, y), rot_deg)
    patch = Polygon(
        footprint,
        closed=True,
        facecolor=fillcolor,
        edgecolor=edgecolor,
        linestyle=linestyle,
        linewidth=1.8,
        alpha=alpha,
    )
    ax.add_patch(patch)

    if show_facing_arrow:
        facing_vector = _facing_vector_for_plot(x, y, rot_deg, facing_target)
        arrow_length = resolve_table_state_geometry(table).nominal_depth * 0.52
        ax.add_patch(
            FancyArrowPatch(
                (x, y),
                (x + facing_vector[0] * arrow_length, y + facing_vector[1] * arrow_length),
                arrowstyle="-|>",
                mutation_scale=10,
                color=edgecolor,
                linewidth=1.0,
                alpha=0.95,
            )
        )
    ax.text(x, y, f"{label}\n{rot_deg:.0f}°", color=edgecolor, fontsize=7, ha="center", va="center")


def _facing_vector_for_plot(
    center_x: float,
    center_y: float,
    rot_deg: float,
    facing_target: tuple[float, float] | None,
) -> tuple[float, float]:
    if facing_target is None:
        # Fallback: choose one normal deterministically (90 deg from long axis).
        theta = math.radians(rot_deg + 90.0)
        return math.cos(theta), math.sin(theta)

    return choose_facing_normal_toward_target(
        table_center=(center_x, center_y),
        target_point=facing_target,
        rot_deg=rot_deg,
    )


def _draw_chair(ax: plt.Axes, x: float, y: float, color: str, filled: bool) -> None:
    patch = Circle((x, y), radius=10.0, facecolor=color if filled else "none", edgecolor=color, linewidth=1.2, alpha=0.6)
    ax.add_patch(patch)


def _finalize_plot(figure: plt.Figure, save_path: str | Path | None, show: bool) -> None:
    if save_path is not None:
        destination = Path(save_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        figure.savefig(destination, dpi=150, bbox_inches="tight")
    if show:
        plt.show()
    plt.close(figure)
