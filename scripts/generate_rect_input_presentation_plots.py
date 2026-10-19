"""Render the source-adaptive Rect Input presentation formation for review."""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Polygon, Rectangle

from aisi.core.models import ROI, SceneState, TableState, TargetStructure
from aisi.core.table_geometry import table_world_footprint
from aisi.generation.layout_synthesizer import (
    INPUT_SEAT_CLEARANCE_DEPTH_CM,
    _rect_input_clearance_regions,
    synthesize_layout,
)


CASES = {
    3: (
        ("table_0", 105.0, 140.0, -20.0),
        ("table_1", 260.0, 250.0, 30.0),
        ("table_2", 405.0, 360.0, 10.0),
    ),
    5: (
        ("table_0", 80.0, 150.0, 0.0),
        ("table_1", 145.0, 340.0, -35.0),
        ("table_2", 255.0, 225.0, 15.0),
        ("table_3", 365.0, 105.0, 50.0),
        ("table_4", 420.0, 360.0, -10.0),
    ),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/aisi/debug/rect_input_presentation"),
        help="Directory for generated PNGs.",
    )
    return parser.parse_args()


def _scene(rows: tuple[tuple[str, float, float, float], ...]) -> SceneState:
    return SceneState(
        ROI(0.0, 0.0, 500.0, 500.0),
        [TableState(table_id, x, y, rotation, 160.0, 80.0, table_type="rect") for table_id, x, y, rotation in rows],
        "input",
    )


def _plot(scene: SceneState, output_path: Path) -> None:
    proposal = synthesize_layout(
        scene,
        scene_features=None,
        target_profile=None,
        target_structure=TargetStructure(structure_type="rect_input_presentation_plot"),
        transformation_strength=1.0,
    )
    notes = dict(note.split("=", 1) for note in proposal.generation_notes if "=" in note)
    presenter_id = notes["rect_input_presenter_id"]
    axis_values = notes["rect_input_presentation_axis"].strip("()").split(",")
    axis = (float(axis_values[0]), float(axis_values[1]))
    figure, plot = plt.subplots(figsize=(9, 9))
    roi = scene.roi
    plot.add_patch(Rectangle((roi.x_min, roi.y_min), roi.width, roi.height, fill=False, edgecolor="#202020", linewidth=1.5))
    for region in _rect_input_clearance_regions(proposal.table_targets, scene.tables, presenter_id, axis):
        plot.add_patch(Polygon(region, closed=True, facecolor="#43a047", edgecolor="#2e7d32", alpha=0.16, linestyle=":", linewidth=0.8))
    source_by_id = {table.table_id: table for table in scene.tables}
    displacements = []
    for target in proposal.table_targets:
        source = source_by_id[target.table_id]
        distance = math.dist((source.x, source.y), (target.target_x, target.target_y))
        displacements.append(distance)
        plot.add_patch(Polygon(table_world_footprint(source, (source.x, source.y), source.rot_deg), closed=True, facecolor="#1e88e5", edgecolor="#1e88e5", alpha=0.16))
        plot.add_patch(Polygon(table_world_footprint(source, (target.target_x, target.target_y), target.target_rot_deg), closed=True, fill=False, edgecolor="#d32f2f", linewidth=2.0, linestyle="--"))
        plot.add_patch(FancyArrowPatch((source.x, source.y), (target.target_x, target.target_y), arrowstyle="->", mutation_scale=10, color="#555555", linewidth=1.0, linestyle=":"))
        role = "Präsentation" if target.table_id == presenter_id else "Zuhören"
        plot.text(target.target_x, target.target_y, f"{role}\n{target.table_id}\n{distance:.0f} cm", color="#c62828", ha="center", va="center", fontsize=8)
    plot.set_title(
        "Rect Input – quelladaptive Präsentationsformation\n"
        f"Präsentation: {presenter_id} · max. Weg: {max(displacements):.1f} cm · Summe: {sum(displacements):.1f} cm\n"
        f"Grün: eine abgerundete {INPUT_SEAT_CLEARANCE_DEPTH_CM:.0f}-cm-Sitz-/Bewegungsseite"
    )
    plot.set_xlim(-20.0, 520.0)
    plot.set_ylim(520.0, -20.0)
    plot.set_aspect("equal", adjustable="box")
    plot.grid(alpha=0.15)
    figure.tight_layout()
    figure.savefig(output_path, dpi=160)
    plt.close(figure)


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for count, rows in CASES.items():
        destination = args.output_dir / f"rect_input_presentation_count{count}.png"
        _plot(_scene(rows), destination)
        print(destination)


if __name__ == "__main__":
    main()
