"""Prepare a Label Studio table-OBB export for Ultralytics OBB training.

Input export folder layout (expected):
- images/
- labels/
- classes.txt

This tool:
- pairs images and labels by stem
- performs deterministic train/val split
- writes images/train, images/val, labels/train, labels/val
- writes data.yaml with nc=1 and names=[table]

It does not modify source files and does not start training.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

DEFAULT_EXTENSIONS: Tuple[str, ...] = ("jpg", "jpeg", "png")


def _parse_extensions(raw: str | None) -> Tuple[str, ...]:
    if raw is None or raw.strip() == "":
        return DEFAULT_EXTENSIONS

    values = [x.strip().lower().lstrip(".") for x in raw.split(",")]
    values = [x for x in values if x]
    if not values:
        raise ValueError("--extensions produced an empty set")

    seen = set()
    out: List[str] = []
    for v in values:
        if v in seen:
            continue
        seen.add(v)
        out.append(v)
    return tuple(out)


def _collect_files_by_stem(folder: Path, extensions: Sequence[str]) -> Dict[str, Path]:
    allowed = {f".{ext.lower()}" for ext in extensions}
    out: Dict[str, Path] = {}
    for p in folder.glob("*"):
        if not p.is_file():
            continue
        if p.suffix.lower() not in allowed:
            continue
        # If duplicates with same stem exist, keep lexicographically first for determinism.
        prev = out.get(p.stem)
        if prev is None or str(p.name).lower() < str(prev.name).lower():
            out[p.stem] = p
    return out


def _collect_label_files_by_stem(folder: Path) -> Dict[str, Path]:
    out: Dict[str, Path] = {}
    for p in folder.glob("*.txt"):
        if not p.is_file():
            continue
        prev = out.get(p.stem)
        if prev is None or str(p.name).lower() < str(prev.name).lower():
            out[p.stem] = p
    return out


def _stable_key(stem: str) -> str:
    return hashlib.sha1(stem.encode("utf-8", errors="ignore")).hexdigest()


def _deterministic_split(stems: Sequence[str], val_frac: float) -> Tuple[List[str], List[str]]:
    if not (0.0 <= val_frac <= 0.9):
        raise ValueError("--val-frac must be in [0.0, 0.9]")

    ranked = sorted(stems, key=_stable_key)
    n = len(ranked)
    val_n = int(round(n * val_frac))
    val_n = max(0, min(n, val_n))

    val_set = set(ranked[:val_n])
    train = [s for s in sorted(stems) if s not in val_set]
    val = [s for s in sorted(stems) if s in val_set]
    return train, val


def _ensure_out_dirs(out_dir: Path) -> Dict[str, Path]:
    if out_dir.exists():
        raise FileExistsError(
            f"Output directory already exists: {out_dir}. "
            "Use a new --out-dir to avoid accidental overwrite."
        )

    paths = {
        "images_train": out_dir / "images" / "train",
        "images_val": out_dir / "images" / "val",
        "labels_train": out_dir / "labels" / "train",
        "labels_val": out_dir / "labels" / "val",
    }
    for p in paths.values():
        p.mkdir(parents=True, exist_ok=False)
    return paths


def _link_or_copy(src: Path, dst: Path, force_copy: bool) -> str:
    if force_copy:
        shutil.copy2(src, dst)
        return "copy"

    try:
        os.link(src, dst)
        return "hardlink"
    except OSError:
        shutil.copy2(src, dst)
        return "copy"


def _write_data_yaml(out_dir: Path) -> None:
    yaml_text = "\n".join(
        [
            "path: .",
            "train: images/train",
            "val: images/val",
            "nc: 1",
            "names: [table]",
            "",
        ]
    )
    (out_dir / "data.yaml").write_text(yaml_text, encoding="utf-8")


def _validate_classes(classes_file: Path) -> None:
    if not classes_file.exists():
        print(f"WARNING: classes.txt not found at {classes_file} (continuing)")
        return

    lines = [x.strip() for x in classes_file.read_text(encoding="utf-8", errors="ignore").splitlines() if x.strip()]
    if not lines:
        print(f"WARNING: classes.txt is empty: {classes_file}")
        return

    if lines[0].lower() != "table":
        print(f"WARNING: first class is '{lines[0]}', expected 'table'")

    if len(lines) > 1:
        print(f"WARNING: classes.txt has {len(lines)} classes; this prep targets table-only")


def _copy_split(
    split_name: str,
    stems: Sequence[str],
    images_by_stem: Dict[str, Path],
    labels_by_stem: Dict[str, Path],
    images_out: Path,
    labels_out: Path,
    force_copy: bool,
) -> Tuple[int, int]:
    hardlinks = 0
    copies = 0
    for stem in stems:
        img_src = images_by_stem[stem]
        lbl_src = labels_by_stem[stem]

        img_dst = images_out / img_src.name
        lbl_dst = labels_out / lbl_src.name

        mode_img = _link_or_copy(img_src, img_dst, force_copy=force_copy)
        mode_lbl = _link_or_copy(lbl_src, lbl_dst, force_copy=force_copy)

        hardlinks += int(mode_img == "hardlink") + int(mode_lbl == "hardlink")
        copies += int(mode_img == "copy") + int(mode_lbl == "copy")

    print(f"{split_name}: {len(stems)} paired samples")
    return hardlinks, copies


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Prepare Label Studio table-OBB export for Ultralytics OBB.")
    parser.add_argument("--export-dir", required=True, help="Path to Label Studio export folder.")
    parser.add_argument("--out-dir", required=True, help="Output folder for prepared Ultralytics OBB dataset.")
    parser.add_argument("--val-frac", type=float, default=0.2, help="Validation fraction in [0.0, 0.9] (default: 0.2).")
    parser.add_argument("--max-images", type=int, default=None, help="Optional limit on number of paired images.")
    parser.add_argument("--copy", action="store_true", help="Force copy mode (default: hardlink with copy fallback).")
    parser.add_argument(
        "--extensions",
        default=",".join(DEFAULT_EXTENSIONS),
        help="Comma-separated image extensions (default: jpg,jpeg,png).",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    export_dir = Path(args.export_dir)
    out_dir = Path(args.out_dir)

    images_dir = export_dir / "images"
    labels_dir = export_dir / "labels"
    classes_file = export_dir / "classes.txt"

    if not export_dir.exists() or not export_dir.is_dir():
        raise FileNotFoundError(f"--export-dir does not exist or is not a directory: {export_dir}")
    if not images_dir.exists() or not images_dir.is_dir():
        raise FileNotFoundError(f"Missing images folder: {images_dir}")
    if not labels_dir.exists() or not labels_dir.is_dir():
        raise FileNotFoundError(f"Missing labels folder: {labels_dir}")

    if args.max_images is not None and int(args.max_images) <= 0:
        raise ValueError("--max-images must be > 0 when provided")

    extensions = _parse_extensions(args.extensions)

    print("=== Prepare Label Studio Table OBB Export ===")
    print(f"export_dir: {export_dir}")
    print(f"out_dir: {out_dir}")
    print(f"val_frac: {args.val_frac}")
    print(f"extensions: {','.join(extensions)}")
    print(f"mode: {'copy' if args.copy else 'hardlink_or_copy_fallback'}")

    _validate_classes(classes_file)

    images_by_stem = _collect_files_by_stem(images_dir, extensions=extensions)
    labels_by_stem = _collect_label_files_by_stem(labels_dir)

    image_stems = set(images_by_stem.keys())
    label_stems = set(labels_by_stem.keys())

    paired_stems = sorted(image_stems & label_stems)
    image_only = sorted(image_stems - label_stems)
    label_only = sorted(label_stems - image_stems)

    if image_only:
        print(f"WARNING: images without labels: {len(image_only)}")
    if label_only:
        print(f"WARNING: labels without images: {len(label_only)}")

    if args.max_images is not None:
        paired_stems = paired_stems[: int(args.max_images)]

    if not paired_stems:
        raise RuntimeError("No paired image/label samples found")

    train_stems, val_stems = _deterministic_split(paired_stems, val_frac=float(args.val_frac))

    out_paths = _ensure_out_dirs(out_dir)

    train_hard, train_copy = _copy_split(
        split_name="train",
        stems=train_stems,
        images_by_stem=images_by_stem,
        labels_by_stem=labels_by_stem,
        images_out=out_paths["images_train"],
        labels_out=out_paths["labels_train"],
        force_copy=bool(args.copy),
    )
    val_hard, val_copy = _copy_split(
        split_name="val",
        stems=val_stems,
        images_by_stem=images_by_stem,
        labels_by_stem=labels_by_stem,
        images_out=out_paths["images_val"],
        labels_out=out_paths["labels_val"],
        force_copy=bool(args.copy),
    )

    _write_data_yaml(out_dir)

    print("--- Summary ---")
    print(f"images_found: {len(images_by_stem)}")
    print(f"labels_found: {len(labels_by_stem)}")
    print(f"paired_samples: {len(paired_stems)}")
    print(f"train_samples: {len(train_stems)}")
    print(f"val_samples: {len(val_stems)}")
    print(f"hardlinks_created: {train_hard + val_hard}")
    print(f"copies_created: {train_copy + val_copy}")
    print(f"prepared_dataset_dir: {out_dir}")


if __name__ == "__main__":
    main()
