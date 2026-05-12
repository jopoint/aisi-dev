from __future__ import annotations

import argparse
import json
from pathlib import Path

from aisi.core.models import dataclass_to_dict
from aisi.generation.layout_synthesizer import synthesize_layout
from aisi.generation.proposal_evaluator import evaluate_layout_proposal
from aisi.generation.target_structure_generator import generate_target_structure
from aisi.input.scene_loader import build_scene_state_from_json
from aisi.interpretation.scene_interpreter import interpret_scene, summarize_scene_features
from aisi.projection.debug_plotter import plot_before_after
from aisi.projection.projection_composer import compose_projection_payload
from aisi.schemas.target_schema_engine import get_target_profile


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run minimal offline synthetic MVP pipeline.")
    parser.add_argument("--scene", required=True, help="Path to scene JSON input.")
    parser.add_argument(
        "--format",
        dest="learning_format",
        required=True,
        choices=["input", "groupwork", "discussion"],
        help="Target learning format.",
    )
    parser.add_argument("--outdir", required=True, help="Output directory for summary and plot.")
    return parser.parse_args()


def run(scene_path: str | Path, learning_format: str, outdir: str | Path) -> dict:
    outdir_path = Path(outdir)
    outdir_path.mkdir(parents=True, exist_ok=True)

    scene_state = build_scene_state_from_json(scene_path, learning_format=learning_format)
    scene_features = interpret_scene(scene_state)
    target_profile = get_target_profile(learning_format)
    target_structure = generate_target_structure(scene_state, scene_features, target_profile)
    layout_proposal = synthesize_layout(scene_state, scene_features, target_profile, target_structure)
    evaluation = evaluate_layout_proposal(scene_state, target_profile, layout_proposal)
    projection_payload = compose_projection_payload(scene_state, layout_proposal)
    features_summary = summarize_scene_features(scene_features)

    plot_before_after(
        scene_state,
        layout_proposal,
        save_path=outdir_path / "before_after.png",
        show=False,
        show_chairs=False,
    )

    rotation_summary = [
        {
            "table_id": target.table_id,
            "source_rot_deg": target.source_rot_deg,
            "target_rot_deg": target.target_rot_deg,
        }
        for target in layout_proposal.table_targets
    ]

    summary = {
        "learning_format": learning_format,
        "input_scene_name": Path(scene_path).name,
        "scene_features_summary": features_summary,
        "scene_features": dataclass_to_dict(scene_features),
        "evaluation": dataclass_to_dict(evaluation),
        "target_structure": dataclass_to_dict(target_structure),
        "layout_proposal": dataclass_to_dict(layout_proposal),
        "projection_payload": dataclass_to_dict(projection_payload),
        "rotation_summary": rotation_summary,
        "overlap_violations": evaluation.details.get("overlap_violations", 0.0),
        "clearance_violations": evaluation.details.get("clearance_violations", 0.0),
        "roi_violations": evaluation.details.get("roi_violations", 0.0),
        "artificial_shape_penalty": evaluation.details.get("artificial_shape_penalty", 0.0),
        "input_shape_penalty": evaluation.details.get("input_shape_penalty", 0.0),
        "combined_shape_penalty": evaluation.details.get("combined_shape_penalty", 0.0),
        "repair_applied": evaluation.details.get("repair_applied", False),
    }

    with (outdir_path / "summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)

    return summary


def main() -> None:
    args = parse_args()
    summary = run(args.scene, learning_format=args.learning_format, outdir=args.outdir)
    print("Synthetic MVP run completed.")
    print(f"Scene: {summary['input_scene_name']}")
    print(f"Format: {summary['learning_format']}")
    print(f"Output: {Path(args.outdir).resolve()}")
    print(f"Total score: {summary['evaluation']['total_score']:.3f}")
    print(f"Features: {summary['scene_features_summary']}")
    for item in summary["rotation_summary"]:
        print(
            f"{item['table_id']}: source_rot_deg={item['source_rot_deg']:.1f}, "
            f"target_rot_deg={item['target_rot_deg']:.1f}"
        )


if __name__ == "__main__":
    main()
