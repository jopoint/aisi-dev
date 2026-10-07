"""Plot the synthetic Input planning preview without publishing chair OSC.

This is intentionally a local review aid: it renders source tables, generated
targets and source-to-target paths in one ROI.
It does not depend on TouchDesigner.  Optional chair markers are a local
review overlay; they are not sent to OSC.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, Polygon, Rectangle

from aisi.app.sim_layout_rules import (
    _normalize_scene_for_aisi,
    compute_synthetic_layout,
    plan_synthetic_input_chairs,
)
from aisi.core.models import TableTarget
from aisi.core.table_geometry import table_world_footprint
from aisi.input.scene_loader import build_scene_state_from_dict


ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plot the synthetic Input table-chair preview.")
    parser.add_argument("--participants", type=int, default=8, help="Planned participants for active-table selection.")
    parser.add_argument(
        "--scene",
        type=Path,
        default=ROOT / "data/aisi/scenes/simulated/live_scene.json",
        help="Source scene JSON.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="PNG destination (defaults below data/aisi/debug).",
    )
    parser.add_argument(
        "--editor-defaults",
        action="store_true",
        help="Use the five-Rect Room-Editor start scene instead of the live scene file.",
    )
    parser.add_argument(
        "--show-chairs",
        action="store_true",
        help="Overlay locally planned Input chairs; does not change OSC output.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.editor_defaults:
        from aisi.app.sim_room_editor import make_default_tables, scene_payload

        raw_scene = scene_payload(make_default_tables(), chairs=[], persons=[])
    else:
        raw_scene = json.loads(args.scene.read_text(encoding="utf-8"))
    scene = build_scene_state_from_dict(_normalize_scene_for_aisi(raw_scene), learning_format="input")
    output = compute_synthetic_layout(
        raw_scene,
        "input",
        transformation_strength=1.0,
        activity_parameters={
            "participants": args.participants,
            "presentation_side": None,
            "adaptive_layout_preview": True,
        },
    )
    destination = args.output or (
        ROOT / "data/aisi/debug/synthetic_input_preview" / f"input_{args.participants}_participants.png"
    )
    targets = {
        table.table_id: TableTarget(
            table_id=table.table_id,
            target_x=item["x_cm"],
            target_y=item["y_cm"],
            source_rot_deg=table.rot_deg,
            target_rot_deg=item["rotation_deg"],
        )
        for table, item in zip(scene.tables, output.table_targets)
    }

    figure, ax = plt.subplots(figsize=(9, 9))
    roi = scene.roi
    ax.add_patch(Rectangle((roi.x_min, roi.y_min), roi.width, roi.height, fill=False, edgecolor="#202020", linewidth=2))
    for table in scene.tables:
        source_polygon = table_world_footprint(table, (table.x, table.y), table.rot_deg)
        target = targets[table.table_id]
        target_polygon = table_world_footprint(table, (target.target_x, target.target_y), target.target_rot_deg)
        moved = (table.x, table.y, table.rot_deg) != (target.target_x, target.target_y, target.target_rot_deg)
        ax.add_patch(Polygon(source_polygon, closed=True, facecolor="#35c75a", edgecolor="#159637", alpha=0.20))
        active = table.table_id in output.active_table_ids
        ax.add_patch(Polygon(
            target_polygon,
            closed=True,
            facecolor="#1976d2" if active else "#757575",
            edgecolor="#1976d2" if active else "#424242",
            alpha=0.14 if active else 0.10,
            linewidth=2.0,
            linestyle="--" if active else ":",
        ))
        if moved:
            ax.add_patch(FancyArrowPatch((table.x, table.y), (target.target_x, target.target_y), arrowstyle="->", color="#555555", linewidth=1.1, mutation_scale=9))
        ax.text(target.target_x, target.target_y, table.table_id, color="#0d47a1", ha="center", va="center", fontsize=7)

    if args.show_chairs:
        for chair in plan_synthetic_input_chairs(raw_scene, output, args.participants):
            ax.add_patch(Circle(
                (float(chair["x_cm"]), float(chair["y_cm"])),
                radius=float(chair["radius_cm"]),
                facecolor="#ef6c00",
                edgecolor="#b54300",
                alpha=0.76,
                linewidth=1.0,
            ))

    ax.set_title(
        f"Table-only Input-Vorschau: {args.participants} Teilnehmende\n"
        "Grün = Source · Blau gestrichelt = aktiv · Grau gepunktet = geparkt"
        + (" · Orange = lokale Chair-Vorschau" if args.show_chairs else "")
    )
    ax.set_xlim(roi.x_min - 20, roi.x_max + 20)
    ax.set_ylim(roi.y_max + 20, roi.y_min - 20)
    ax.set_aspect("equal", adjustable="box")
    ax.grid(alpha=0.15)
    destination.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(destination, dpi=180, bbox_inches="tight")
    plt.close(figure)
    print(destination)


if __name__ == "__main__":
    main()
