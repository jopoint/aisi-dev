"""Build a table-only OBB dataset skeleton from an existing image directory.

This tool intentionally does NOT generate OBB labels.
It only creates the folder structure, copies/links images, and creates empty label files.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple


DEFAULT_EXTENSIONS: Tuple[str, ...] = ("jpg", "jpeg", "png")


def _parse_extensions(raw: str | None) -> Tuple[str, ...]:
    if raw is None or raw.strip() == "":
        return DEFAULT_EXTENSIONS

    exts: List[str] = []
    for item in raw.split(","):
        value = item.strip().lower().lstrip(".")
        if value:
            exts.append(value)

    if not exts:
        raise ValueError("--extensions produced an empty set")

    # Keep order stable while removing duplicates.
    seen = set()
    deduped: List[str] = []
    for ext in exts:
        if ext in seen:
            continue
        seen.add(ext)
        deduped.append(ext)
    return tuple(deduped)


def _collect_images(image_dir: Path, extensions: Sequence[str]) -> List[Path]:
    allowed = {f".{ext.lower()}" for ext in extensions}
    images = [
        p
        for p in image_dir.rglob("*")
        if p.is_file() and p.suffix.lower() in allowed
    ]
    # Deterministic base ordering.
    images.sort(key=lambda p: str(p.as_posix()).lower())
    return images


def _stable_key(path: Path) -> str:
    # Deterministic pseudo-random key for robust train/val split.
    data = str(path.as_posix()).encode("utf-8", errors="ignore")
    return hashlib.sha1(data).hexdigest()


def _split_train_val(images: Sequence[Path], val_frac: float) -> Tuple[List[Path], List[Path]]:
    if not (0.0 <= val_frac <= 0.9):
        raise ValueError("--val-frac must be in range [0.0, 0.9]")

    n = len(images)
    if n == 0:
        return [], []

    ranked = sorted(images, key=_stable_key)
    val_count = int(round(n * val_frac))
    val_count = max(0, min(n, val_count))

    val_set = set(ranked[:val_count])
    val = [p for p in images if p in val_set]
    train = [p for p in images if p not in val_set]
    return train, val


def _safe_filename(index: int, src: Path) -> str:
    # Keep extension, avoid collisions with deterministic index prefix.
    return f"img_{index:06d}{src.suffix.lower()}"


def _link_or_copy(src: Path, dst: Path, force_copy: bool) -> str:
    if force_copy:
        shutil.copy2(src, dst)
        return "copy"

    # os.link is fast and space-efficient; fallback to copy when unsupported.
    try:
        os.link(src, dst)
        return "hardlink"
    except OSError:
        shutil.copy2(src, dst)
        return "copy"


def _prepare_dirs(out_dir: Path) -> dict[str, Path]:
    if out_dir.exists():
        raise FileExistsError(
            f"Output directory already exists: {out_dir}. "
            "Use a new --out-dir to avoid overwriting existing datasets."
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


def _emit_split(
    split_name: str,
    images: Sequence[Path],
    image_out_dir: Path,
    label_out_dir: Path,
    force_copy: bool,
) -> Tuple[int, int, int]:
    link_count = 0
    copy_count = 0

    for idx, src in enumerate(images):
        out_name = _safe_filename(idx, src)
        dst_img = image_out_dir / out_name
        mode = _link_or_copy(src, dst_img, force_copy=force_copy)
        if mode == "hardlink":
            link_count += 1
        else:
            copy_count += 1

        dst_lbl = label_out_dir / f"{Path(out_name).stem}.txt"
        # Empty label file by design: manual OBB annotation happens later.
        dst_lbl.write_text("", encoding="utf-8")

    print(f"{split_name}: wrote {len(images)} images, {len(images)} empty label files")
    return len(images), link_count, copy_count


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build table-only OBB dataset skeleton (no label conversion).")
    parser.add_argument("--image-dir", required=True, help="Input image directory (recursive scan).")
    parser.add_argument("--out-dir", required=True, help="Output dataset directory (must not already exist).")
    parser.add_argument("--val-frac", type=float, default=0.2, help="Validation fraction in [0.0, 0.9] (default: 0.2).")
    parser.add_argument("--max-images", type=int, default=None, help="Optional limit of images after deterministic ordering.")
    parser.add_argument("--copy", action="store_true", help="Force copy mode (default: hardlink with copy fallback).")
    parser.add_argument(
        "--extensions",
        default=",".join(DEFAULT_EXTENSIONS),
        help="Comma-separated image extensions, e.g. jpg,jpeg,png (default: jpg,jpeg,png).",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    image_dir = Path(args.image_dir)
    out_dir = Path(args.out_dir)
    extensions = _parse_extensions(args.extensions)

    if not image_dir.exists() or not image_dir.is_dir():
        raise FileNotFoundError(f"--image-dir does not exist or is not a directory: {image_dir}")

    if args.max_images is not None and int(args.max_images) <= 0:
        raise ValueError("--max-images must be > 0 when provided")

    print("=== Build Table OBB Dataset Skeleton ===")
    print(f"image_dir: {image_dir}")
    print(f"out_dir: {out_dir}")
    print(f"val_frac: {args.val_frac}")
    print(f"extensions: {','.join(extensions)}")
    print(f"mode: {'copy' if args.copy else 'hardlink_or_copy_fallback'}")

    images = _collect_images(image_dir=image_dir, extensions=extensions)
    if args.max_images is not None:
        images = images[: int(args.max_images)]

    if not images:
        raise RuntimeError("No images found with the selected extensions")

    train_images, val_images = _split_train_val(images=images, val_frac=float(args.val_frac))

    paths = _prepare_dirs(out_dir)

    train_n, train_links, train_copies = _emit_split(
        split_name="train",
        images=train_images,
        image_out_dir=paths["images_train"],
        label_out_dir=paths["labels_train"],
        force_copy=bool(args.copy),
    )
    val_n, val_links, val_copies = _emit_split(
        split_name="val",
        images=val_images,
        image_out_dir=paths["images_val"],
        label_out_dir=paths["labels_val"],
        force_copy=bool(args.copy),
    )

    _write_data_yaml(out_dir)

    print("--- Summary ---")
    print(f"found_images: {len(images)}")
    print(f"train_images: {train_n}")
    print(f"val_images: {val_n}")
    print(f"hardlinks_created: {train_links + val_links}")
    print(f"copies_created: {train_copies + val_copies}")
    print(f"written_to: {out_dir}")


if __name__ == "__main__":
    main()
