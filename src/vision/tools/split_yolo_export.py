#!/usr/bin/env python3
r"""
YOLO export splitter: splits images/labels into train/val sets (90/10).
Creates data.yaml with absolute paths.

Usage:
  python .\src\vision\tools\split_yolo_export.py
"""
from pathlib import Path
import random
import shutil

def main():
    src_root = Path("data/vision/yolo_export_115")
    img_dir = src_root / "images"
    lab_dir = src_root / "labels"

    imgs = sorted(list(img_dir.glob("*.jpg")) + list(img_dir.glob("*.jpeg")) + list(img_dir.glob("*.png")))
    if not imgs:
        raise SystemExit(f"No images found in {img_dir}")

    random.seed(42)
    random.shuffle(imgs)

    val_n = max(1, int(0.1 * len(imgs)))
    val_set = set(imgs[:val_n])
    train_set = imgs[val_n:]

    dst_root = Path("data/vision/yolo_115")
    out_img_tr = dst_root / "images/train"
    out_img_va = dst_root / "images/val"
    out_lab_tr = dst_root / "labels/train"
    out_lab_va = dst_root / "labels/val"

    for d in [out_img_tr, out_img_va, out_lab_tr, out_lab_va]:
        d.mkdir(parents=True, exist_ok=True)

    def label_path_for(img_path: Path) -> Path:
        return lab_dir / (img_path.stem + ".txt")

    def copy_pair(img_path: Path, split: str):
        if split == "val":
            img_out = out_img_va / img_path.name
            lab_out = out_lab_va / (img_path.stem + ".txt")
        else:
            img_out = out_img_tr / img_path.name
            lab_out = out_lab_tr / (img_path.stem + ".txt")

        shutil.copy2(img_path, img_out)
        lp = label_path_for(img_path)
        if lp.exists():
            shutil.copy2(lp, lab_out)
        else:
            lab_out.write_text("", encoding="utf-8")

    for p in train_set:
        copy_pair(p, "train")
    for p in val_set:
        copy_pair(p, "val")

    # Generate data.yaml
    output_dir_abs = dst_root.resolve()
    data_yaml_path = dst_root / "data.yaml"
    yaml_content = f"""path: {output_dir_abs}
train: images/train
val: images/val
nc: 3
names: ['table', 'chair', 'person']
"""
    data_yaml_path.write_text(yaml_content)

    # Print summary
    print(f"✓ Split complete!")
    print(f"  Train: {len(train_set)} images")
    print(f"  Val:   {len(val_set)} images (90/10 split)")
    print(f"  Output: {output_dir_abs}")
    print(f"  Config: {data_yaml_path}")

if __name__ == "__main__":
    main()
