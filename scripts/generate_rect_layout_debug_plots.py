"""Render representative rect-template layouts for visual review."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

# This script renders PNG artifacts only. Select a headless backend before the
# shared debug_plotter module imports matplotlib.pyplot.
matplotlib.use("Agg")

from aisi.core.models import ROI, SceneState, TableState, TargetStructure
from aisi.generation.layout_synthesizer import synthesize_layout
from aisi.projection.debug_plotter import plot_layout_proposal


SOURCE_POSITIONS = ((90.0, 140.0), (250.0, 140.0), (410.0, 140.0), (90.0, 360.0), (250.0, 360.0), (410.0, 360.0))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/aisi/debug/rect_layout_templates"),
        help="Directory for generated PNGs.",
    )
    return parser.parse_args()


def make_scene(table_count: int, learning_format: str) -> SceneState:
    tables = [
        TableState(f"table_{index}", x, y, 0.0, 160.0, 80.0, table_type="rect")
        for index, (x, y) in enumerate(SOURCE_POSITIONS[:table_count])
    ]
    return SceneState(ROI(0.0, 0.0, 500.0, 500.0), tables, learning_format)


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for learning_format in ("input", "groupwork", "discussion"):
        for table_count in (1, 3, 4, 5, 6):
            scene = make_scene(table_count, learning_format)
            proposal = synthesize_layout(
                scene,
                scene_features=None,
                target_profile=None,
                target_structure=TargetStructure(structure_type="rect_template_debug"),
                transformation_strength=1.0,
            )
            destination = args.output_dir / f"rect_{learning_format}_{table_count}.png"
            plot_layout_proposal(scene, proposal, save_path=destination)
            print(destination)


if __name__ == "__main__":
    main()
