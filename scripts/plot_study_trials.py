"""Render the active T3A/T4A Study layouts for physical setup review."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle
from matplotlib.transforms import Affine2D


ROOM_CM = 500.0
TABLE_WIDTH_CM = 160.0
TABLE_DEPTH_CM = 80.0


def add_table(ax, pose: dict[str, float], *, edgecolor: str, label: str, linewidth: float = 2.0) -> None:
    """Draw one 160 x 80 cm Rect footprint at its authored world pose."""

    x_cm = pose["x_cm"]
    y_cm = pose["y_cm"]
    rotation_deg = pose["rotation_deg"]
    rectangle = Rectangle(
        (x_cm - TABLE_WIDTH_CM / 2.0, y_cm - TABLE_DEPTH_CM / 2.0),
        TABLE_WIDTH_CM,
        TABLE_DEPTH_CM,
        fill=False,
        edgecolor=edgecolor,
        linewidth=linewidth,
    )
    rectangle.set_transform(Affine2D().rotate_deg_around(x_cm, y_cm, rotation_deg) + ax.transData)
    ax.add_patch(rectangle)
    ax.text(x_cm, y_cm, label, ha="center", va="center", fontsize=9)


def render_trial(ax, trial: dict[str, object], title: str) -> None:
    """Render source, target, static tables, and participant start marker."""

    ax.set(xlim=(0.0, ROOM_CM), ylim=(0.0, ROOM_CM), aspect="equal", title=title)
    ax.set_xticks(range(0, int(ROOM_CM) + 1, 100))
    ax.set_yticks(range(0, int(ROOM_CM) + 1, 100))
    ax.grid(True, alpha=0.25)
    ax.set_xlabel("x [cm]")
    ax.set_ylabel("y [cm]")

    for index, static_pose in enumerate(trial.get("distractor_tables", ()), start=1):
        add_table(ax, static_pose, edgecolor="black", label=f"S{index}")

    source = trial["source_pose"]
    target = trial["target_pose"]
    add_table(ax, source, edgecolor="green", label="Source", linewidth=3.0)
    add_table(ax, target, edgecolor="blue", label="Target", linewidth=3.0)
    ax.annotate(
        "",
        xy=(target["x_cm"], target["y_cm"]),
        xytext=(source["x_cm"], source["y_cm"]),
        arrowprops={"arrowstyle": "->", "color": "tab:red", "linestyle": "--", "linewidth": 1.5},
    )

    for participant in trial.get("participant_start_positions", ()):
        x_cm = participant["x_cm"]
        y_cm = participant["y_cm"]
        ax.add_patch(
            Circle(
                (x_cm, y_cm),
                participant["radius_cm"],
                fill=False,
                edgecolor="tab:red",
                linewidth=2.0,
            )
        )
        ax.text(x_cm, y_cm, participant["id"], ha="center", va="center", color="tab:red", fontsize=9)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trials", type=Path, default=Path("data/aisi/study/trials.json"))
    parser.add_argument("--out-dir", type=Path, default=Path("data/aisi/study/debug_plots"))
    parser.add_argument("--show", action="store_true")
    args = parser.parse_args()

    payload = json.loads(args.trials.read_text(encoding="utf-8"))
    args.out_dir.mkdir(parents=True, exist_ok=True)
    for task_id in ("T3", "T4"):
        trial = next(
            trial
            for trial in payload["trials"]
            if trial["task_id"] == task_id and trial["variant"] == "A"
        )
        figure, axis = plt.subplots(figsize=(7, 7))
        render_trial(axis, trial, f"{task_id}A — active trial layout")
        output_path = args.out_dir / f"{task_id.lower()}a_layout.png"
        figure.savefig(output_path, dpi=160, bbox_inches="tight")
        print(output_path)
        if args.show:
            plt.show()
        plt.close(figure)


if __name__ == "__main__":
    main()
