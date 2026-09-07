from pathlib import Path
import random
import re
import shutil


ROOT = Path(
    r"C:\dev\Promotion_Prototypen\AISI\data\vision\training\rect_v1"
)

IMAGES_SRC = ROOT / "dataset_obb" / "images" / "train"
LABELS_SRC = ROOT / "dataset_obb" / "labels" / "train"

OUT = ROOT / "bootstrap_obb"

SEED = 42
VAL_FRACTION = 0.20


def clip_name(stem: str) -> str:
    # rect_01_center_0042 -> rect_01_center
    return re.sub(r"_\d+$", "", stem)


def main():
    labels = sorted(LABELS_SRC.glob("*.txt"))

    if not labels:
        raise RuntimeError("No OBB labels found")

    pairs = []

    for label in labels:
        image = IMAGES_SRC / f"{label.stem}.jpg"

        if not image.exists():
            print(f"WARNING: image missing for {label.name}")
            continue

        pairs.append((image, label))

    # Group by source clip to avoid near-identical frames
    # leaking between train and validation.
    groups = {}

    for image, label in pairs:
        groups.setdefault(
            clip_name(image.stem),
            []
        ).append((image, label))

    clip_names = sorted(groups)

    rng = random.Random(SEED)
    rng.shuffle(clip_names)

    n_val = max(
        1,
        round(len(clip_names) * VAL_FRACTION),
    )

    val_clips = set(clip_names[:n_val])
    train_clips = set(clip_names[n_val:])

    if OUT.exists():
        shutil.rmtree(OUT)

    for split in ("train", "val"):
        (OUT / "images" / split).mkdir(
            parents=True,
            exist_ok=True,
        )
        (OUT / "labels" / split).mkdir(
            parents=True,
            exist_ok=True,
        )

    counts = {"train": 0, "val": 0}

    for clip, items in groups.items():
        split = "val" if clip in val_clips else "train"

        for image, label in items:
            shutil.copy2(
                image,
                OUT / "images" / split / image.name,
            )

            shutil.copy2(
                label,
                OUT / "labels" / split / label.name,
            )

            counts[split] += 1

    yaml_text = """path: .
train: images/train
val: images/val

names:
  0: table
"""

    (OUT / "data.yaml").write_text(
        yaml_text,
        encoding="utf-8",
    )

    print("")
    print("==============================")
    print(f"Total labeled images: {len(pairs)}")
    print(f"Train images:         {counts['train']}")
    print(f"Val images:           {counts['val']}")
    print(f"Train clips:          {sorted(train_clips)}")
    print(f"Val clips:            {sorted(val_clips)}")
    print(f"Dataset:              {OUT}")
    print("==============================")


if __name__ == "__main__":
    main()