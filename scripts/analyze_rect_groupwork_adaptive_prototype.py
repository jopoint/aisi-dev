"""Erzeuge die Entscheidungsplots des quelladaptiven Rect-Groupwork-Prototyps."""

from __future__ import annotations

import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Polygon, Rectangle

from aisi.analysis.rect_groupwork_adaptive_prototype import (
    SEAT_CLEARANCE_DEPTH_CM,
    _group_clearance_regions,
    solve_rect_groupwork_prototype,
)
from aisi.core.models import SceneState, TableTarget
from aisi.core.table_geometry import table_world_footprint
from aisi.generation.layout_synthesizer import _layout_rect_groupwork_templates
from aisi.input.scene_loader import build_scene_state_from_json


ROOT = Path(__file__).resolve().parents[1]
SCENE_DIRECTORY = ROOT / "data" / "aisi" / "scenes" / "rect_groupwork_validation"
OUTPUT_DIRECTORY = ROOT / "data" / "aisi" / "debug" / "rect_groupwork_adaptive_prototype"


def _distances(scene: SceneState, targets: list[TableTarget] | tuple[TableTarget, ...]) -> list[float]:
    target_by_id = {target.table_id: target for target in targets}
    return [
        math.dist((table.x, table.y), (target_by_id[table.table_id].target_x, target_by_id[table.table_id].target_y))
        for table in scene.tables
    ]


def _json_number(value: float) -> float | None:
    return value if math.isfinite(value) else None


def _plot_case(scene: SceneState, result, output_path: Path, profile: str) -> None:
    figure, axis = plt.subplots(figsize=(11, 9))
    roi = scene.roi
    axis.add_patch(Rectangle((roi.x_min, roi.y_min), roi.width, roi.height, fill=False, linewidth=1.5, edgecolor="#202020"))
    source_by_id = {table.table_id: table for table in scene.tables}
    for _, regions in _group_clearance_regions(scene, result.table_targets, result.groups):
        for region in regions:
            axis.add_patch(
                Polygon(
                    region,
                    closed=True,
                    facecolor="#43a047",
                    edgecolor="#2e7d32",
                    linewidth=0.8,
                    alpha=0.12,
                    linestyle=":",
                )
            )

    for table in scene.tables:
        axis.add_patch(Polygon(table_world_footprint(table, (table.x, table.y), table.rot_deg), closed=True, facecolor="#1e88e5", edgecolor="#1e88e5", alpha=0.16))

    for target in result.table_targets:
        source = source_by_id[target.table_id]
        displacement = math.dist((source.x, source.y), (target.target_x, target.target_y))
        source_label_y = source.y + 22.0 if displacement < 12.0 else source.y
        target_label_y = target.target_y - 22.0 if displacement < 12.0 else target.target_y
        axis.text(source.x, source_label_y, f"Quelle\n{source.table_id}\n{source.rot_deg:.1f}°", color="#1565c0", ha="center", va="center", fontsize=8)
        axis.add_patch(Polygon(table_world_footprint(source, (target.target_x, target.target_y), target.target_rot_deg), closed=True, fill=False, edgecolor="#d32f2f", linewidth=2.0, linestyle="--"))
        axis.add_patch(FancyArrowPatch((source.x, source.y), (target.target_x, target.target_y), arrowstyle="->", mutation_scale=10, color="#555555", linewidth=1.0, linestyle=":"))
        axis.text(target.target_x, target_label_y, f"Ziel\n{target.target_rot_deg:.1f}°\n{displacement:.1f} cm", color="#c62828", ha="center", va="center", fontsize=8)

    groups = " | ".join(" + ".join(group) for group in result.groups)
    objective = result.objective
    profile = profile.replace(", dann ", ",\ndann ").replace(" bei +50 cm Bewegungsbudget", "\nbei +50 cm Bewegungsbudget")
    axis.set_title(
        "Rect Groupwork – quelladaptiver Prototyp\n"
        f"Profil: {profile}\n"
        f"Paare/Singleton: {groups}\n"
        f"max. Verschiebung {objective.max_displacement_cm:.1f} cm · "
        f"Summe {objective.total_displacement_cm:.1f} cm\n"
        f"Rotation {objective.total_rotation_change_deg:.1f}° · Kreuzungen {objective.crossing_count}\n"
        f"min. Inselabstand {objective.min_intergroup_gap_cm:.1f} cm · "
        f"Zonenüberlappung {objective.clearance_overlap_area_cm2:.0f} cm²\n"
        f"Grün: {SEAT_CLEARANCE_DEPTH_CM:.0f}-cm Sitz-/Bewegungsflächen"
    )
    axis.set_xlim(roi.x_min - 20.0, roi.x_max + 20.0)
    axis.set_ylim(roi.y_max + 20.0, roi.y_min - 20.0)
    axis.set_aspect("equal", adjustable="box")
    axis.grid(alpha=0.15)
    figure.tight_layout()
    figure.savefig(output_path, dpi=160)
    plt.close(figure)


def main() -> None:
    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    summary: list[dict] = []
    for count in range(2, 6):
        scene = build_scene_state_from_json(SCENE_DIRECTORY / f"rect_groupwork_{count}.json", learning_format="groupwork")
        movement = solve_rect_groupwork_prototype(scene)
        balanced = solve_rect_groupwork_prototype(scene, selection="clearance")
        reference_targets, _ = _layout_rect_groupwork_templates(scene, sorted(scene.tables, key=lambda table: table.table_id))
        reference_distances = _distances(scene, reference_targets)
        summary.append(
            {
                "count": count,
                "movement_minimal": {
                    "groups": [list(group) for group in movement.groups],
                    "max_displacement_cm": movement.objective.max_displacement_cm,
                    "total_displacement_cm": movement.objective.total_displacement_cm,
                    "min_intergroup_gap_cm": _json_number(movement.objective.min_intergroup_gap_cm),
                    "clearance_overlap_area_cm2": movement.objective.clearance_overlap_area_cm2,
                },
                "aggressive_clearance_profile": {
                    "groups": [list(group) for group in balanced.groups],
                    "max_displacement_cm": balanced.objective.max_displacement_cm,
                    "total_displacement_cm": balanced.objective.total_displacement_cm,
                    "total_rotation_change_deg": balanced.objective.total_rotation_change_deg,
                    "crossing_count": balanced.objective.crossing_count,
                    "min_intergroup_gap_cm": _json_number(balanced.objective.min_intergroup_gap_cm),
                    "clearance_overlap_area_cm2": balanced.objective.clearance_overlap_area_cm2,
                },
                "obsolete_id_template_reference": {
                    "max_displacement_cm": max(reference_distances),
                    "total_displacement_cm": sum(reference_distances),
                },
            }
        )
        if count in (3, 5):
            _plot_case(
                scene,
                balanced,
                OUTPUT_DIRECTORY / f"rect_groupwork_adaptive_count{count}.png",
                "Zonenüberlappung minimieren ohne Bewegungsbudget",
            )

    with (OUTPUT_DIRECTORY / "decision_summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)
    print(f"Quelladaptive Auswertung geschrieben nach: {OUTPUT_DIRECTORY}")


if __name__ == "__main__":
    main()
