"""Copy a diverse, deterministic subset of captured vision hard examples."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

# Permit ``python scripts\\select_hard_example_candidates.py`` from the repo
# root without requiring an external PYTHONPATH setting on Windows.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.vision.hard_example_candidates import write_candidate_subset


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-dir", type=Path, default=Path("data/vision/debug/hard_examples"),
        help="Directory containing hard_example_*.png captures.",
    )
    parser.add_argument(
        "--output-dir", type=Path,
        default=Path("data/vision/training/rect_obb_hard_v2/candidates"),
        help="Directory receiving copied representatives and manifest.csv.",
    )
    parser.add_argument(
        "--representatives-per-burst", type=int, default=3,
        help="Maximum visually diverse representatives selected from each burst (default: 3).",
    )
    args = parser.parse_args()
    decisions, manifest = write_candidate_subset(
        args.input_dir,
        args.output_dir,
        representatives=args.representatives_per_burst,
    )
    print(
        f"Hard examples: input={len(decisions)} selected={sum(item.selected for item in decisions)} "
        f"bursts={len({item.burst_id for item in decisions})} manifest={manifest}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
